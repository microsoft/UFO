from uuid import uuid4

from flask import Blueprint, jsonify, request
from ufo.cs.contracts import UFORequest, UFOResponse

from .session_manager import SessionManager
from .task_manager import TaskManager
from .ws_manager import WSManager


def create_api_blueprint(
    session_manager: SessionManager,
    task_manager: TaskManager,
    ws_manager: WSManager,
    ws_event_loop,
):
    api = Blueprint("api", __name__)

    @api.route("/api/ufo/task", methods=["POST"])
    def run_task():
        try:
            data = request.json
            ufo_request = UFORequest(**data)
            session_id = ufo_request.session_id
            if not session_id or session_id not in session_manager.sessions:
                session_id = ufo_request.session_id or str(uuid4())
                session = session_manager.get_or_create_session(
                    session_id, ufo_request.request
                )
            else:
                session = session_manager.sessions[session_id]
                if ufo_request.action_results:
                    session_manager.process_action_results(
                        session_id, ufo_request.action_results
                    )

            status = "continue"
            try:
                session.run_coro.send(None)
            except StopIteration:
                status = "completed"
            actions = session.get_actions()

            response = UFOResponse(
                session_id=session_id,
                status=status,
                actions=actions,
                messages=[],
            )
            return jsonify(response.model_dump())
        except Exception as e:
            return (
                jsonify({"status": "failure", "error": f"Server error: {str(e)}"}),
                500,
            )

    @api.route("/api/clients")
    def list_clients():
        return jsonify({"online_clients": ws_manager.list_clients()})

    @api.route("/api/dispatch", methods=["POST"])
    def dispatch_task_api():
        data = request.json
        client_id = data["client_id"]
        task_content = data["request"]
        ws = ws_manager.get_client(client_id)
        if not ws:
            return jsonify({"error": "client not online"}), 404

        task_id = task_manager.new_task_id()
        import asyncio
        import json

        asyncio.run_coroutine_threadsafe(
            ws.send(
                json.dumps(
                    {"type": "task", "task_id": task_id, "request": task_content}
                )
            ),
            ws_event_loop,
        )
        return jsonify({"status": "dispatched", "task_id": task_id})

    @api.route("/api/task_result/<task_id>")
    def get_task_result(task_id: str):
        result = task_manager.get_result(task_id)
        if not result:
            return jsonify({"status": "pending"})
        return jsonify({"status": "done", "result": result})

    @api.route("/api/health")
    def health_check():
        return jsonify(
            {"status": "healthy", "online_clients": ws_manager.list_clients()}
        )

    return api
