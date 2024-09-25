import gymnasium as gym
import time

from ael.config.config import Config
from ufo.automator.app_apis.word.wordclient import WordWinCOMReceiver

configs = Config.get_instance().config_data

if configs is not None:
    BACKEND = configs["CONTROL_BACKEND"]


class WindowsAppEnv(gym.Env):
    """
    The Windows App Environment.
    """

    def __init__(self, task_json_object):
        """
        Initialize the Windows App Environment.
        :param app_root_name: The root name of the app.
        :param process_name: The process name of the app.
        """
        super(WindowsAppEnv, self).__init__()
        self.app_window = None
        self.app_root_name = task_json_object.app_object.app_root_name
        self.process_name = task_json_object.app_object.description.lower()
        self.win_app = task_json_object.app_object.win_app
        self.client_clsid = task_json_object.app_object.client_clsid
        self.win_com_receiver = WordWinCOMReceiver(self.app_root_name, self.process_name, self.client_clsid)

    def start(self, seed):
        """
        Start the Window env.
        :param seed: The seed file to start the env.
        """
        from ufo.automator.ui_control import openfile

        file_controller = openfile.FileController(BACKEND)
        file_controller.execute_code({"APP": self.win_app, "file_path": seed})

    def close(self):
        """
        Close the Window env.
        """
        com_object = self.win_com_receiver.get_object_from_process_name()
        com_object.Close()
        self.win_com_receiver.client.Quit()
        time.sleep(1)