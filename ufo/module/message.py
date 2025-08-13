import asyncio
import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import WebSocket


from ufo.contracts.contracts import ClientRequest, ServerResponse


class MessageBus:
    def __init__(self, ws: Optional[WebSocket] = None):
        self.ws = ws
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    async def send_commands(
        self, server_response: ServerResponse, timeout: float = 10.0
    ):
        fut = asyncio.get_event_loop().create_future()

        request_id = str(uuid.uuid4())
        server_response.response_id = request_id

        self.pending_requests[server_response.response_id] = fut

        await self.ws.send(server_response.model_dump_json())

        try:
            return await asyncio.wait_for(fut, timeout)
        except asyncio.TimeoutError:
            self.pending_requests.pop(server_response.response_id, None)
            self.logger.warning(f"Waiting for {server_response} timed out")
            raise TimeoutError(f"Waiting for {server_response} timed out")

    async def handle_client_message(self, msg: Dict[str, Any]):
        """
        Handle a message from the client.
        :param msg: The message from the client.
        """
        client_req = ClientRequest(**msg)
        req_id = client_req.request_id

        if req_id in self.pending_requests:
            fut = self.pending_requests.pop(req_id)
            fut.set_result(client_req.action_results)
