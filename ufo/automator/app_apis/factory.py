# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Type, Dict, Any

from ufo.automator.app_apis.basic import WinCOMReceiverBasic
from ufo.automator.app_apis.excel.excelclient import ExcelWinCOMReceiver
from ufo.automator.app_apis.powerpoint.powerpointclient import PowerPointWinCOMReceiver
from ufo.automator.app_apis.shell.shell_client import ShellReceiver
from ufo.automator.app_apis.web.webclient import WebReceiver
from ufo.automator.app_apis.word.wordclient import WordWinCOMReceiver
from ufo.automator.basic import ReceiverBasic, ReceiverFactory
from ufo.automator.puppeteer import ReceiverManager
from ufo.utils import print_with_color


class APIReceiverFactory(ReceiverFactory):
    """
    The factory class for the API receiver.
    """

    @classmethod
    def is_api(cls) -> bool:
        """
        Check if the receiver is API.
        """
        return True


@ReceiverManager.register
class COMReceiverFactory(APIReceiverFactory):
    """
    The factory class for the COM receiver.
    """

    def create_receiver(
        self, app_root_name: str, process_name: str
    ) -> WinCOMReceiverBasic:
        """
        Create the wincom receiver.
        :param app_root_name: The app root name.
        :param process_name: The process name.
        :return: The receiver.
        """

        com_receiver = self.__com_client_mapper(app_root_name)
        clsid = self.__app_root_mappping(app_root_name)

        if clsid is None or com_receiver is None:

            return None

        return com_receiver(app_root_name, process_name, clsid)

    def __com_client_mapper(self, app_root_name: str) -> Type[WinCOMReceiverBasic]:
        """
        Map the app root to the corresponding COM client.
        :param app_root_name: The app root name.
        :return: The COM client.
        """
        win_com_client_mapping = {
            "WINWORD.EXE": WordWinCOMReceiver,
            "EXCEL.EXE": ExcelWinCOMReceiver,
            "POWERPNT.EXE": PowerPointWinCOMReceiver,
        }

        com_receiver = win_com_client_mapping.get(app_root_name, None)

        return com_receiver

    def __app_root_mappping(self, app_root_name: str) -> str:
        """
        Map the app root to the corresponding app.
        :return: The CLSID of the COM object.
        """

        win_com_map = {
            "WINWORD.EXE": "Word.Application",
            "EXCEL.EXE": "Excel.Application",
            "POWERPNT.EXE": "PowerPoint.Application",
            "olk.exe": "Outlook.Application",
        }

        return win_com_map.get(app_root_name, None)

    @classmethod
    def name(cls) -> str:
        """
        The name of the factory.
        """
        return "COM"


@ReceiverManager.register
class WebReceiverFactory(APIReceiverFactory):
    """
    The factory class for the COM receiver.
    """

    def create_receiver(self, app_root_name: str, *args, **kwargs) -> ReceiverBasic:
        """
        Create the web receiver.
        :param app_root_name: The app root name.
        :param process_name: The process name.
        :return: The receiver.
        """

        if app_root_name not in self.supported_app_roots:
            return None

        web_receiver = WebReceiver()
        print_with_color(f"Web receiver created for {app_root_name}.", "green")

        return web_receiver

    @property
    def supported_app_roots(self):
        """
        Get the supported app roots.
        """
        return ["msedge.exe", "chrome.exe"]

    @classmethod
    def name(cls) -> str:
        """
        The name of the factory.
        """
        return "Web"


@ReceiverManager.register
class ShellReceiverFactory(APIReceiverFactory):
    """
    The factory class for the API receiver.
    """

    def create_receiver(self, *args, **kwargs) -> ReceiverBasic:
        """
        Create the web receiver.
        :param app_root_name: The app root name.
        :return: The receiver.
        """

        return ShellReceiver()

    @property
    def supported_app_roots(self):
        """
        Get the supported app roots.
        """
        return

    @classmethod
    def name(cls) -> str:
        """
        The name of the factory.
        """
        return "Shell"


class MCPReceiver(ReceiverBasic):
    """
    MCP receiver that wraps existing receivers to expose functionality via MCP protocol.
    """
    
    _command_registry: Dict[str, Type] = {}
    
    def __init__(self, app_namespace: str, underlying_receiver: ReceiverBasic):
        """
        Initialize the MCP receiver.
        :param app_namespace: The application namespace (word, excel, powerpoint, web, shell)
        :param underlying_receiver: The underlying receiver to wrap
        """
        self.app_namespace = app_namespace
        self.underlying_receiver = underlying_receiver
    @property
    def type_name(self):
        return f"MCP_{self.app_namespace.upper()}"
    
    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP tool by delegating to the underlying receiver.
        :param tool_name: The name of the tool to execute
        :param tool_args: The arguments for the tool
        :return: The result of the tool execution
        """
        try:
            # Check if the underlying receiver has the method
            if hasattr(self.underlying_receiver, tool_name):
                method = getattr(self.underlying_receiver, tool_name)
                
                # Unpack tool_args dictionary as keyword arguments
                if tool_args:
                    result = method(**tool_args)
                else:
                    result = method()
                    
                return {
                    "success": True,
                    "result": result,
                    "tool_name": tool_name,
                    "namespace": self.app_namespace
                }
            else:                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not available in {self.app_namespace} receiver",
                    "tool_name": tool_name,
                    "namespace": self.app_namespace
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing tool '{tool_name}': {str(e)}",
                "tool_name": tool_name,
                "namespace": self.app_namespace
            }


@ReceiverManager.register
class MCPReceiverFactory(APIReceiverFactory):
    """
    The factory class for MCP receivers that wrap existing application receivers.
    """
    
    def __init__(self):
        """
        Initialize the MCP receiver factory.
        """
        super().__init__()
    
    def create_receiver(self, app_namespace: str, app_root_name: str = None, process_name: str = None) -> ReceiverBasic:
        """
        Create an MCP receiver for the specified application namespace.
        :param app_namespace: The application namespace (word, excel, powerpoint, web, shell)
        :param app_root_name: The app root name (for COM applications)
        :param process_name: The process name (for COM applications)
        :return: The MCP receiver wrapping the appropriate underlying receiver
        """
        underlying_receiver = None
        
        # Create the appropriate underlying receiver based on the namespace
        if app_namespace.lower() in ["word", "excel", "powerpoint"]:
            # For COM applications, use the COMReceiverFactory
            com_factory = COMReceiverFactory()
            if app_root_name and process_name:
                underlying_receiver = com_factory.create_receiver(app_root_name, process_name)
        elif app_namespace.lower() == "web":
            # For web applications, use the WebReceiverFactory
            web_factory = WebReceiverFactory()
            if app_root_name:
                underlying_receiver = web_factory.create_receiver(app_root_name)
            else:
                underlying_receiver = WebReceiver()
        elif app_namespace.lower() == "shell":
            # For shell operations, use the ShellReceiverFactory
            shell_factory = ShellReceiverFactory()
            underlying_receiver = shell_factory.create_receiver()
        
        if underlying_receiver is None:
            return None
            
        # Wrap the underlying receiver in an MCP receiver
        mcp_receiver = MCPReceiver(app_namespace, underlying_receiver)
        print_with_color(f"MCP receiver created for {app_namespace}.", "green")
        
        return mcp_receiver
    
    @property
    def supported_app_roots(self):
        """
        Get the supported app roots for MCP.
        """
        return ["word", "excel", "powerpoint", "web", "shell"]
    
    @classmethod
    def name(cls) -> str:
        """
        The name of the factory.
        """
        return "MCP"
