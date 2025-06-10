from flask import Flask, request, jsonify
from uuid import uuid4
import logging

from ufo.cs.service_session import ServiceSession
from ufo.cs.contracts import UFORequest, UFOResponse
from ufo.config import Config


app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get application configuration
configs = Config.get_instance().config_data

# Dictionary to store active sessions
sessions = {}


@app.route('/api/ufo/task', methods=['POST'])
def run_task():
    """
    Handles task requests from clients.
    
    If session_id is None, creates a new session.
    Otherwise, updates the existing session with action results.
    
    Returns actions for the client to execute.
    """
    try:
        # Parse the request data
        data = request.json
        ufo_request = UFORequest(**data)
        
        # Handle session creation or retrieval
        session_id = ufo_request.session_id
        
        if session_id is None or session_id not in sessions:
            # Create a new session with a unique ID
            if session_id is None:
                session_id = str(uuid4())
            
            # Initialize a new session
            session = ServiceSession(task=session_id, should_evaluate=False, id=session_id)
            
            if ufo_request.request is None:
                return jsonify({
                    "error": "Request text is required for new sessions"
                }), 400
                
            # Initialize the session with the request
            session.init(request=ufo_request.request)
            
            # Store the session
            sessions[session_id] = session
            
            logger.info(f"Created new session: {session_id}")
        else:
            # Get the existing session
            session = sessions[session_id]
            
            # Update session state with action results
            if ufo_request.action_results:
                session.update_session_state_from_action_results(ufo_request.action_results)
                logger.info(f"Updated session {session_id} with action results")
        
        # Step the session forward to get the next actions
        session.step_forward()
        
        # Get actions to execute
        actions = session.get_actions()
        
        # Determine if the session is finished
        is_finished = session.is_finished()
        
        # Create the response
        status = "completed" if is_finished else "continue"
        
        response = UFOResponse(
            session_id=session_id,
            status=status,
            actions=actions,
            messages=[]  # Can add custom messages if needed
        )
        
        logger.info(f"Session {session_id} status: {status}, Actions: {len(actions)}")
        
        # If session is completed, we can remove it from our sessions dict to free resources
        if is_finished:
            logger.info(f"Session {session_id} completed, removing from active sessions")
            # Instead of removing immediately, consider a cleanup mechanism that removes after some time
            # sessions.pop(session_id, None) 
        
        return jsonify(response.model_dump())
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({
            "status": "failure",
            "error": f"Server error: {str(e)}"
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "active_sessions": len(sessions)}), 200


def start_server(host='0.0.0.0', port=5000, debug=False):
    """Start the Flask server"""
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    # Default to running on localhost:5000
    start_server(debug=True)

