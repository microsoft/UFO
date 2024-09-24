import gymnasium as gym

from ael.config.config import Config
from ael.automator.word import app_control as control

configs = Config.get_instance().config_data

if configs is not None:
    BACKEND = configs["CONTROL_BACKEND"]


class WindowsAppEnv(gym.Env):
    """
    The Windows App Environment.
    """

    def __init__(self, app_root_name, process_name: str):
        """
        Initialize the Windows App Environment.
        :param app_root_name: The root name of the app.
        :param process_name: The process name of the app.
        """
        super(WindowsAppEnv, self).__init__()
        # app window
        self.app_window = None
        # app root name like: 'Word.Application'
        self._app_root_name = app_root_name
        # process name like : 'Word'
        self._process_name = process_name
        # app control instance
        self.app_control = control.AppControl(self._app_root_name)

    def start(self, seed):
        """
        Start the Window env.
        :param seed: The seed file to start the env.
        """
        # close all the previous windows
        self.app_control.open_file_with_app(seed)
        
        from ufo.automator.ui_control.inspector import ControlInspectorFacade

        desktop_windows = ControlInspectorFacade(BACKEND).get_desktop_windows()
        self.app_window = desktop_windows[0]
        self.app_window.set_focus()


    def close(self):
        """
        Close the Window env.
        """
        self.app_control.quit()