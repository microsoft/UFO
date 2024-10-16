import time

from instantiation.config.config import Config
from ufo.automator.puppeteer import ReceiverManager

from PIL import ImageGrab
from pywinauto import Desktop

configs = Config.get_instance().config_data
if configs is not None:
    BACKEND = configs["CONTROL_BACKEND"]


class WindowsAppEnv:
    """
    The Windows App Environment.
    """

    def __init__(self, app_object: object) -> None:
        """
        Initialize the Windows App Environment.
        :param app_object: The app object containing the app information.
        """
        super().__init__()

        self.app_window = None
        self.app_root_name = app_object.app_root_name  # App executable name
        self.process_name = (
            app_object.description.lower()
        )  # Process name (e.g., 'word')
        self.win_app = app_object.win_app  # App Windows process name (e.g., 'winword')

        # Setup COM receiver for Windows application
        self.receive_factory = ReceiverManager._receiver_factory_registry["COM"][
            "factory"
        ]
        self.win_com_receiver = self.receive_factory.create_receiver(
            self.app_root_name, self.process_name
        )

    def start(self, cached_template_path: str) -> None:
        """
        Start the Window env.
        :param cached_template_path: The file path to start the env.
        """

        from ufo.automator.ui_control import openfile

        file_controller = openfile.FileController(BACKEND)
        file_controller.execute_code(
            {"APP": self.win_app, "file_path": cached_template_path}
        )

    def close(self):
        """
        Close the Window env.
        """

        com_object = self.win_com_receiver.get_object_from_process_name()
        com_object.Close()
        self.win_com_receiver.client.Quit()
        time.sleep(1)

    def save_screenshot(self, save_path: str) -> None:
        """
        Capture the screenshot of the current window or full screen if the window is not found.
        :param save_path: The path where the screenshot will be saved.
        :return: None
        """
        # Create a Desktop object
        desktop = Desktop(backend=BACKEND) 

        # Get a list of all windows, including those that are empty
        windows_list = desktop.windows()

        matched_window = None
        for window in windows_list:
            window_title = window.element_info.name.lower()
            if (
                self.process_name in window_title
            ):  # Match window name with app_root_name
                matched_window = window
                break

        if matched_window:
            # If the window is found, bring it to the foreground and capture a screenshot
            matched_window.set_focus()
            rect = matched_window.rectangle()
            screenshot = ImageGrab.grab(
                bbox=(rect.left, rect.top, rect.right, rect.bottom)
            )
        else:
            # If no window is found, take a full-screen screenshot
            print("Window not found, taking a full-screen screenshot.")
            screenshot = ImageGrab.grab()

        # Save the screenshot to the specified path
        screenshot.save(save_path)
        print(f"Screenshot saved to {save_path}")