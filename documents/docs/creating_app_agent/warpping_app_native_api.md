# Wrapping Your App's Native API

UFO takes actions on applications based on UI controls, but providing native API to its toolboxes can enhance the efficiency and accuracy of the actions. This document provides guidance on how to wrap your application's native API into UFO's toolboxes.

## How to Wrap Your App's Native API?

Before developing the native API wrappers, we strongly recommend that you read the design of the [Automator](../automator/overview.md).

### Step 1: Create a Receiver for the Native API

The `Receiver` is a class that receives the native API calls from the `AppAgent` and executes them. To wrap your application's native API, you need to create a `Receiver` class that contains the methods to execute the native API calls.

To create a `Receiver` class, follow these steps:

1. **Create a Folder for Your Application:**

    - Navigate to the `ufo/automator/app_api/` directory.
    - Create a folder named after your application.

2. **Create a Python File:**

    - Inside the folder you just created, add a Python file named after your application.

3. **Define the Receiver Class:**

    - In the Python file, define a class named `{Your_Receiver}`, inheriting from the `ReceiverBasic` class located in `ufo/automator/basic.py`.
    - Initialize the `Your_Receiver` class with the object that executes the native API calls. For example, if your API is based on a `com` object, initialize the `com` object in the `__init__` method of the `Your_Receiver` class.

Example of `WinCOMReceiverBasic` class:
```python
class WinCOMReceiverBasic(ReceiverBasic):
    """
    The base class for Windows COM client.
    """

    _command_registry: Dict[str, Type[CommandBasic]] = {}

    def __init__(self, app_root_name: str, process_name: str, clsid: str) -> None:
        """
        Initialize the Windows COM client.
        :param app_root_name: The app root name.
        :param process_name: The process name.
        :param clsid: The CLSID of the COM object.
        """

        self.app_root_name = app_root_name
        self.process_name = process_name
        self.clsid = clsid
        self.client = win32com.client.Dispatch(self.clsid)
        self.com_object = self.get_object_from_process_name()
```

4. **Define Methods to Execute Native API Calls:**

    - Define the methods in the `Your_Receiver` class to execute the native API calls.

Example of `ExcelWinCOMReceiver` class:
```python
def table2markdown(self, sheet_name: str) -> str:
        """
        Convert the table in the sheet to a markdown table string.
        :param sheet_name: The sheet name.
        :return: The markdown table string.
        """

        sheet = self.com_object.Sheets(sheet_name)
        data = sheet.UsedRange()
        df = pd.DataFrame(data[1:], columns=data[0])
        df = df.dropna(axis=0, how="all")
        df = df.applymap(self.format_value)

        return df.to_markdown(index=False)
```

5. **Create a Factory Class:**

    - Create a Factory class to manage multiple `Receiver` classes. The Factory class should have a method to create the `Receiver` class based on the application name.

Example of `COMReceiverFactory` class:
```python
class COMReceiverFactory(ReceiverFactory):
    """
    The factory class for the COM receiver.
    """

    def create_receiver(self, app_root_name: str, process_name: str) -> WinCOMReceiverBasic:
        """
        Create the wincom receiver.
        :param app_root_name: The app root name.
        :param process_name: The process name.
        :return: The receiver.
        """

        com_receiver = self.__com_client_mapper(app_root_name)
        clsid = self.__app_root_mappping(app_root_name)

        if clsid is None or com_receiver is None:
            print_with_color(f"Warning: Win32COM API is not supported for {process_name}.", "yellow")
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
        }

        return win_com_client_mapping.get(app_root_name, None)
```

6. **Register the ReceiverFactory in ReceiverManager:**

    - Register your `ReceiverFactory` in the `ReceiverManager` class in the `ufo/automator/puppeteer.py` file.

Example:
```python
class ReceiverManager:
    """
    The class for the receiver manager.
    """

    def __init__(self):
        """
        Initialize the receiver manager.
        """
        self.receiver_registry = {}
        self.receiver_factories = {}
        self.ui_control_receiver: Optional[ControlReceiver] = None
        self.com_receiver: Optional[WinCOMReceiverBasic] = None

        self.load_receiver_factories()

    def load_receiver_factories(self) -> None:
        """
        Load the receiver factories. Now we have two types of receiver factories: UI control receiver factory and COM receiver factory.
        A receiver factory is responsible for creating the receiver for the specific type of receiver.
        """
        self.__register_receiver_factory("UIControl", UIControlReceiverFactory())
        self.__register_receiver_factory("COM", COMReceiverFactory())

    def __update_receiver_registry(self) -> None:
        """
        Update the receiver registry. A receiver registry is a dictionary that maps the command name to the receiver.
        """
        if self.ui_control_receiver is not None:
            self.receiver_registry.update(self.ui_control_receiver.self_command_mapping())
        if self.com_receiver is not None:
            self.receiver_registry.update(self.com_receiver.self_command_mapping())

    def create_com_receiver(self, app_root_name, process_name) -> WinCOMReceiverBasic:
        """
        Get the COM client.
        :param app_root_name: The app root name.
        :param process_name: The process name.
        """
        factory = self.receiver_factories.get("COM")
        self.com_receiver = factory.create_receiver(app_root_name, process_name)
        self.__update_receiver_registry()
        return self.com_receiver
```

The `Receiver` class is now ready to receive the native API calls from the `AppAgent`.

### Step 2: Create a Command for the Native API

Commands are the actions that the `AppAgent` can execute on the application. To create a command for the native API, you need to create a `Command` class that contains the method to execute the native API calls.

1. **Create a Command Class:**

    - Create a `Command` class in the same Python file where the `Receiver` class is located. The `Command` class should inherit from the `CommandBasic` class located in `ufo/automator/basic.py`.

Example:
```python
class WinCOMCommand(CommandBasic):
    """
    The abstract command interface.
    """

    def __init__(self, receiver: WinCOMReceiverBasic, params=None) -> None:
        """
        Initialize the command.
        :param receiver: The receiver of the command.
        """
        self.receiver = receiver
        self.params = params if params is not None else {}

    @abstractmethod
    def execute(self):
        pass

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the command.
        :return: The name of the command.
        """
        return cls.__name__
```

2. **Define the Execute Method:**

    - Define the `execute` method in the `Command` class to call the receiver to execute the native API calls.

Example:
```python
def execute(self):
    """
    Execute the command to insert a table.
    :return: The inserted table.
    """
    return self.receiver.insert_excel_table(
        sheet_name=self.params.get("sheet_name", 1),
        table=self.params.get("table"),
        start_row=self.params.get("start_row", 1),
        start_col=self.params.get("start_col", 1),
    )
```

3. **Register the Command Class:**

    - Register the `Command` class in the corresponding `Receiver` class using the `@your_receiver.register` decorator.

Example:
```python
@ExcelWinCOMReceiver.register
class InsertExcelTable(WinCOMCommand):
    ...
```

The `Command` class is now registered in the `Receiver` class and available for the `AppAgent` to execute the native API calls.

### Step 3: Provide Prompt Descriptions for the Native API

To let the `AppAgent` know the usage of the native API calls, you need to provide prompt descriptions.

1. **Create an api.yaml File:**

    - Create an `api.yaml` file in the `ufo/prompts/apps/{your_app_name}` directory.

2. **Define Prompt Descriptions:**

    - Define the prompt descriptions for the native API calls in the `api.yaml` file.

Example:
```yaml
table2markdown:
  summary: |-
    "table2markdown" is to get the table content in a sheet of the Excel app and convert it to markdown format.
  class_name: |-
    GetSheetContent
  usage: |-
    [1]

 API call: table2markdown(sheet_name: str)
    [2] Args:
      - sheet_name: The name of the sheet in the Excel app.
    [3] Example: table2markdown(sheet_name="Sheet1")
    [4] Available control item: Any control item in the Excel app.
    [5] Return: the markdown format string of the table content of the sheet.
```

!!! note
    The `table2markdown` is the name of the native API call. It `MUST` match the `name()` defined in the corresponding `Command` class!

3. **Configure the api.yaml File in config_dev.yaml:**

    - Configure the address of the `api.yaml` file in the `config_dev.yaml` file with the application name as the key and the path to the `api.yaml` file as the value.

Example:
```yaml
EXCEL_API_PROMPT: "ufo/prompts/apps/excel/api.yaml"
```

4. **Register the Prompt Address in APIPromptLoader:**
    
    - Register the prompt address in the `APIPromptLoader.load_api_prompt` method in the `ufo/prompter/agent_prompter.py` file.

Example:
```python
def load_api_prompt(self) -> Dict[str, str]:
    """
    Load the prompt template for COM APIs.
    :return: The prompt template for COM APIs.
    """
    prompt_address = configs["APP_API_PROMPT_ADDRESS"].get(self.root_name, None)

    print(prompt_address)

    if prompt_address:
        return AppAgentPrompter.load_prompt_template(prompt_address, None)
    else:
        return {}
```

You shoud add the following data to the `app2configkey_mapper` dictionary:

```python
"your_application_program_name": "YOUR_APPLICATION_API_PROMPT",
```

The `AppAgent` can now use the prompt descriptions to understand the usage of the native API calls.

---

By following these steps, you will have successfully wrapped the native API of your application into UFO's toolboxes, allowing the `AppAgent` to execute the native API calls on the application!
