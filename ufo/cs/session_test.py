from uuid import uuid4
from ufo.cs.computer import Computer
from ufo.cs.service_session import ServiceSession


def test_run_session():
    session_id = str(uuid4())
    session = ServiceSession(task=session_id, should_evaluate=False, id=session_id)
    session.init(request="open notepad and write 'hellow world'")
    computer = Computer('localhost')
    is_finished = session.is_finished()
    while not is_finished:
        session.step_forward()
        actions = session.get_actions()
        # Process all actions in the actions list
        action_results = {}
        for action in actions:
            # Run each action and collect the results
            result = computer.run_action(action)
            action_results[action.call_id] = result
        
        # Update session state with collected results
        session.update_session_state_from_action_results(action_results)

        is_finished = session.is_finished()

if __name__ == "__main__":
    test_run_session()