import gymnasium as gym
from gymnasium import spaces
from ..ui_control import control, screenshot as screen


class WindowsAppEnv(gym.Env):
    def __init__(self,app_root_name=None,exit_fail_times=5,score_threshold=5):
        """
        :param app_root_name: The app_root_name to be focused on.
        :param exit_fail_times: The available max continuent times of failure.
        :param score_threshold: The threshold of the score to do summary.
        :return: None
        """
        super(WindowsAppEnv, self).__init__()
        # 应用程序窗口
        self.app_root_name = app_root_name
        # s0->st action记录
        self.history_actions = []
        # s0->st states记录
        self.history_states = []
        # 3 observation state
        self.init_state = None
        self.last_state = None
        self.current_state = self.init_state
        # 最近失败次数
        self.recent_fail_times= 0 
        self.exit_fail_times = exit_fail_times
        # task exploration round
        self.round = 0
        self.score_threshold = score_threshold

    def step(self):
        """
        Interact with explorer agent and update the states.
        """
        self.last_state = self.current_state
        self.update_current_state()
        
    def reset(self):
        # 重置应用程序,放弃目前的状态，回到备份的状态文件
        return self.get_current_state()

    def update_current_state(self):
        # 从应用程序获取状态
        # 调用pywinauto、win32com等api来获取所有的状态信息
        self.current_state = control.get_app_states(self.app_root_name)
        if not self.init_state:
            self.init_state = self.current_state

    def get_all_states(self):
        """
        Return 3 states of the environment.
        :return: The 3 states of the environment.
        """
        return self._init_state,self._last_state,self._current_state
    
    def is_done(self):
        """
        :return: True if the fail times reach the max times, False otherwise.
        """
        return self._recent_fail_times >= self._exit_fail_times

def execute_task_summary(app_env:WindowsAppEnv):
    """
    Call the summary agent and execute the summary task.
    :param app_env: The WindowsAppEnv object TO do summary task.
    :return: The description of Task.
    """
    return ""

def execute_exploration(app_env:WindowsAppEnv):
    """
    Call the explorer action agent and execute the action
    :param app_env: The WindowsAppEnv object to do exploration task.
    :return: Record the actions and status of execution.
    """
    return None,None

def calculate_reward(app_env:WindowsAppEnv):
    """
    Calcluate the reward of the current state.
    :param app_env: The WindowsAppEnv object to calculate the reward.
    :return: The reward of the current state.
    """
    return 0