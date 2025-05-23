#  Bash Automator

UFO allows the `HostAgent` to execute bash commands on the host machine. The bash commands can be used to open applications or execute system commands. The `Bash Automator` is implemented in the `ufo/automator/app_apis/shell` module.


!!!note
    Only `HostAgent` is currently supported by the Bash Automator.

## Receiver
The Web Automator receiver is the `ShellReceiver` class defined in the `ufo/automator/app_apis/shell/shell_client.py` file. 

::: automator.app_apis.shell.shell_client.ShellReceiver


<br>

## Command

We now only support one command in the Bash Automator to execute a bash command on the host machine.

```python
@ShellReceiver.register
class RunShellCommand(ShellCommand):
    """
    The command to run the crawler with various options.
    """

    def execute(self):
        """
        Execute the command to run the crawler.
        :return: The result content.
        """
        return self.receiver.run_shell(params=self.params)

    @classmethod
    def name(cls) -> str:
        """
        The name of the command.
        """
        return "run_shell"
```


Below is the list of available commands in the Web Automator that are currently supported by UFO:

| Command Name | Function Name | Description |
|--------------|---------------|-------------|
| `RunShellCommand` | `run_shell` | Get the content of a web page into a markdown format. |
