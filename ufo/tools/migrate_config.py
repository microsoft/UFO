# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Configuration Migration Tool for UFO³

Migrates legacy configuration from ufo/config/ to the new config/ufo/ structure.

Usage:
    # Interactive migration (recommended)
    python -m ufo.tools.migrate_config

    # Dry run (preview changes without making them)
    python -m ufo.tools.migrate_config --dry-run

    # Migration with backup
    python -m ufo.tools.migrate_config --backup

    # Force migration (skip confirmation)
    python -m ufo.tools.migrate_config --force

    # Custom paths
    python -m ufo.tools.migrate_config --legacy-path ufo/config --new-path config/ufo
"""

import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

console = Console()


class ConfigMigrator:
    """
    Configuration migration tool with safety features.

    Features:
    - Dry run mode to preview changes
    - Automatic backup creation
    - Detailed migration report
    - Safety confirmations
    - Rollback support
    """

    def __init__(
        self,
        legacy_path: str = "ufo/config",
        new_path: str = "config/ufo",
        backup: bool = True,
    ):
        """
        Initialize ConfigMigrator.

        :param legacy_path: Legacy configuration path
        :param new_path: New configuration path
        :param backup: Whether to create backups
        """
        self.legacy_path = Path(legacy_path)
        self.new_path = Path(new_path)
        self.backup = backup
        self.backup_path = None

    def check_legacy_exists(self) -> bool:
        """
        Check if legacy configuration exists.

        :return: True if legacy config exists
        """
        return self.legacy_path.exists() and any(self.legacy_path.glob("*.yaml"))

    def check_new_exists(self) -> bool:
        """
        Check if new configuration exists.

        :return: True if new config exists
        """
        return self.new_path.exists() and any(self.new_path.glob("*.yaml"))

    def discover_files(self) -> List[Path]:
        """
        Discover all YAML files in legacy path.

        :return: List of YAML file paths
        """
        if not self.legacy_path.exists():
            return []

        return sorted(self.legacy_path.glob("*.yaml"))

    def create_backup(self) -> Path:
        """
        Create backup of legacy configuration.

        :return: Path to backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(f"{self.legacy_path}.backup_{timestamp}")

        console.print(f"\n[yellow]Creating backup:[/yellow] {backup_path}")
        shutil.copytree(self.legacy_path, backup_path)
        console.print("[green]✓[/green] Backup created successfully")

        self.backup_path = backup_path
        return backup_path

    def migrate_files(self, dry_run: bool = False) -> List[Tuple[Path, Path]]:
        """
        Migrate files from legacy to new path.

        :param dry_run: If True, only preview changes without copying
        :return: List of (source, destination) tuples
        """
        files = self.discover_files()
        migrations = []

        # Create new directory if needed
        if not dry_run:
            self.new_path.mkdir(parents=True, exist_ok=True)

        for file in files:
            dest = self.new_path / file.name
            migrations.append((file, dest))

            if not dry_run:
                shutil.copy2(file, dest)
                console.print(f"[green]✓[/green] Copied: {file.name} → {dest}")
            else:
                console.print(f"[blue]→[/blue] Would copy: {file.name} → {dest}")

        return migrations

    def show_summary(
        self, migrations: List[Tuple[Path, Path]], dry_run: bool = False
    ) -> None:
        """
        Show migration summary.

        :param migrations: List of (source, destination) tuples
        :param dry_run: Whether this was a dry run
        """
        console.print()

        # Create summary table
        table = Table(title="Migration Summary", show_header=True)
        table.add_column("File", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Destination", style="blue")

        for source, dest in migrations:
            status = "Would migrate" if dry_run else "Migrated"
            table.add_row(source.name, status, str(dest))

        console.print(table)
        console.print()

    def show_next_steps(self) -> None:
        """Show next steps after migration."""
        panel = Panel.fit(
            "[bold green]Migration Complete![/bold green]\n\n"
            "[yellow]Next Steps:[/yellow]\n"
            "1. Verify the new configuration files work correctly:\n"
            "   [cyan]python -m ufo --task test[/cyan]\n\n"
            "2. Once verified, you can remove the legacy config:\n"
            "   [cyan]rm -rf ufo/config/*.yaml[/cyan]\n\n"
            + (
                f"3. If needed, rollback using backup:\n"
                f"   [cyan]cp -r {self.backup_path}/* ufo/config/[/cyan]\n\n"
                if self.backup_path
                else ""
            )
            + "[green]Your UFO³ configuration is now using the modern structure![/green]",
            title="✨ Success",
            border_style="green",
        )
        console.print(panel)

    def run(self, dry_run: bool = False, force: bool = False) -> bool:
        """
        Run the migration process.

        :param dry_run: If True, only preview changes
        :param force: Skip confirmation prompts
        :return: True if migration succeeded
        """
        console.print(
            Panel.fit(
                "[bold blue]UFO³ Configuration Migration Tool[/bold blue]\n"
                f"Legacy: [yellow]{self.legacy_path}/[/yellow]\n"
                f"New:    [green]{self.new_path}/[/green]",
                title="🔧 Config Migration",
                border_style="blue",
            )
        )

        # Check if legacy exists
        if not self.check_legacy_exists():
            console.print(
                f"\n[yellow]⚠️  No legacy configuration found at:[/yellow] {self.legacy_path}/"
            )
            console.print(
                "[green]✓[/green] You're already using the modern config structure!"
            )
            return True

        # Check if new already exists
        if self.check_new_exists() and not force:
            console.print(
                f"\n[yellow]⚠️  Warning:[/yellow] New configuration already exists at {self.new_path}/"
            )
            if not Confirm.ask(
                "Do you want to overwrite existing files?", default=False
            ):
                console.print("[red]Migration cancelled.[/red]")
                return False

        # Discover files
        files = self.discover_files()
        if not files:
            console.print(
                f"\n[yellow]⚠️  No YAML files found in:[/yellow] {self.legacy_path}/"
            )
            return False

        console.print(f"\n[cyan]Found {len(files)} configuration file(s):[/cyan]")
        for file in files:
            console.print(f"  • {file.name}")

        # Confirm migration
        if not dry_run and not force:
            console.print()
            if not Confirm.ask(
                f"Migrate these files to {self.new_path}?", default=True
            ):
                console.print("[red]Migration cancelled.[/red]")
                return False

        # Create backup if requested
        if self.backup and not dry_run:
            self.create_backup()

        # Perform migration
        console.print(
            f"\n[bold]{'[DRY RUN] ' if dry_run else ''}Migrating files...[/bold]"
        )
        migrations = self.migrate_files(dry_run=dry_run)

        # Show summary
        self.show_summary(migrations, dry_run=dry_run)

        # Show next steps (if not dry run)
        if not dry_run:
            self.show_next_steps()
        else:
            console.print(
                Panel.fit(
                    "[yellow]This was a dry run - no files were modified.[/yellow]\n\n"
                    "Run without --dry-run to perform the actual migration:\n"
                    "[cyan]python -m ufo.tools.migrate_config[/cyan]",
                    title="ℹ️  Dry Run Complete",
                    border_style="yellow",
                )
            )

        return True


def main():
    """Main entry point for the migration tool."""
    parser = argparse.ArgumentParser(
        description="Migrate UFO configuration from legacy to modern structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive migration (recommended)
  python -m ufo.tools.migrate_config

  # Dry run (preview changes)
  python -m ufo.tools.migrate_config --dry-run

  # Force migration without confirmation
  python -m ufo.tools.migrate_config --force

  # Custom paths
  python -m ufo.tools.migrate_config --legacy-path ufo/config --new-path config/ufo
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without making them",
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

    # Create and run migrator
    migrator = ConfigMigrator(
        legacy_path=args.legacy_path,
        new_path=args.new_path,
        backup=not args.no_backup,
    )

    try:
        success = migrator.run(dry_run=args.dry_run, force=args.force)
        exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n\n[red]Migration cancelled by user.[/red]")
        exit(1)
    except Exception as e:
        console.print(f"\n\n[red]Error during migration:[/red] {e}")
        console.print_exception()
        exit(1)


if __name__ == "__main__":
    main()
