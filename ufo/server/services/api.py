import asyncio
import datetime
from uuid import uuid4

from flask import Blueprint, jsonify, request
from ufo.cs.contracts import ClientRequest, ServerResponse

from .session_manager import SessionManager
from .task_manager import TaskManager
from .ws_manager import WSManager


def create_api_blueprint(
    session_manager: SessionManager,
    task_manager: TaskManager,
    ws_manager: WSManager,
    ws_event_loop: asyncio.AbstractEventLoop,
):
    """
    Create and configure a Flask API blueprint for UFO server REST endpoints.

    This function registers all required HTTP routes for session management, client listing,
    task dispatching, and health checks. It uses the provided session manager, task manager,
    and WebSocket manager to handle business logic, and the specified event loop for async operations.

    :param session_manager: The manager responsible for handling session state.
    :param task_manager: The manager responsible for task ID generation and results.
    :param ws_manager: The manager responsible for managing online WebSocket clients.
    :param ws_event_loop: The asyncio event loop used for scheduling async WebSocket operations.
    :return: A Flask Blueprint object with all registered API endpoints.
    """
    api = Blueprint("api", __name__)

    @api.route("/api/ufo/task", methods=["POST"])
    def run_task():
        """
        Handle a client task request. If no session exists, creates a new one.
        Otherwise, updates the existing session with action results.
        :return: JSON response with session_id, status, actions, and messages.
        """
        try:
            data = request.json
            ufo_request = ClientRequest(**data)
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

            response = ServerResponse(
                session_id=session_id,
                status=status,
                actions=actions,
                agent_name="Placeholder Agent",  # Replace with actual agent name if available
                process_name="Placeholder Process",  # Replace with actual process name if available
                root_name="Placeholder Root",  # Replace with actual root name if available
                messages=[],
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )
            return jsonify(response.model_dump())
        except Exception as e:
            return (
                jsonify({"status": "failure", "error": f"Server error: {str(e)}"}),
                500,
            )

    @api.route("/api/clients")
    def list_clients():
        """
        List all online clients.
        :return: JSON response with a list of online client IDs.
        """
        return jsonify({"online_clients": ws_manager.list_clients()})

    @api.route("/api/dispatch", methods=["POST"])
    def dispatch_task_api():
        """
        Dispatch a task to a specific client identified by client_id.
        :return: JSON response indicating the task has been dispatched or an error if the client is not online.
        """
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
        """
        Get the result of a task by its ID.
        :param task_id: The ID of the task to retrieve the result for.
        :return: JSON response with the task result or a status indicating the task is still pending.
        """
        result = task_manager.get_result(task_id)
        if not result:
            return jsonify({"status": "pending"})
        return jsonify({"status": "done", "result": result})

    @api.route("/api/health")
    def health_check():
        """
        Health check endpoint to verify the server is running and list online clients.
        :return: JSON response with server status and list of online clients.
        """
        return jsonify(
            {"status": "healthy", "online_clients": ws_manager.list_clients()}
        )

    return api
