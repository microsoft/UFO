# Web Automator

We also support the use of the `Web Automator` to get the content of a web page. The `Web Automator` is implemented in `ufo/autoamtor/app_apis/web` module. 

## Configuration

There are several configurations that need to be set up before using the API Automator in the `config_dev.yaml` file. Below is the list of configurations related to the API Automator:

| Configuration Option    | Description                                                                                             | Type     | Default Value |
|-------------------------|---------------------------------------------------------------------------------------------------------|----------|---------------|
| `USE_APIS`              | Whether to allow the use of application APIs.                                                           | Boolean  | True          |
| `APP_API_PROMPT_ADDRESS`      | The prompt address for the application API. | Dict | {"WINWORD.EXE": "ufo/prompts/apps/word/api.yaml", "EXCEL.EXE": "ufo/prompts/apps/excel/api.yaml", "msedge.exe": "ufo/prompts/apps/web/api.yaml", "chrome.exe": "ufo/prompts/apps/web/api.yaml"} |

!!!note
    Only `msedge.exe` and `chrome.exe` are currently supported by the Web Automator.

## Receiver
The Web Automator receiver is the `WebReceiver` class defined in the `ufo/automator/app_apis/web/webclient.py` module:

::: automator.app_apis.web.webclient.WebReceiver

<br>

## Command

We now only support one command in the Web Automator to get the content of a web page into a markdown format. More commands will be added in the future for the Web Automator.

```python
@WebReceiver.register
class WebCrawlerCommand(WebCommand):
    """
    The command to run the crawler with various options.
    """

    def execute(self):
        """
        Execute the command to run the crawler.
        :return: The result content.
        """
        return self.receiver.web_crawler(
            url=self.params.get("url"),
            ignore_link=self.params.get("ignore_link", False),
        )

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "web_crawler"
```


Below is the list of available commands in the Web Automator that are currently supported by UFO:

| Command Name | Function Name | Description |
|--------------|---------------|-------------|
| `WebCrawlerCommand` | `web_crawler` | Get the content of a web page into a markdown format. |


!!! tip
    Please refer to the `ufo/prompts/apps/web/api.yaml` file for the prompt details for the `WebCrawlerCommand` command.