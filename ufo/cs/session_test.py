from uuid import uuid4
from ufo.cs.computer import Computer
from ufo.module.sessions.service_session import ServiceSession


def test_run_session_with_receivers():
    """Test session using app receivers when appropriate."""
    session_id = str(uuid4())
    session = ServiceSession(task=session_id, should_evaluate=False, id=session_id)
    session.init(request="open notepad and write 'hello world'")

    # Enhanced computer with receiver support
    computer = Computer("localhost")

    is_finished = session.is_finished()
    while not is_finished:
        session.step_forward()
        actions = session.get_commands()

        # Process all actions in the actions list
        action_results = {}
        for action in actions:
            # Computer will automatically choose appropriate receiver
            result = computer.run_action(action)
            action_results[action.call_id] = result

        # Update session state with collected results
        session.process_action_results(action_results)
        is_finished = session.is_finished()


def test_office_app_session():
    """Test session specifically for Office applications."""
    session_id = str(uuid4())
    session = ServiceSession(task=session_id, should_evaluate=False, id=session_id)
    session.init(
        request="open PowerPoint and create a new slide with title 'Hello World'"
    )

    computer = Computer("localhost")
    is_finished = session.is_finished()
    while not is_finished:
        session.step_forward()
        actions = session.get_commands()
        # Process all actions in the actions list
        action_results = {}
        for action in actions:
            # Run each action and collect the results
            result = computer.run_action(action)
            # Convert BaseModel result to dict if applicable
            if (
                hasattr(result, "__class__")
                and hasattr(result.__class__, "__name__")
                and hasattr(result, "model_dump")
            ):
                try:
                    # Check if it's a BaseModel instance by looking for the model_dump method
                    if callable(getattr(result, "model_dump", None)):
                        result = result.model_dump()
                except Exception:
                    # If conversion fails, keep the original result
                    pass

            action_results[action.call_id] = result

        # Update session state with collected results
        session.process_action_results(action_results)

        is_finished = session.is_finished()


def test_run_session():
    session_id = str(uuid4())
    session = ServiceSession(task=session_id, should_evaluate=False, id=session_id)
    session.init(request="open notepad and write 'hellow world'")
    computer = Computer("localhost")
    is_finished = session.is_finished()
    while not is_finished:
        session.step_forward()
        actions = session.get_commands()
        # Process all actions in the actions list
        action_results = {}
        for action in actions:
            # Run each action and collect the results
            result = computer.run_action(action)
            action_results[action.call_id] = result

        # Update session state with collected results
        session.process_action_results(action_results)

        is_finished = session.is_finished()


if __name__ == "__main__":
    test_office_app_session()
