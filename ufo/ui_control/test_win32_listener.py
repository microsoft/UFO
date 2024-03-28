import win32com.client
from win32com.client import Dispatch
# 事件处理类
class WordEvents:
    def OnWindowSelectionChange(self, Sel):
        print("左键选择内容:")
        Sel = Dispatch(Sel)
        print(f"content: {Sel.Text}")
        print(f"font size: {Sel.Font.Size}")
        print(f"font name: {Sel.Font.Name}")


    def OnWindowBeforeRightClick(self, Sel, Cancel):
        print("右键选择内容:")
        Sel = Dispatch(Sel)
        print(f"content: {Sel.Text}")
        print(f"font size: {Sel.Font.Size}")
        print(f"font name: {Sel.Font.Name}")

    def OnWindowBeforeDoubleClick(self, Sel, Cancel):
        print("双击选择内容:")
        Sel = Dispatch(Sel)
        print(f"content: {Sel.Text}")
        print(f"font size: {Sel.Font.Size}")
        print(f"font name: {Sel.Font.Name}")

def listen_events():
    # 连接到现有的Word应用程序实例
    word_app = win32com.client.GetActiveObject("Word.Application")
    
    # Attach the event handler
    word_events = win32com.client.DispatchWithEvents(word_app, WordEvents)
    
    print("已连接到Word. 按 Ctrl+C 退出监听状态.")

    # 挂起脚本，允许事件响应，而无限循环阻塞
    try:
        while True:
            win32com.client.pythoncom.PumpWaitingMessages()
            # Known issue: Below sleep makes the python process hang if too short such as 0.01
            win32com.client.pythoncom.PumpWaitingMessages()
    except KeyboardInterrupt:
        print("程序已终止")

if __name__ == "__main__":
    listen_events()
