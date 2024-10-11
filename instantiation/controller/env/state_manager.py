import time

from instantiation.controller.config.config import Config
from ufo.automator.puppeteer import ReceiverManager

configs = Config.get_instance().config_data

if configs is not None:
    BACKEND = configs["CONTROL_BACKEND"]


class WindowsAppEnv:
    """
    The Windows App Environment.
    """

    def __init__(self, app_object):
        """
        Initialize the Windows App Environment.
        :param app_object: The app object containing the app information.
        """

        super(WindowsAppEnv, self).__init__()
        self.app_window = None
        self.app_root_name = app_object.app_root_name
        self.process_name = app_object.description.lower()
        self.win_app = app_object.win_app

        self.receive_factory = ReceiverManager._receiver_factory_registry["COM"][
            "factory"
        ]
        self.win_com_receiver = self.receive_factory.create_receiver(
            self.app_root_name, self.process_name
        )

    def start(self, cached_template_path):
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
