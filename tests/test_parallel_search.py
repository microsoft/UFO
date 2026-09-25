# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from langchain.docstore.document import Document
from mcp.shared.exceptions import McpError
from mcp.types import CallToolRequest, ErrorData

from config.config_loader import ConfigLoader
from ufo.module.context import Context, ContextNames
from ufo.prompter.basic import BasicPrompter
from ufo.rag import retriever, web_search
from ufo.rag.web_search import ParallelSearchWeb


def test_parallel_provider_loads_from_rag_yaml(tmp_path):
    config_dir = tmp_path / "config" / "ufo"
    config_dir.mkdir(parents=True)
    (config_dir / "rag.yaml").write_text(
        'RAG_ONLINE_SEARCH: true\nRAG_ONLINE_SEARCH_PROVIDER: "parallel"\n'
    )

    config = ConfigLoader(base_path=str(tmp_path / "config")).load_ufo_config()

    assert config.rag.online_search is True
    assert config.rag.online_search_provider == "parallel"


def test_parallel_search_invokes_web_search_and_surfaces_evidence():
    server = FastMCP("parallel-search-test")
    calls = []

    @server.tool()
    def web_search(objective: str, search_queries: list[str]):
        calls.append((objective, search_queries))
        return {
            "search_id": "test-search",
            "results": [
                {
                    "title": "UFO documentation",
                    "url": "https://example.com/ufo",
                    "excerpts": ["Useful attributed evidence."],
                }
            ],
            "session_id": "test-session",
        }

    search = ParallelSearchWeb()
    search.transport = server

    results = search.search("UFO agent framework", top_k=1)

    assert calls == [
        (
            "Find current, reliable information about: UFO agent framework",
            ["UFO agent framework"],
        )
    ]
    assert results == [
        {
            "name": "UFO documentation",
            "url": "https://example.com/ufo",
            "snippet": "Useful attributed evidence.",
        }
    ]
    assert search.create_documents(results) == [
        Document(
            page_content=(
                "UFO documentation\nSource: https://example.com/ufo\n\n"
                "Useful attributed evidence."
            ),
            metadata={
                "name": "UFO documentation",
                "url": "https://example.com/ufo",
                "snippet": "Useful attributed evidence.",
            },
        )
    ]


def test_parallel_transport_sends_ufo_user_agent():
    server = FastMCP("parallel-search-user-agent-test")
    observed_user_agents = []

    @server.tool()
    def web_search(objective: str, search_queries: list[str]):
        return {"results": []}

    app = server.http_app(path="/mcp", stateless_http=True)

    async def capture_headers(scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            observed_user_agents.append(headers.get(b"user-agent", b"").decode())
        await app(scope, receive, send)

    def client_factory(headers=None, timeout=None, auth=None):
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=capture_headers),
            base_url="http://parallel.test",
            headers=headers,
            timeout=timeout,
            auth=auth,
        )

    search = ParallelSearchWeb("http://parallel.test/mcp")
    search.transport.httpx_client_factory = client_factory

    async def run_search():
        async with app.lifespan(app):
            return await search._search("UFO")

    assert asyncio.run(run_search()) == []
    assert isinstance(search.transport, StreamableHttpTransport)
    assert observed_user_agents
    assert set(observed_user_agents) == {"UFO"}


def test_online_retriever_keeps_bing_as_default(monkeypatch):
    calls = []

    class FakeBing:
        def search(self, query, top_k):
            calls.append(("bing", query, top_k))
            return [{"name": "Bing", "url": "https://bing.test", "snippet": "Bing"}]

        def create_documents(self, results):
            return [Document(page_content="Bing")]

        def create_indexer(self, documents):
            return "bing-index"

    class UnexpectedParallel:
        def __init__(self):
            raise AssertionError("the default route must not contact Parallel")

    monkeypatch.setattr(web_search, "BingSearchWeb", FakeBing)
    monkeypatch.setattr(web_search, "ParallelSearchWeb", UnexpectedParallel)
    monkeypatch.setattr(
        web_search.ufo_config.rag, "online_search_provider", "bing"
    )

    online = retriever.OnlineDocRetriever("current UFO docs", top_k=2)

    assert online.indexer == "bing-index"
    assert calls == [("bing", "current UFO docs", 2)]


@pytest.mark.parametrize("status_code", [429, 503])
def test_parallel_http_failure_leaves_online_retriever_empty(monkeypatch, status_code):
    async def reject_request(scope, receive, send):
        await send({"type": "http.response.start", "status": status_code, "headers": []})
        await send({"type": "http.response.body", "body": b"Search unavailable"})

    def client_factory(headers=None, timeout=None, auth=None):
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=reject_request),
            headers=headers,
            timeout=timeout,
            auth=auth,
        )

    search = ParallelSearchWeb("http://parallel.test/mcp")
    search.transport.httpx_client_factory = client_factory
    monkeypatch.setattr(web_search, "ParallelSearchWeb", lambda: search)
    monkeypatch.setattr(web_search.ufo_config.rag, "online_search_provider", "parallel")

    online = retriever.OnlineDocRetriever("current UFO docs", top_k=1)

    assert online.indexer is None
    assert online.retrieve("current UFO docs", top_k=1) == []


def test_online_retriever_routes_explicit_parallel_selection(monkeypatch):
    calls = []

    class FakeParallel:
        def search(self, query, top_k):
            calls.append(("parallel", query, top_k))
            return [
                {
                    "name": "Parallel",
                    "url": "https://parallel.test",
                    "snippet": "Parallel",
                }
            ]

        def create_documents(self, results):
            return [Document(page_content="Parallel")]

        def create_indexer(self, documents):
            return "parallel-index"

    monkeypatch.setattr(web_search, "ParallelSearchWeb", FakeParallel)
    monkeypatch.setattr(
        web_search.ufo_config.rag, "online_search_provider", "parallel"
    )

    online = retriever.OnlineDocRetriever("current UFO docs", top_k=2)

    assert online.indexer == "parallel-index"
    assert calls == [("parallel", "current UFO docs", 2)]


def test_parallel_protocol_failure_leaves_online_retriever_empty(monkeypatch):
    server = FastMCP("parallel-search-protocol-error-test")

    async def reject_tool_call(request):
        raise McpError(ErrorData(code=-32603, message="Temporary server error"))

    server._mcp_server.request_handlers[CallToolRequest] = reject_tool_call
    search = ParallelSearchWeb()
    search.transport = server
    monkeypatch.setattr(web_search, "ParallelSearchWeb", lambda: search)
    monkeypatch.setattr(web_search.ufo_config.rag, "online_search_provider", "parallel")

    online = retriever.OnlineDocRetriever("current UFO docs", top_k=1)

    assert online.indexer is None
    assert online.retrieve("current UFO docs", top_k=1) == []


@pytest.mark.parametrize("failure", ["tool_error", "invalid_payload", "timeout"])
def test_parallel_native_failures_return_no_evidence(monkeypatch, failure):
    server = FastMCP("parallel-search-failure-test")

    @server.tool(name="web_search")
    async def handle_search(objective: str, search_queries: list[str]):
        if failure == "tool_error":
            raise ValueError("Search temporarily unavailable")
        if failure == "timeout":
            await asyncio.sleep(1)
        return "invalid JSON"

    if failure == "timeout":
        monkeypatch.setattr(
            web_search, "Client", lambda transport: Client(transport, timeout=0.01)
        )
    search = ParallelSearchWeb()
    search.transport = server

    assert search.search("current UFO docs") is None


def test_parallel_search_preserves_cancellation(monkeypatch):
    search = ParallelSearchWeb()
    monkeypatch.setattr(search, "_search", AsyncMock(side_effect=asyncio.CancelledError))

    with pytest.raises(asyncio.CancelledError):
        search.search("current UFO docs")


def test_app_agent_process_uses_parallel_from_session_request(monkeypatch):
    from ufo.agents.agent.app_agent import AppAgent

    server = FastMCP("parallel-search-app-agent-test")
    calls = []

    @server.tool(name="web_search")
    def handle_search(objective: str, search_queries: list[str]):
        calls.append(search_queries)
        return {
            "results": [
                {
                    "title": "Current UFO guide",
                    "url": "https://example.com/guide",
                    "excerpts": ["Instructions for the requested task."],
                }
            ]
        }

    class LocalParallelSearchWeb(ParallelSearchWeb):
        def __init__(self):
            self.transport = server

    class NoopProcessor:
        def __init__(self, agent, global_context):
            self.processing_context = self

        async def process(self):
            pass

        def get_local(self, key):
            return None

    monkeypatch.setattr(web_search, "ParallelSearchWeb", LocalParallelSearchWeb)
    monkeypatch.setattr(web_search.ufo_config.rag, "online_search", True)
    monkeypatch.setattr(web_search.ufo_config.rag, "online_search_provider", "parallel")
    monkeypatch.setattr(web_search.ufo_config.rag, "online_search_topk", 1)
    monkeypatch.setattr(web_search, "get_hugginface_embedding", lambda: object())
    monkeypatch.setattr(
        web_search.FAISS, "from_documents", lambda documents, embeddings: documents
    )

    agent = AppAgent.__new__(AppAgent)
    agent.retriever_factory = retriever.RetrieverFactory()
    agent._load_mcp_context = AsyncMock()
    agent._context_provision_executed = False
    agent._processor_cls = NoopProcessor

    context = Context()
    context.set(ContextNames.REQUEST, "UFO docs")

    asyncio.run(agent.process(context))

    assert calls == [["UFO docs"]]
    assert agent.online_doc_retriever.indexer == [
        Document(
            page_content=(
                "Current UFO guide\nSource: https://example.com/guide\n\n"
                "Instructions for the requested task."
            ),
            metadata={
                "url": "https://example.com/guide",
                "name": "Current UFO guide",
                "snippet": "Instructions for the requested task.",
            },
        )
    ]

    stored_documents = agent.online_doc_retriever.indexer
    agent.online_doc_retriever.indexer = SimpleNamespace(
        similarity_search=lambda query, top_k, filter=None: stored_documents
    )
    agent.offline_doc_retriever = None
    agent.prompter = BasicPrompter
    _, online_prompt = agent.external_knowledge_prompt_helper("UFO docs", 1, 1)

    assert "Instructions for the requested task." in online_prompt
    assert "Current UFO guide" in online_prompt
    assert "https://example.com/guide" in online_prompt
