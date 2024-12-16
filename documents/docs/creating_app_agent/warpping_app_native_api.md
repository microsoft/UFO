# Wrapping Your App's Native API

UFO takes actions on applications based on UI controls, but providing native API to its toolboxes can enhance the efficiency and accuracy of the actions. This document provides guidance on how to wrap your application's native API into UFO's toolboxes.

## How to Wrap Your App's Native API?

Before developing the native API wrappers, we strongly recommend that you read the design of the [Automator](../automator/overview.md).

### Step 1: Create a Receiver for the Native API

The `Receiver` is a class that receives the native API calls from the `AppAgent` and executes them. To wrap your application's native API, you need to create a `Receiver` class that contains the methods to execute the native API calls.

To create a `Receiver` class, follow these steps:

#### 1. Create a Folder for Your Application

- Navigate to the `ufo/automator/app_api/` directory.
- Create a folder named after your application.

#### 2. Create a Python File

- Inside the folder you just created, add a Python file named after your application, for example, `{your_application}_client.py`.

#### 3. Define the Receiver Class

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
---

#### 4. Define Methods to Execute Native API Calls

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
---


#### 5. Create a Factory Class

- Create your Factory class inheriting from the `APIReceiverFactory` class to manage multiple `Receiver` classes that share the same API type.
- Implement the `create_receiver` and `name` methods in the `ReceiverFactory` class. The `create_receiver` method should return the `Receiver` class.
- By default, the `create_receiver` takes the `app_root_name` and `process_name` as parameters and returns the `Receiver` class.
- Register the `ReceiverFactory` class with the decorator `@ReceiverManager.register`.

Example of the `COMReceiverFactory` class:

```python
from ufo.automator.puppeteer import ReceiverManager

@ReceiverManager.register
class COMReceiverFactory(APIReceiverFactory):
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
            # print_with_color(f"Warning: Win32COM API is not supported for {process_name}.", "yellow")
            return None

        return com_receiver(app_root_name, process_name, clsid)

    @classmethod
    def name(cls) -> str:
        """
        Get the name of the receiver factory.
        :return: The name of the receiver factory.
        """
        return "COM"
```

!!!note
    The `create_receiver` method should return `None` if the application is not supported.


!!!note
    You must register your `ReceiverFactory` with the decorator `@ReceiverManager.register` for the `ReceiverManager` to manage the `ReceiverFactory`.

The `Receiver` class is now ready to receive the native API calls from the `AppAgent`.

### Step 2: Create a Command for the Native API

Commands are the actions that the `AppAgent` can execute on the application. To create a command for the native API, you need to create a `Command` class that contains the method to execute the native API calls.

#### 1. Create a Command Class

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
---

#### 2. Define the Execute Method

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
        

**3. Register the Command Class:**

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

#### 1. Create an api.yaml File

    - Create an `api.yaml` file in the `ufo/prompts/apps/{your_app_name}` directory.

#### 2. Define Prompt Descriptions

- Define the prompt descriptions for the native API calls in the `api.yaml` file.

Example:

```yaml
table2markdown:
summary: |-
    "table2markdown" is to get the table content in a sheet of the Excel app and convert it to markdown format.
class_name: |-
    GetSheetContent
usage: |-
    [1] API call: table2markdown(sheet_name: str)
    [2] Args:
    - sheet_name: The name of the sheet in the Excel app.
    [3] Example: table2markdown(sheet_name="Sheet1")
    [4] Available control item: Any control item in the Excel app.
    [5] Return: the markdown format string of the table content of the sheet.
```
    

!!! note
    The `table2markdown` is the name of the native API call. It `MUST` match the `name()` defined in the corresponding `Command` class!


#### 3. Register the Prompt Address in `config_dev.yaml`
    
- Register the prompt address by adding to the `APP_API_PROMPT_ADDRESS` field of `config_dev.yaml` file with the application program name as the key and the prompt file address as the value.

Example:
```yaml
APP_API_PROMPT_ADDRESS: {
    "WINWORD.EXE": "ufo/prompts/apps/word/api.yaml",
    "EXCEL.EXE": "ufo/prompts/apps/excel/api.yaml",
    "msedge.exe": "ufo/prompts/apps/web/api.yaml",
    "chrome.exe": "ufo/prompts/apps/web/api.yaml"
    "your_application_program_name": "YOUR_APPLICATION_API_PROMPT"
} 
```

!!!note
    The `your_application_program_name` **must** match the name of the application program.

The `AppAgent` can now use the prompt descriptions to understand the usage of the native API calls.

---

By following these steps, you will have successfully wrapped the native API of your application into UFO's toolboxes, allowing the `AppAgent` to execute the native API calls on the application!
