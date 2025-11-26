# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Configuration Validation and Diagnostic Tool for UFO³

Validates configuration files and provides helpful diagnostics.

Usage:
    # Validate UFO configuration
    python -m ufo.tools.validate_config ufo

    # Validate Galaxy configuration
    python -m ufo.tools.validate_config galaxy

    # Validate both
    python -m ufo.tools.validate_config all

    # Show detailed configuration
    python -m ufo.tools.validate_config ufo --show-config
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

console = Console()


class ConfigValidator:
    """
    Configuration validator with helpful diagnostics.

    Features:
    - Validates config file structure
    - Checks for required fields
    - Detects common configuration errors
    - Shows configuration hierarchy
    - Provides migration suggestions
    """

    REQUIRED_UFO_FIELDS = {
        "HOST_AGENT": ["API_TYPE", "API_KEY", "API_MODEL"],
        "APP_AGENT": ["API_TYPE", "API_KEY", "API_MODEL"],
    }

    REQUIRED_GALAXY_FIELDS = {
        "CONSTELLATION_AGENT": ["API_TYPE", "API_KEY", "API_MODEL"],
    }

    def __init__(self, module: str):
        """
        Initialize ConfigValidator.

        :param module: Module name ("ufo" or "galaxy")
        """
        self.module = module
        self.new_path = Path(f"config/{module}")
        self.legacy_path = Path(f"{module}/config") if module == "ufo" else None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def check_paths(self) -> Tuple[bool, bool]:
        """
        Check which configuration paths exist.

        :return: (new_exists, legacy_exists)
        """
        new_exists = self.new_path.exists() and any(self.new_path.glob("*.yaml"))
        legacy_exists = (
            self.legacy_path
            and self.legacy_path.exists()
            and any(self.legacy_path.glob("*.yaml"))
        )
        return new_exists, legacy_exists

    def validate_structure(self) -> bool:
        """
        Validate configuration file structure.

        :return: True if validation passed
        """
        new_exists, legacy_exists = self.check_paths()

        if not new_exists and not legacy_exists:
            self.errors.append(
                f"No configuration found for {self.module}\n"
                f"Expected at: {self.new_path}/"
                + (f" or {self.legacy_path}/" if self.legacy_path else "")
            )
            return False

        if legacy_exists and not new_exists:
            self.warnings.append(
                f"Using legacy configuration path: {self.legacy_path}/\n"
                f"Consider migrating to: {self.new_path}/\n"
                f"Run: python -m ufo.tools.migrate_config"
            )

        if new_exists and legacy_exists:
            self.warnings.append(
                f"Configuration found in both locations:\n"
                f"  - {self.new_path}/ (active)\n"
                f"  - {self.legacy_path}/ (ignored)\n"
                f"Consider removing legacy config to avoid confusion"
            )

        return True

    def validate_fields(self, config: Dict[str, Any]) -> bool:
        """
        Validate required configuration fields.

        :param config: Configuration dictionary
        :return: True if validation passed
        """
        required_fields = (
            self.REQUIRED_UFO_FIELDS
            if self.module == "ufo"
            else self.REQUIRED_GALAXY_FIELDS
        )

        all_valid = True

        for section, fields in required_fields.items():
            if section not in config:
                self.errors.append(f"Missing required section: {section}")
                all_valid = False
                continue

            section_config = config[section]
            if not isinstance(section_config, dict):
                self.errors.append(f"Invalid section format: {section} (expected dict)")
                all_valid = False
                continue

            for field in fields:
                if field not in section_config:
                    self.errors.append(f"Missing required field: {section}.{field}")
                    all_valid = False
                    continue

                value = section_config[field]
                if not value or value in ["YOUR_KEY", "sk-", "YOUR_ENDPOINT"]:
                    self.warnings.append(
                        f"Placeholder value detected: {section}.{field} = '{value}'\n"
                        f"Please update with actual value"
                    )

        return all_valid

    def validate_api_config(self, config: Dict[str, Any]) -> None:
        """
        Validate API configuration.

        :param config: Configuration dictionary
        """
        agents = (
            ["HOST_AGENT", "APP_AGENT"]
            if self.module == "ufo"
            else ["CONSTELLATION_AGENT"]
        )

        for agent in agents:
            if agent not in config:
                continue

            agent_config = config[agent]
            api_type = agent_config.get("API_TYPE", "").lower()

            if api_type == "aoai":
                # Azure OpenAI specific validation
                if not agent_config.get("API_DEPLOYMENT_ID"):
                    self.warnings.append(
                        f"{agent}: API_DEPLOYMENT_ID recommended for AOAI"
                    )

            elif api_type == "azure_ad":
                # Azure AD specific validation
                required = ["AAD_TENANT_ID", "AAD_API_SCOPE", "AAD_API_SCOPE_BASE"]
                for field in required:
                    if not agent_config.get(field):
                        self.errors.append(
                            f"{agent}: {field} required for Azure AD auth"
                        )

    def show_tree(self, path: Path) -> None:
        """
        Show configuration file tree.

        :param path: Configuration directory path
        """
        if not path.exists():
            return

        tree = Tree(f"[bold blue]{path}/[/bold blue]", guide_style="dim")

        for file in sorted(path.glob("*.yaml")):
            tree.add(f"[cyan]{file.name}[/cyan]")

        console.print(tree)

    def show_report(self, config: Dict[str, Any] = None) -> None:
        """
        Show validation report.

        :param config: Configuration dictionary (optional)
        """
        console.print()
        console.print(
            Panel.fit(
                f"[bold]Configuration Validation Report[/bold]\n"
                f"Module: [cyan]{self.module}[/cyan]",
                title="🔍 Validation",
                border_style="blue",
            )
        )

        # Path information
        console.print(f"\n[bold]Configuration Paths:[/bold]")
        new_exists, legacy_exists = self.check_paths()

        if new_exists:
            console.print(f"  [green]✓[/green] {self.new_path}/ (active)")
            self.show_tree(self.new_path)
        else:
            console.print(f"  [red]✗[/red] {self.new_path}/ (not found)")

        if self.legacy_path:
            if legacy_exists:
                console.print(f"  [yellow]⚠[/yellow] {self.legacy_path}/ (legacy)")
                self.show_tree(self.legacy_path)
            else:
                console.print(f"  [dim]  {self.legacy_path}/ (not found)[/dim]")

        # Errors
        if self.errors:
            console.print(f"\n[bold red]Errors ({len(self.errors)}):[/bold red]")
            for error in self.errors:
                console.print(f"  [red]✗[/red] {error}")

        # Warnings
        if self.warnings:
            console.print(
                f"\n[bold yellow]Warnings ({len(self.warnings)}):[/bold yellow]"
            )
            for warning in self.warnings:
                console.print(f"  [yellow]⚠[/yellow] {warning}")

        # Info
        if self.info:
            console.print(f"\n[bold blue]Info ({len(self.info)}):[/bold blue]")
            for info_msg in self.info:
                console.print(f"  [blue]ℹ[/blue] {info_msg}")

        # Summary
        console.print()
        if not self.errors:
            console.print(
                Panel.fit(
                    "[bold green]✓ Configuration is valid![/bold green]"
                    + (
                        "\n\nConsider addressing warnings for best practices."
                        if self.warnings
                        else ""
                    ),
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel.fit(
                    f"[bold red]✗ Configuration has {len(self.errors)} error(s)[/bold red]\n\n"
                    "Please fix errors before running UFO³.",
                    border_style="red",
                )
            )

    def validate(self, show_config: bool = False) -> bool:
        """
        Run full validation.

        :param show_config: Whether to show configuration details
        :return: True if validation passed
        """
        # Check structure
        if not self.validate_structure():
            self.show_report()
            return False

        # Load configuration
        try:
            from config.config_loader import get_ufo_config, get_galaxy_config

            if self.module == "ufo":
                config_obj = get_ufo_config()
            else:
                config_obj = get_galaxy_config()

            config = config_obj._raw

            # Validate fields
            self.validate_fields(config)

            # Validate API config
            self.validate_api_config(config)

            # Show report
            self.show_report(config)

            # Show configuration if requested
            if show_config:
                self.show_configuration(config)

            return len(self.errors) == 0

        except Exception as e:
            self.errors.append(f"Failed to load configuration: {e}")
            self.show_report()
            return False

    def show_configuration(self, config: Dict[str, Any]) -> None:
        """
        Show configuration details.

        :param config: Configuration dictionary
        """
        console.print(f"\n[bold]Configuration Details:[/bold]")

        # Create table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Section", style="cyan", width=30)
        table.add_column("Key", style="yellow", width=30)
        table.add_column("Value", style="green")

        def add_config_rows(section_name: str, section_data: Any, prefix: str = ""):
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    if isinstance(value, dict):
                        add_config_rows(section_name, value, f"{prefix}{key}.")
                    else:
                        # Mask sensitive values
                        display_value = "***" if "KEY" in key else str(value)
                        table.add_row(
                            section_name if not prefix else "",
                            f"{prefix}{key}",
                            display_value,
                        )

        # Add rows for each section
        for section, data in config.items():
            if isinstance(data, dict):
                add_config_rows(section, data)

        console.print(table)


def main():
    """Main entry point for the validation tool."""
    parser = argparse.ArgumentParser(
        description="Validate UFO³ configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate UFO configuration
  python -m ufo.tools.validate_config ufo

  # Validate Galaxy configuration
  python -m ufo.tools.validate_config galaxy

  # Validate and show config
  python -m ufo.tools.validate_config ufo --show-config
        """,
    )

    parser.add_argument(
        "module",
        choices=["ufo", "galaxy", "all"],
        help="Module to validate (ufo, galaxy, or all)",
    )

    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show detailed configuration",
    )

    args = parser.parse_args()

    modules = ["ufo", "galaxy"] if args.module == "all" else [args.module]
    all_valid = True

    for module in modules:
        validator = ConfigValidator(module)
        valid = validator.validate(show_config=args.show_config)
        all_valid = all_valid and valid

        if len(modules) > 1:
            console.print("\n" + "=" * 70 + "\n")

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
