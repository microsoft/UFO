import gymnasium as gym

from ael.config.config import Config
import win32com.client as win32

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
        self.app_root_name = task_json_object.app_object.root_name
        self.win_app = task_json_object.app_object.win_app
        self.app_instance = win32.gencache.EnsureDispatch(self.app_root_name)

    def start(self, seed):
        """
        Start the Window env.
        :param seed: The seed file to start the env.
        """
        # close all the previous windows

        from ufo.automator.ui_control import openfile

        file_controller = openfile.FileController(BACKEND)        
        file_controller.execute_code({"APP": self.win_app, "file_path": seed})

    def close(self):
        """
        Close the Window env.
        """
        self.app_instance.Quit()