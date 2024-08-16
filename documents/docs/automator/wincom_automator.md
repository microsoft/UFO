# API Automator

UFO currently support the use of [`Win32 API`](https://learn.microsoft.com/en-us/windows/win32/api/) API automator to interact with the application's native API. We implement them in python using the [`pywin32`](https://pypi.org/project/pywin32/) library. The API automator now supports `Word` and `Excel` applications, and we are working on extending the support to other applications.

## Configuration

There are several configurations that need to be set up before using the API Automator in the `config_dev.yaml` file. Below is the list of configurations related to the API Automator:

| Configuration Option    | Description                                                                                             | Type     | Default Value |
|-------------------------|---------------------------------------------------------------------------------------------------------|----------|---------------|
| `USE_APIS`              | Whether to allow the use of application APIs.                                                           | Boolean  | True          |
| `APP_API_PROMPT_ADDRESS`      | The prompt address for the application API. | Dict | {"WINWORD.EXE": "ufo/prompts/apps/word/api.yaml", "EXCEL.EXE": "ufo/prompts/apps/excel/api.yaml", "msedge.exe": "ufo/prompts/apps/web/api.yaml", "chrome.exe": "ufo/prompts/apps/web/api.yaml"} |

!!! note
    Only `WINWORD.EXE` and `EXCEL.EXE` are currently supported by the API Automator. 


## Receiver
The base class for the receiver of the API Automator is the `WinCOMReceiverBasic` class defined in the `ufo/automator/app_apis/basic` module. It is initialized with the application's win32 com object and provides functionalities to interact with the application's native API. Below is the reference for the `WinCOMReceiverBasic` class:

::: automator.app_apis.basic.WinCOMReceiverBasic

The receiver of `Word` and `Excel` applications inherit from the `WinCOMReceiverBasic` class. The `WordReceiver` and `ExcelReceiver` classes are defined in the `ufo/automator/app_apis/word` and `ufo/automator/app_apis/excel` modules, respectively:


## Command

The command of the API Automator for the `Word` and `Excel` applications in located in the `client` module in the `ufo/automator/app_apis/{app_name}` folder inheriting from the `WinCOMCommand` class. It encapsulates the function and parameters required to execute the action. Below is an example of a `WordCommand` class that inherits from the `SelectTextCommand` class:

```python
@WordWinCOMReceiver.register
class SelectTextCommand(WinCOMCommand):
    """
    The command to select text.
    """

    def execute(self):
        """
        Execute the command to select text.
        :return: The selected text.
        """
        return self.receiver.select_text(self.params.get("text"))

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "select_text"
```

!!! note
    The concrete command classes must implement the `execute` method to execute the action and the `name` method to return the name of the atomic command.

!!! note
    Each command must register with a concrete `WinCOMReceiver` to be executed using the `register` decorator.

Below is the list of available commands in the API Automator that are currently supported by UFO:

### Word API Commands

| Command Name | Function Name | Description |
|--------------|---------------|-------------|
| `InsertTableCommand` | `insert_table` | Insert a table to a Word document. |
| `SelectTextCommand` | `select_text` | Select the text in a Word document. |
| `SelectTableCommand` | `select_table` | Select a table in a Word document. |


### Excel API Commands

| Command Name | Function Name | Description |
|--------------|---------------|-------------|
| `GetSheetContentCommand` | `get_sheet_content` | Get the content of a sheet in the Excel app. |
| `Table2MarkdownCommand` | `table2markdown` | Convert the table content in a sheet of the Excel app to markdown format. |
| `InsertExcelTableCommand` | `insert_excel_table` | Insert a table to the Excel sheet. |


!!! tip
    Please refer to the `ufo/prompts/apps/{app_name}/api.yaml` file for the prompt details for the commands.

!!! tip
    You can customize the commands by adding new command classes to the `ufo/automator/app_apis/{app_name}/` module.

  
  