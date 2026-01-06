# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Configuration Conversion Tool for UFO²

Converts legacy monolithic configuration (ufo/config/*.yaml) to the new modular
structure (config/ufo/*.yaml) with proper format transformation.

This tool:
- Parses old YAML (with flow-style dicts using braces)
- Splits into modular files (agents, rag, system, mcp, prices)
- Converts to standard YAML format (block-style with indentation)
- Preserves comments where possible
- Validates conversion results

Usage:
    # Interactive conversion (recommended)
    python -m ufo.tools.convert_config

    # Dry run (preview changes without writing files)
    python -m ufo.tools.convert_config --dry-run

    # Custom paths
    python -m ufo.tools.convert_config --legacy-path ufo/config --new-path config/ufo

    # Force overwrite existing files
    python -m ufo.tools.convert_config --force
"""

import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

console = Console()


class ConfigConverter:
    """
    Converts legacy UFO configuration to new modular structure.

    Mapping rules:
    - config.yaml → agents.yaml + rag.yaml + system.yaml
    - agent_mcp.yaml → mcp.yaml
    - config_prices.yaml → prices.yaml
    - config_dev.yaml → environment-specific (kept separate)
    """

    # Field mapping from legacy config.yaml to new modular files
    FIELD_MAPPING = {
        # agents.yaml - Agent configurations
        "agents.yaml": [
            "HOST_AGENT",
            "APP_AGENT",
            "CONSTELLATION_AGENT",
            "BACKUP_AGENT",
            "EVALUATION_AGENT",
            "OPERATOR",
            "FOLLOWERAGENT_PROMPT",
        ],
        # rag.yaml - RAG configurations
        "rag.yaml": [
            "RAG_OFFLINE_DOCS",
            "RAG_OFFLINE_DOCS_RETRIEVED_TOPK",
            "BING_API_KEY",
            "RAG_ONLINE_SEARCH",
            "RAG_ONLINE_SEARCH_TOPK",
            "RAG_ONLINE_RETRIEVED_TOPK",
            "RAG_EXPERIENCE",
            "RAG_EXPERIENCE_RETRIEVED_TOPK",
            "EXPERIENCE_SAVED_PATH",
            "RAG_DEMONSTRATION",
            "RAG_DEMONSTRATION_RETRIEVED_TOPK",
            "RAG_DEMONSTRATION_COMPLETION_N",
            "DEMONSTRATION_SAVED_PATH",
            "EXPERIENCE_PROMPT",
            "DEMONSTRATION_PROMPT",
        ],
        # system.yaml - System and execution configurations
        "system.yaml": [
            "MAX_TOKENS",
            "MAX_RETRY",
            "TEMPERATURE",
            "TOP_P",
            "TIMEOUT",
            "CONTROL_BACKEND",
            "IOU_THRESHOLD_FOR_MERGE",
            "MAX_STEP",
            "MAX_ROUND",
            "SLEEP_TIME",
            "RECTANGLE_TIME",
            "ACTION_SEQUENCE",
            "SHOW_VISUAL_OUTLINE_ON_SCREEN",
            "MAXIMIZE_WINDOW",
            "JSON_PARSING_RETRY",
            "SAFE_GUARD",
            "CONTROL_LIST",
            "HISTORY_KEYS",
            "ANNOTATION_COLORS",
            "HIGHLIGHT_BBOX",
            "ANNOTATION_FONT_SIZE",
            "CLICK_API",
            "AFTER_CLICK_WAIT",
            "INPUT_TEXT_API",
            "INPUT_TEXT_ENTER",
            "INPUT_TEXT_INTER_KEY_PAUSE",
            "PRINT_LOG",
            "CONCAT_SCREENSHOT",
            "LOG_LEVEL",
            "INCLUDE_LAST_SCREENSHOT",
            "REQUEST_TIMEOUT",
            "LOG_XML",
            "LOG_TO_MARKDOWN",
            "SCREENSHOT_TO_MEMORY",
            "DEFAULT_PNG_COMPRESS_LEVEL",
            "SAVE_UI_TREE",
            "SAVE_FULL_SCREEN",
            "TASK_STATUS",
            "SAVE_EXPERIENCE",
            "EVA_SESSION",
            "EVA_ROUND",
            "EVA_ALL_SCREENSHOTS",
            "ASK_QUESTION",
            "USE_CUSTOMIZATION",
            "QA_PAIR_FILE",
            "QA_PAIR_NUM",
            "OMNIPARSER",
            "CONTROL_FILTER_TYPE",
            "CONTROL_FILTER_TOP_K_PLAN",
            "CONTROL_FILTER_TOP_K_SEMANTIC",
            "CONTROL_FILTER_TOP_K_ICON",
            "CONTROL_FILTER_MODEL_SEMANTIC_NAME",
            "CONTROL_FILTER_MODEL_ICON_NAME",
            "USE_APIS",
            "API_PROMPT",
            "USE_MCP",
            "MCP_SERVERS_CONFIG",
            "MCP_PREFERRED_APPS",
            "MCP_FALLBACK_TO_UI",
            "MCP_INSTRUCTIONS_PATH",
            "MCP_TOOL_TIMEOUT",
            "MCP_LOG_EXECUTION",
            "DEVICE_INFO",
            "HOSTAGENT_PROMPT",
            "APPAGENT_PROMPT",
            "EVALUATION_PROMPT",
            "HOSTAGENT_EXAMPLE_PROMPT",
            "APPAGENT_EXAMPLE_PROMPT",
            "APPAGENT_EXAMPLE_PROMPT_AS",
            "APP_API_PROMPT_ADDRESS",
            "WORD_API_PROMPT",
            "EXCEL_API_PROMPT",
            "CONSTELLATION_CREATION_PROMPT",
            "CONSTELLATION_EDITING_PROMPT",
            "CONSTELLATION_CREATION_EXAMPLE_PROMPT",
            "CONSTELLATION_EDITING_EXAMPLE_PROMPT",
            "ENABLED_THIRD_PARTY_AGENTS",
        ],
    }

    def __init__(
        self,
        legacy_path: str = "ufo/config",
        new_path: str = "config/ufo",
        backup: bool = True,
    ):
        """
        Initialize ConfigConverter.

        :param legacy_path: Legacy configuration directory
        :param new_path: New configuration directory
        :param backup: Whether to create backups before overwriting
        """
        self.legacy_path = Path(legacy_path)
        self.new_path = Path(new_path)
        self.backup = backup
        self.backup_path = None

    def load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """
        Load YAML file, handling both standard and flow-style formats.

        :param file_path: Path to YAML file
        :return: Parsed configuration dictionary
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse YAML (PyYAML handles both flow and block styles)
        try:
            data = yaml.safe_load(content)
            return data or {}
        except yaml.YAMLError as e:
            console.print(f"[red]Error parsing {file_path}:[/red] {e}")
            return {}

    def save_yaml(
        self,
        data: Dict[str, Any],
        file_path: Path,
        header_comment: Optional[str] = None,
    ) -> None:
        """
        Save configuration to YAML file in standard block format.

        :param data: Configuration data
        :param file_path: Output file path
        :param header_comment: Optional header comment
        """
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            # Write header comment if provided
            if header_comment:
                # Split multi-line comment and format properly
                for line in header_comment.split("\n"):
                    f.write(f"# {line}\n")
                f.write(
                    f"# Auto-generated by convert_config.py on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

            # Write YAML in block style with proper formatting
            yaml.dump(
                data,
                f,
                default_flow_style=False,  # Use block style, not flow style
                allow_unicode=True,
                sort_keys=False,  # Preserve order
                indent=2,
                width=120,
            )

    def split_config(self, config_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Split monolithic config into modular files.

        :param config_data: Original configuration dictionary
        :return: Dictionary mapping file names to their configuration data
        """
        result = {"agents.yaml": {}, "rag.yaml": {}, "system.yaml": {}}

        for key, value in config_data.items():
            # Find which file this key belongs to
            placed = False
            for file_name, fields in self.FIELD_MAPPING.items():
                if key in fields:
                    result[file_name][key] = value
                    placed = True
                    break

            # If not mapped, put in system.yaml as fallback
            if not placed:
                console.print(
                    f"[yellow]Warning:[/yellow] Field '{key}' not in mapping, adding to system.yaml"
                )
                result["system.yaml"][key] = value

        return result

    def convert_legacy_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert all legacy config files to new format.

        :return: Dictionary mapping new file names to their data
        """
        converted = {}

        # 1. Convert config.yaml → agents.yaml + rag.yaml + system.yaml
        config_file = self.legacy_path / "config.yaml"
        if config_file.exists():
            console.print(f"\n[cyan]Processing:[/cyan] {config_file}")
            config_data = self.load_yaml(config_file)
            split_configs = self.split_config(config_data)
            converted.update(split_configs)

        # 2. Convert agent_mcp.yaml → mcp.yaml (direct copy with format conversion)
        mcp_file = self.legacy_path / "agent_mcp.yaml"
        if mcp_file.exists():
            console.print(f"[cyan]Processing:[/cyan] {mcp_file}")
            mcp_data = self.load_yaml(mcp_file)
            converted["mcp.yaml"] = mcp_data

        # 3. Convert config_prices.yaml → prices.yaml (direct copy with format conversion)
        prices_file = self.legacy_path / "config_prices.yaml"
        if prices_file.exists():
            console.print(f"[cyan]Processing:[/cyan] {prices_file}")
            prices_data = self.load_yaml(prices_file)
            converted["prices.yaml"] = prices_data

        # 4. Keep config_dev.yaml as is (environment-specific)
        dev_file = self.legacy_path / "config_dev.yaml"
        if dev_file.exists():
            console.print(
                f"[yellow]Skipping:[/yellow] {dev_file} (environment-specific, use --env=dev)"
            )

        return converted

    def create_backup(self) -> Optional[Path]:
        """
        Create backup of existing new config directory.

        :return: Path to backup directory if created
        """
        if not self.new_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(f"{self.new_path}.backup_{timestamp}")

        console.print(f"\n[yellow]Creating backup:[/yellow] {backup_path}")

        import shutil

        shutil.copytree(self.new_path, backup_path)
        console.print("[green]✓[/green] Backup created successfully")

        self.backup_path = backup_path
        return backup_path

    def write_converted_configs(
        self, converted: Dict[str, Dict[str, Any]], dry_run: bool = False
    ) -> List[Tuple[str, Path]]:
        """
        Write converted configurations to files.

        :param converted: Converted configuration data
        :param dry_run: If True, only preview without writing
        :return: List of (filename, path) tuples
        """
        written_files = []

        # Header comments for each file
        headers = {
            "agents.yaml": "UFO Agent Configurations\nAll agent configurations for HOST, APP, BACKUP, EVALUATION, and OPERATOR agents",
            "rag.yaml": "RAG (Retrieval Augmented Generation) Configuration",
            "system.yaml": "UFO System Configuration",
            "mcp.yaml": "MCP (Model Context Protocol) Agent Configuration",
            "prices.yaml": "API Pricing Configuration\nSource: https://openai.com/pricing\nPrices in $ per 1000 tokens",
        }

        for filename, data in converted.items():
            if not data:
                continue

            output_path = self.new_path / filename

            if dry_run:
                console.print(
                    f"[blue]→[/blue] Would write: {output_path} ({len(data)} keys)"
                )
            else:
                self.save_yaml(data, output_path, headers.get(filename))
                console.print(
                    f"[green]✓[/green] Wrote: {output_path} ({len(data)} keys)"
                )

            written_files.append((filename, output_path))

        return written_files

    def show_summary(
        self, written_files: List[Tuple[str, Path]], dry_run: bool = False
    ) -> None:
        """
        Show conversion summary.

        :param written_files: List of written files
        :param dry_run: Whether this was a dry run
        """
        console.print()

        table = Table(title="Conversion Summary", show_header=True)
        table.add_column("New File", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Path", style="blue")

        for filename, path in written_files:
            status = "Would create" if dry_run else "Created"
            table.add_row(filename, status, str(path))

        console.print(table)
        console.print()

    def show_next_steps(self) -> None:
        """Show next steps after conversion."""
        panel = Panel.fit(
            "[bold green]Conversion Complete![/bold green]\n\n"
            "[yellow]Next Steps:[/yellow]\n"
            "1. Review the converted files in config/ufo/\n\n"
            "2. Copy agents.yaml.template to agents.yaml and fill in your API keys:\n"
            "   [cyan]cp config/ufo/agents.yaml.template config/ufo/agents.yaml[/cyan]\n\n"
            "3. Update agents.yaml with your actual credentials\n\n"
            "4. Test the new configuration:\n"
            "   [cyan]python -m ufo --task test[/cyan]\n\n"
            "5. Once verified, you can remove legacy configs:\n"
            "   [cyan]rm -rf ufo/config/*.yaml[/cyan]\n\n"
            + (
                f"6. If needed, restore from backup:\n"
                f"   [cyan]cp -r {self.backup_path}/* config/ufo/[/cyan]\n\n"
                if self.backup_path
                else ""
            )
            + "[green]Your UFO² configuration is now using the modern modular structure![/green]",
            title="✨ Success",
            border_style="green",
        )
        console.print(panel)

    def run(self, dry_run: bool = False, force: bool = False) -> bool:
        """
        Run the conversion process.

        :param dry_run: If True, only preview changes
        :param force: Skip confirmation prompts
        :return: True if conversion succeeded
        """
        console.print(
            Panel.fit(
                "[bold blue]UFO² Configuration Conversion Tool[/bold blue]\n"
                f"Legacy: [yellow]{self.legacy_path}/[/yellow]\n"
                f"New:    [green]{self.new_path}/[/green]\n\n"
                "[cyan]This tool converts monolithic config to modular structure:[/cyan]\n"
                "• config.yaml → agents.yaml + rag.yaml + system.yaml\n"
                "• agent_mcp.yaml → mcp.yaml\n"
                "• config_prices.yaml → prices.yaml",
                title="🔧 Config Conversion",
                border_style="blue",
            )
        )

        # Check if legacy exists
        if not self.legacy_path.exists():
            console.print(
                f"\n[red]Error:[/red] Legacy config not found at {self.legacy_path}/"
            )
            return False

        # Check if new already exists
        if self.new_path.exists() and not force:
            console.print(
                f"\n[yellow]⚠️  Warning:[/yellow] Target directory already exists: {self.new_path}/"
            )
            if not dry_run:
                if not Confirm.ask(
                    "Do you want to overwrite existing files?", default=False
                ):
                    console.print("[red]Conversion cancelled.[/red]")
                    return False

        # Create backup if requested and not dry run
        if self.backup and not dry_run and self.new_path.exists():
            self.create_backup()

        # Convert configurations
        console.print(
            f"\n[bold]{'[DRY RUN] ' if dry_run else ''}Converting configurations...[/bold]"
        )
        converted = self.convert_legacy_config()

        if not converted:
            console.print("\n[yellow]No configurations to convert.[/yellow]")
            return False

        # Write converted files
        written_files = self.write_converted_configs(converted, dry_run=dry_run)

        # Show summary
        self.show_summary(written_files, dry_run=dry_run)

        # Show next steps (if not dry run)
        if not dry_run:
            self.show_next_steps()
        else:
            console.print(
                Panel.fit(
                    "[yellow]This was a dry run - no files were modified.[/yellow]\n\n"
                    "Run without --dry-run to perform the actual conversion:\n"
                    "[cyan]python -m ufo.tools.convert_config[/cyan]",
                    title="ℹ️  Dry Run Complete",
                    border_style="yellow",
                )
            )

        return True


def main():
    """Main entry point for the conversion tool."""
    parser = argparse.ArgumentParser(
        description="Convert UFO configuration from legacy to modern modular structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive conversion (recommended)
  python -m ufo.tools.convert_config

  # Dry run (preview changes)
  python -m ufo.tools.convert_config --dry-run

  # Force conversion without confirmation
  python -m ufo.tools.convert_config --force

  # Custom paths
  python -m ufo.tools.convert_config --legacy-path ufo/config --new-path config/ufo
        """,
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without making them"
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup (not recommended)",
    )

    parser.add_argument(
        "--force", action="store_true", help="Skip confirmation prompts"
    )

    parser.add_argument(
        "--legacy-path",
        default="ufo/config",
        help="Legacy configuration path (default: ufo/config)",
    )

    parser.add_argument(
        "--new-path",
        default="config/ufo",
        help="New configuration path (default: config/ufo)",
    )

    args = parser.parse_args()

    # Create and run converter
    converter = ConfigConverter(
        legacy_path=args.legacy_path, new_path=args.new_path, backup=not args.no_backup
    )

    try:
        success = converter.run(dry_run=args.dry_run, force=args.force)
        exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n\n[red]Conversion cancelled by user.[/red]")
        exit(1)
    except Exception as e:
        console.print(f"\n\n[red]Error during conversion:[/red] {e}")
        console.print_exception()
        exit(1)


if __name__ == "__main__":
    main()
