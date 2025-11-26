# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Configuration Doctor - Health Check and Setup Assistant for UFO³

A diagnostic tool that helps users identify and fix common configuration issues.

Usage:
    python -m ufo.tools.config_doctor
    python -m ufo.tools.config_doctor --setup
    python -m ufo.tools.config_doctor --fix
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import re

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich import box

console = Console()


class ConfigIssue:
    """Represents a configuration issue with severity and fix suggestions."""
   
    SEVERITY_CRITICAL = "critical"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"
   
    def __init__(self, title: str, description: str, severity: str = SEVERITY_WARNING,
                 fix_suggestion: Optional[str] = None, auto_fix: Optional[callable] = None):
        self.title = title
        self.description = description
        self.severity = severity
        self.fix_suggestion = fix_suggestion
        self.auto_fix = auto_fix
   
    @property
    def severity_icon(self) -> str:
        return {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(self.severity, "❓")
   
    @property
    def severity_color(self) -> str:
        return {"critical": "red", "warning": "yellow", "info": "blue"}.get(self.severity, "white")


class ConfigDoctor:
    """Configuration health check and diagnostic tool."""
   
    def __init__(self):
        self.issues: List[ConfigIssue] = []
       
    def run_health_check(self, module: Optional[str] = None) -> bool:
        """Run comprehensive health check."""
        console.print("🩺 [bold blue]UFO³ Configuration Doctor[/bold blue]")
        console.print("Running health check...\n")
       
        self._check_config_structure(module)
        self._check_required_files(module)
        self._check_api_configuration(module)
       
        self._show_health_report()
        return not any(issue.severity == ConfigIssue.SEVERITY_CRITICAL for issue in self.issues)
   
    def _check_config_structure(self, module: Optional[str] = None):
        """Check configuration directory structure."""
        modules_to_check = [module] if module else ["ufo", "galaxy"]
       
        for mod in modules_to_check:
            if mod == "ufo":
                new_path = Path("config/ufo")
                legacy_path = Path("ufo/config")
               
                new_exists = new_path.exists() and any(new_path.glob("*.yaml"))
                legacy_exists = legacy_path.exists() and any(legacy_path.glob("*.yaml"))
               
                if not new_exists and not legacy_exists:
                    self.issues.append(ConfigIssue(
                        title="Missing UFO Configuration",
                        description=f"No UFO configuration found",
                        severity=ConfigIssue.SEVERITY_CRITICAL,
                        fix_suggestion="Run setup: python -m ufo.tools.config_doctor --setup"
                    ))
                elif legacy_exists and not new_exists:
                    self.issues.append(ConfigIssue(
                        title="Legacy Configuration Structure",
                        description=f"Using legacy config path: {legacy_path}/",
                        severity=ConfigIssue.SEVERITY_WARNING,
                        fix_suggestion="Migrate: python -m ufo.tools.migrate_config"
                    ))
   
    def _check_required_files(self, module: Optional[str] = None):
        """Check for required configuration files."""
        if not module or module == "ufo":
            config_path = Path("config/ufo")
            if not config_path.exists():
                config_path = Path("ufo/config")
           
            agents_file = config_path / "agents.yaml"
            template_file = config_path / "agents.yaml.template"
           
            if not agents_file.exists() and template_file.exists():
                self.issues.append(ConfigIssue(
                    title="Missing UFO Configuration File",
                    description="agents.yaml not found",
                    severity=ConfigIssue.SEVERITY_CRITICAL,
                    fix_suggestion=f"Copy template: cp {template_file} {agents_file}",
                    auto_fix=lambda tf=template_file, af=agents_file: self._copy_template(tf, af)
                ))
   
    def _check_api_configuration(self, module: Optional[str] = None):
        """Check API configuration for common issues."""
        try:
            # Try to import from the config module
            try:
                from config.config_loader import get_ufo_config
            except ImportError:
                # Fallback for different project structures
                sys.path.insert(0, str(Path(__file__).parent.parent.parent))
                from config.config_loader import get_ufo_config
           
            if not module or module == "ufo":
                config = get_ufo_config()
               
                for agent_name in ["HOST_AGENT", "APP_AGENT"]:
                    if agent_name not in config:
                        continue
                       
                    agent_config = config[agent_name]
                   
                    # Check for placeholder API keys
                    api_key = agent_config.get("API_KEY", "")
                    if api_key in ["YOUR_KEY", "sk-YOUR_KEY_HERE", ""]:
                        self.issues.append(ConfigIssue(
                            title=f"Placeholder API Key in {agent_name}",
                            description=f"API_KEY contains placeholder: '{api_key}'",
                            severity=ConfigIssue.SEVERITY_CRITICAL,
                            fix_suggestion="Replace with actual API key"
                        ))
                   
                    # Check required fields
                    for field in ["API_TYPE", "API_MODEL"]:
                        if not agent_config.get(field):
                            self.issues.append(ConfigIssue(
                                title=f"Missing {agent_name} Configuration",
                                description=f"Required field {field} is missing",
                                severity=ConfigIssue.SEVERITY_CRITICAL,
                                fix_suggestion=f"Add {field} to configuration"
                            ))
                           
        except Exception:
            self.issues.append(ConfigIssue(
                title="Failed to Load Configuration",
                description="Cannot load UFO configuration",
                severity=ConfigIssue.SEVERITY_CRITICAL,
                fix_suggestion="Check configuration file format"
            ))
   
    def _copy_template(self, template_path: Path, target_path: Path) -> bool:
        """Copy template file to target location."""
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(template_path.read_text(encoding="utf-8"), encoding="utf-8")
            return True
        except (FileNotFoundError, PermissionError, OSError) as e:
            console.print(f"[red]Error copying template: {e}[/red]")
            return False
   
    def _show_health_report(self):
        """Display health report."""
        console.print("\n" + "="*50)
        console.print("🏥 [bold blue]Health Report[/bold blue]")
        console.print("="*50)
       
        if not self.issues:
            console.print(Panel.fit(
                "[bold green]✅ No issues found![/bold green]\n"
                "Your configuration is healthy.",
                border_style="green"
            ))
            return
       
        # Count by severity
        critical = sum(1 for i in self.issues if i.severity == ConfigIssue.SEVERITY_CRITICAL)
        warning = sum(1 for i in self.issues if i.severity == ConfigIssue.SEVERITY_WARNING)
        info = sum(1 for i in self.issues if i.severity == ConfigIssue.SEVERITY_INFO)
       
        console.print(f"Found: 🚨 {critical} Critical, ⚠️ {warning} Warnings, ℹ️ {info} Info\n")
       
        # Show issues
        table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        table.add_column("", width=3)
        table.add_column("Issue", width=30)
        table.add_column("Fix", width=40)
       
        for issue in self.issues:
            table.add_row(
                issue.severity_icon,
                f"[{issue.severity_color}]{issue.title}[/{issue.severity_color}]",
                issue.fix_suggestion or "Manual fix required"
            )
       
        console.print(table)
       
        if critical > 0:
            console.print("\n🔧 [red]Fix critical issues first![/red]")
            console.print("Run: python -m ufo.tools.config_doctor --fix")
   
    def auto_fix_issues(self) -> int:
        """Automatically fix issues that have auto-fix functions."""
        fixable = [i for i in self.issues if i.auto_fix]
       
        if not fixable:
            console.print("ℹ️ No auto-fixable issues found.")
            return 0
       
        console.print(f"🔧 Found {len(fixable)} auto-fixable issues")
        if not Confirm.ask("Proceed with fixes?"):
            return 0
       
        fixed = 0
        for issue in fixable:
            try:
                if issue.auto_fix():
                    console.print(f"✅ Fixed: {issue.title}")
                    fixed += 1
                else:
                    console.print(f"❌ Failed: {issue.title}")
            except Exception as e:
                console.print(f"❌ Error fixing {issue.title}: {e}")
       
        console.print(f"\n✅ Fixed {fixed}/{len(fixable)} issues")
        return fixed
   
    def run_setup_assistant(self):
        """Interactive setup assistant."""
        console.print("🚀 [bold blue]UFO³ Setup Assistant[/bold blue]")
       
        config_dir = Path("config/ufo")
        config_dir.mkdir(parents=True, exist_ok=True)
       
        agents_file = config_dir / "agents.yaml"
        template_file = config_dir / "agents.yaml.template"
       
        # Copy template
        if not agents_file.exists() and template_file.exists():
            console.print(f"📄 Copying template to {agents_file}")
            agents_file.write_text(template_file.read_text(encoding="utf-8"), encoding="utf-8")
       
        # Get API configuration
        console.print("\n🔑 API Configuration")
        api_type = Prompt.ask("API provider", choices=["openai", "aoai"], default="openai")
       
        if api_type == "openai":
            api_key = Prompt.ask("OpenAI API key (starts with sk-)")
            api_model = Prompt.ask("Model name", default="gpt-4o")
           
            self._update_config(agents_file, {
                "HOST_AGENT": {"API_TYPE": "openai", "API_KEY": api_key, "API_MODEL": api_model},
                "APP_AGENT": {"API_TYPE": "openai", "API_KEY": api_key, "API_MODEL": api_model}
            })
       
        console.print(f"✅ Configuration saved to {agents_file}")
        console.print("Run health check: python -m ufo.tools.config_doctor")
   
    def _update_config(self, file_path: Path, updates: Dict[str, Any]):
        """Update YAML configuration file."""
        try:
            config = {}
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
           
            for key, value in updates.items():
                if key in config and isinstance(config[key], dict):
                    config[key].update(value)
                else:
                    config[key] = value
           
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
               
        except (yaml.YAMLError, FileNotFoundError, PermissionError) as e:
            console.print(f"[red]Error updating config: {e}[/red]")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="UFO³ Configuration Doctor")
    parser.add_argument("--setup", action="store_true", help="Run setup assistant")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument("--module", choices=["ufo", "galaxy"], help="Check specific module")
   
    args = parser.parse_args()
    doctor = ConfigDoctor()
   
    if args.setup:
        doctor.run_setup_assistant()
    else:
        success = doctor.run_health_check(args.module)
        if args.fix and doctor.issues:
            doctor.auto_fix_issues()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
