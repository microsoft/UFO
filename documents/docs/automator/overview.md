# Application Puppeteer

The `Puppeteer` is a tool that allows UFO to automate and take actions on applications. Currently, UFO supports two types of actions: `GUI` and `API`. Each application has a shared GUI action interface to operate with mouse and keyboard events, and a private API action interface to operate with the application's native API. We illustrate the `Puppeteer` architecture in the figure below:

The state machine diagram for the `HostAgent` is shown below:
<h1 align="center">
    <img src="../../img/puppeteer.png"/> 
</h1>



!!! note
    UFO can also call in-app AI tools, such as `Copilot`, to assist with the automation process. This is achieved by using either `GUI` or `API` to interact with the in-app AI tool.

- [UI Automator](./ui_automator.md) - This action type is used to interact with the application's UI controls, such as buttons, text boxes, and menus. UFO uses the **UIA** or **Win32** APIs to interact with the application's UI controls.
- [API](./wincom_automator.md) - This action type is used to interact with the application's native API. Users and app developers can create their own API actions to interact with specific applications.
- [Web](./web_automator.md) - This action type is used to interact with web applications. UFO uses the [**crawl4ai**](https://github.com/unclecode/crawl4ai) library to extract information from web pages.
- [Bash](./bash_automator.md) - This action type is used to interact with the command line interface (CLI) of an application.
- [AI Tool](./ai_tool_automator.md) - This action type is used to interact with the LLM-based AI tools.

## Action Design Patterns

Actions in UFO are implemented using the [command](https://refactoring.guru/design-patterns/command) design pattern, which encapsulates a receiver, a command, and an invoker. The receiver is the object that performs the action, the command is the object that encapsulates the action, and the invoker is the object that triggers the action.

The basic classes for implementing actions in UFO are as follows:

| Role | Class | Description |
| --- | --- | --- |
| Receiver | `ufo.automator.basic.ReceiverBasic` | The base class for all receivers in UFO. Receivers are objects that perform actions on applications. |
| Command | `ufo.automator.basic.CommandBasic` | The base class for all commands in UFO. Commands are objects that encapsulate actions to be performed by receivers. |
| Invoker | `ufo.automator.puppeteer.AppPuppeteer` | The base class for the invoker in UFO. Invokers are objects that trigger commands to be executed by receivers. |

The advantage of using the command design pattern in the agent framework is that it allows for the decoupling of the sender and receiver of the action. This decoupling enables the agent to execute actions on different objects without knowing the details of the object or the action being performed, making the agent more flexible and extensible for new actions.

## Receiver

The `Receiver` is a central component in the Automator application that performs actions on the application. It provides functionalities to interact with the application and execute the action. All available actions are registered in the with the `ReceiverManager` class.

You can find the reference for a basic `Receiver` class below:

::: automator.basic.ReceiverBasic

<br>

## Command

The `Command` is a specific action that the `Receiver` can perform on the application. It encapsulates the function and parameters required to execute the action. The `Command` class is a base class for all commands in the Automator application.

You can find the reference for a basic `Command` class below:

::: automator.basic.CommandBasic

<br>

!!! note
    Each command must register with a specific `Receiver` to be executed using the `register_command` decorator. For example:
        @ReceiverExample.register
        class CommandExample(CommandBasic):
            ...
    

## Invoker (AppPuppeteer)

The `AppPuppeteer` plays the role of the invoker in the Automator application. It triggers the commands to be executed by the receivers. The `AppPuppeteer` equips the `AppAgent` with the capability to interact with the application's UI controls. It provides functionalities to translate action strings into specific actions and execute them. All available actions are registered in the `Puppeteer` with the `ReceiverManager` class.

You can find the implementation of the `AppPuppeteer` class in the `ufo/automator/puppeteer.py` file, and its reference is shown below.

::: automator.puppeteer.AppPuppeteer

<br>


## Receiver Manager
The `ReceiverManager` manages all the receivers and commands in the Automator application. It provides functionalities to register and retrieve receivers and commands. It is a complementary component to the `AppPuppeteer`.

::: automator.puppeteer.ReceiverManager

<br>

For further details, refer to the specific documentation for each component and class in the Automator module.