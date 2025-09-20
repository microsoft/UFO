# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from .. import utils

from art import text2art
from typing import Tuple
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.align import Align
from rich import box


console = Console()

WELCOME_TEXT = """
Welcome to use UFO🛸, A UI-focused Agent for Windows OS Interaction. 
{art}
Please enter your request to be completed🛸: """.format(
    art=text2art("UFO")
)


def first_request() -> str:
    """
    Ask for the first request.
    :return: The first request.
    """

    return input()


def new_request() -> Tuple[str, bool]:
    """
    Ask for a new request.
    :return: The new request and whether the conversation is complete.
    """

    # Create a styled panel for the prompt
    prompt_panel = Panel.fit(
        "[bold cyan]What would you like me to help you with next?[/bold cyan]\n\n"
        "[dim]💡 Enter your new request, or type 'N' to exit[/dim]",
        title="🛸 [bold blue]UFO Assistant[/bold blue]",
        border_style="cyan",
        box=box.ROUNDED,
    )

    console.print()
    console.print(prompt_panel)
    console.print()

    request = Prompt.ask("[bold green]Your request[/bold green]", console=console)

    if request.upper() == "N":
        # Show goodbye message
        goodbye_panel = Panel.fit(
            "[bold yellow]👋 Thank you for using UFO! Goodbye![/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED,
        )
        console.print(goodbye_panel)
        complete = True
    else:
        # Show confirmation
        console.print(f"[dim]✨ Processing your request: [bold]{request}[/bold][/dim]")
        complete = False

    return request, complete


def experience_asker() -> bool:
    """
    Ask for saving the conversation flow for future reference.
    :return: Whether to save the conversation flow.
    """

    # Create an attractive panel for the experience saving prompt
    experience_panel = Panel(
        "[bold magenta]💾 Save Experience for Future Learning[/bold magenta]\n\n"
        "[dim]Would you like to save the current conversation flow?\n"
        "This helps UFO learn and improve for similar tasks in the future.[/dim]\n\n"
        "[bold cyan]Benefits:[/bold cyan]\n"
        "• 🚀 Faster execution for similar tasks\n"
        "• 🎯 Better accuracy over time\n"
        "• 🤝 Personalized assistance",
        title="🧠 [bold]Learning & Memory[/bold]",
        border_style="magenta",
        box=box.DOUBLE,
    )

    console.print()
    console.print(experience_panel)
    console.print()

    save_experience = Confirm.ask(
        "[bold green]Save this conversation flow?[/bold green]",
        default=True,
        console=console,
    )

    if save_experience:
        console.print(
            "[dim green]✅ Experience will be saved for future reference[/dim green]"
        )
    else:
        console.print("[dim yellow]ℹ️  Experience will not be saved[/dim yellow]")

    return save_experience


def question_asker(question: str, index: int) -> str:
    """
    Ask for the user input for the question.
    :param question: The question to ask.
    :param index: The index of the question.
    :return: The user input.
    """

    # Create a numbered question panel
    question_panel = Panel(
        f"[bold blue]❓ Question #{index}[/bold blue]\n\n" f"[white]{question}[/white]",
        title=f"🤔 [bold]Information Needed[/bold]",
        border_style="blue",
        box=box.ROUNDED,
    )

    console.print()
    console.print(question_panel)
    console.print()

    answer = Prompt.ask(
        f"[bold cyan]Your answer to question #{index}[/bold cyan]", console=console
    )

    # Show confirmation
    console.print(f"[dim green]✅ Answer recorded: {answer}[/dim green]")

    return answer


def sensitive_step_asker(action, control_text) -> bool:
    """
    Ask for confirmation for sensitive steps.
    :param action: The action to be performed.
    :param control_text: The control text.
    :return: Whether to proceed.
    """

    # Create a warning panel for sensitive actions
    warning_panel = Panel(
        f"[bold red]⚠️  Security Confirmation Required[/bold red]\n\n"
        f"[yellow]UFO is about to perform a potentially sensitive action:[/yellow]\n\n"
        f"[bold white]Action:[/bold white] [cyan]{action}[/cyan]\n"
        f"[bold white]Target:[/bold white] [cyan]{control_text}[/cyan]\n\n"
        f"[dim]Please review this action carefully before proceeding.[/dim]",
        title="🔒 [bold red]Security Check[/bold red]",
        border_style="red",
        box=box.HEAVY,
    )

    console.print()
    console.print(warning_panel)
    console.print()

    # Add some visual separation and emphasis
    console.print(
        "[bold red]🚨 IMPORTANT:[/bold red] This action may modify system settings or data."
    )
    console.print()

    proceed = Confirm.ask(
        "[bold yellow]Do you want to proceed with this action?[/bold yellow]",
        default=False,  # Default to False for security
        console=console,
    )

    if proceed:
        console.print("[dim green]✅ Action approved - proceeding...[/dim green]")
    else:
        console.print("[dim red]❌ Action cancelled by user[/dim red]")

    return proceed
