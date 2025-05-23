import argparse
import json
import logging
import sys
import time
import requests

from ufo.cs.computer import Computer
from ufo.cs.contracts import UFORequest, UFOResponse


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UFOWebClient:
    """
    Client for interacting with the UFO web service.
    Sends requests to the service, executes actions, and sends results back.
    """
    def __init__(self, server_url, computer_name="client"):
        """
        Initialize the UFO web client
        
        Args:
            server_url (str): URL of the UFO web service
            computer_name (str): Name for the Computer instance
        """
        self.server_url = server_url.rstrip('/')
        self.computer = Computer(computer_name)
        self.session_id = None
        
    def run_task(self, request_text):
        """
        Run a task by communicating with the UFO web service
        
        Args:
            request_text (str): The user's request text
            
        Returns:
            bool: True if task completed successfully, False otherwise
        """
        try:
            # Initial request to start the session
            response = self._send_request(request_text)
            
            # Process the session until it's completed or fails
            while True:
                if response.status == "failure":
                    logger.error(f"Task failed: {response.error}")
                    return False
                
                elif response.status == "completed":
                    logger.info("Task completed successfully")
                    return True
                
                # Execute the actions and collect results
                action_results = self._execute_actions(response.actions)
                
                # Send the results back to the server
                response = self._send_request(None, action_results)
                
        except Exception as e:
            logger.error(f"Error running task: {str(e)}", exc_info=True)
            return False
    
    def _send_request(self, request_text=None, action_results=None):
        """
        Send a request to the UFO web service
        
        Args:
            request_text (str, optional): User's request text
            action_results (dict, optional): Results from executed actions
            
        Returns:
            UFOResponse: Response from the server
        """
        # Prepare the request data
        request_data = {
            "session_id": self.session_id
        }
        
        if request_text is not None:
            request_data["request"] = request_text
            
        if action_results is not None:
            request_data["action_results"] = action_results
        
        # Send the request to the server
        ufo_request = UFORequest(**request_data)
        response = requests.post(
            f"{self.server_url}/api/ufo/task",
            json=ufo_request.model_dump(),
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        if response.status_code != 200:
            raise Exception(f"Server returned error: {response.status_code}, {response.text}")
        
        # Parse the response
        response_data = response.json()
        ufo_response = UFOResponse(**response_data)
        
        # Update the session ID if needed
        if self.session_id is None and ufo_response.session_id is not None:
            self.session_id = ufo_response.session_id
            logger.info(f"Session ID: {self.session_id}")
        
        return ufo_response
    
    def _execute_actions(self, actions):
        """
        Execute the actions provided by the server
        
        Args:
            actions (list): List of actions to execute
            
        Returns:
            dict: Results from executing the actions
        """
        action_results = {}
        
        if actions:
            logger.info(f"Executing {len(actions)} actions...")
            
            # Process each action
            for action in actions:
                logger.info(f"Running action: {action.name}")
                
                # Execute the action and collect the result
                result = self.computer.run_action(action)
                action_results[action.call_id] = result
                
                # Add a small delay between actions to prevent overloading
                time.sleep(0.1)
        
        return action_results


def main():
    """Main entry point for the UFO web client"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='UFO Web Client')
    parser.add_argument('--server', dest='server_url', default='http://localhost:5000',
                        help='UFO Web Service URL (default: http://localhost:5000)')
    parser.add_argument('--request', dest='request_text', default='open notepad and write "Hello, World!"',
                        help='The task request text')
    args = parser.parse_args()
    
    # Create and run the client
    client = UFOWebClient(args.server_url)
    success = client.run_task(args.request_text)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()