import gymnasium as gym
from gymnasium import spaces
from ..ui_control import control, screenshot as screen


class WindowsAppEnv(gym.Env):
    def __init__(self,app_window=None):
        """
        :param app_window: The app_window to be focused on.从中解析出所有需要的state
        :return: None
        """
        super(WindowsAppEnv, self).__init__()
        # 定义状态空间和动作空间
        # self.action_space = spaces.Discrete(2)  # 例如，两个动作
        # self.observation_space = spaces.Box(low=0, high=255, shape=(480, 640, 3), dtype=np.uint8)  # 假设状态是一个图像

        # 初始化 Windows 应用程序
        self.init_state = control.get_app_states(app_window)
        self.last_state = None
        # 最近失败次数
        self.recent_fail_times= 0 

    def step(self, action):
        # 执行动作，例如点击或输入
        # prompt the exploration_action_agent to act
        # actions includes the initive action apis

        # 获取新的状态
        new_state = self.get_state()

        # 计算奖励
        reward = self.calculate_reward(new_state)

        # 检查是否中断
        if self.is_interupted(new_state):
            pass
        
        done = self.is_done(new_state)

        return new_state, reward, done, {}

    def reset(self):
        # 重置应用程序状态
        self.app.window().reset()
        return self.get_state()

    def get_state(self):
        # 从应用程序获取状态
        # 调用pywinauto、win32com的来获取所有的状态信息

        
        return self.app.window().capture_as_image()

    def calculate_reward(self, state):
        """
        :param state: The current state to calculate the reward.
        :return: The reward of the current state.
        """
        return 0  # 示例奖励
    
    def is_interupted(self, state):
        # 定义何时中断一个 episode
        return False
    

    def is_done(self, state):
        # 定义何时结束一个 episode
        return False  # 示例结束条件