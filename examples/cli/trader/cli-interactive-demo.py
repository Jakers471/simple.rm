#!/usr/bin/env python3
"""
Interactive CLI Demo for Risk Manager Setup

This script simulates the CLI interface without requiring backend connections.
Perfect for testing UI/UX and demonstrating the setup flow.

Usage:
    python cli-interactive-demo.py
"""

import time
import sys
from typing import Optional

# Try to import rich for beautiful output, fallback to basic if not available
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better visuals: pip install rich")


class CLIDemo:
    """Simulated CLI interface for Risk Manager setup"""

    def __init__(self):
        if RICH_AVAILABLE:
            self.console = Console()
        self.username = ""
        self.api_key = ""
        self.account_id = None
        self.account_name = ""

    def clear_screen(self):
        """Clear the terminal screen"""
        if RICH_AVAILABLE:
            self.console.clear()
        else:
            print("\n" * 50)

    def show_box(self, title: str, content: str, style: str = "white"):
        """Display content in a box"""
        if RICH_AVAILABLE:
            self.console.print(Panel(content, title=title, border_style=style))
        else:
            border = "=" * 60
            print(f"\n{border}")
            print(f"{title:^60}")
            print(border)
            print(content)
            print(border)

    def show_welcome(self):
        """Display welcome screen"""
        self.clear_screen()

        welcome_text = """
        ██████╗ ██╗███████╗██╗  ██╗
        ██╔══██╗██║██╔════╝██║ ██╔╝
        ██████╔╝██║███████╗█████╔╝
        ██╔══██╗██║╚════██║██╔═██╗
        ██║  ██║██║███████║██║  ██╗
        ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝

        MANAGER - Setup Wizard v1.0.0

        This wizard will guide you through:
          • TopstepX API authentication
          • Trading account selection
          • Risk rule configuration
          • Service installation & testing

        Estimated time: 5-10 minutes
        """

        self.show_box("RISK MANAGER - SETUP WIZARD", welcome_text, "cyan")

        if RICH_AVAILABLE:
            Prompt.ask("\nPress ENTER to begin setup", default="")
        else:
            input("\nPress ENTER to begin setup: ")

    def configure_authentication(self):
        """Step 1: Configure authentication"""
        self.clear_screen()

        auth_text = """
        Enter your TopstepX credentials

        Get your API key from:
        TopstepX Dashboard → Settings → API Access → Generate Key
        """

        self.show_box("SETUP WIZARD - Step 1 of 4: Authentication", auth_text)

        if RICH_AVAILABLE:
            self.username = Prompt.ask("\nUsername")
            self.api_key = Prompt.ask("API Key", password=True)
        else:
            self.username = input("\nUsername: ")
            self.api_key = input("API Key (hidden): ")

        # Simulate validation
        print("\nValidating credentials...")
        time.sleep(1)

        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Connecting to TopstepX API...", total=None)
                time.sleep(2)
                progress.update(task, description="✓ Connected to TopstepX API")
                time.sleep(0.5)
        else:
            print("  Connecting to TopstepX API...")
            time.sleep(1)
            print("  ✓ Connected to TopstepX API")

        success_text = """
        ✓ Authentication successful
        ✓ JWT token obtained
        ✓ Token valid for 24 hours

        Credentials saved to: config/accounts.yaml
        """

        self.show_box("Success!", success_text, "green")

        if RICH_AVAILABLE:
            Prompt.ask("\nPress ENTER to continue to Step 2", default="")
        else:
            input("\nPress ENTER to continue to Step 2: ")

    def select_account(self):
        """Step 2: Account selection"""
        self.clear_screen()

        self.show_box("SETUP WIZARD - Step 2 of 4: Account Selection",
                     "Fetching your TopstepX accounts...")

        time.sleep(1)

        # Simulate account list
        accounts = [
            {"id": 1234, "name": "Main Trading Account", "balance": "$10,250", "status": "Active"},
            {"id": 1235, "name": "Practice Account", "balance": "$5,000", "status": "Active"},
            {"id": 1236, "name": "Demo Account", "balance": "$2,500", "status": "Paused"},
        ]

        if RICH_AVAILABLE:
            table = Table(title="Available Accounts", show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim")
            table.add_column("Account Name")
            table.add_column("Balance", justify="right")
            table.add_column("Status")

            for i, acc in enumerate(accounts, 1):
                status_style = "green" if acc["status"] == "Active" else "yellow"
                table.add_row(
                    str(i),
                    acc["name"],
                    acc["balance"],
                    f"[{status_style}]{acc['status']}[/{status_style}]"
                )

            self.console.print(table)
            choice = Prompt.ask("\nSelect account to monitor [1-3]", choices=["1", "2", "3"], default="1")
        else:
            print("\nAvailable Accounts:")
            print(f"{'#':<5} {'Account Name':<25} {'Balance':<12} {'Status'}")
            print("-" * 60)
            for i, acc in enumerate(accounts, 1):
                print(f"{i:<5} {acc['name']:<25} {acc['balance']:<12} {acc['status']}")

            choice = input("\nSelect account to monitor [1-3]: ") or "1"

        selected = accounts[int(choice) - 1]
        self.account_id = selected["id"]
        self.account_name = selected["name"]

        confirm_text = f"""
        Selected: {selected['name']} (ID: {selected['id']})

        This account will be monitored for risk violations.
        You can change this later in the admin panel.
        """

        self.show_box("Confirm Selection", confirm_text)

        if RICH_AVAILABLE:
            confirmed = Confirm.ask("Confirm selection?", default=True)
        else:
            confirmed = input("Confirm selection? [Y/n]: ").lower() != 'n'

        if confirmed:
            print("\n✓ Account configuration saved")
            time.sleep(1)

    def configure_rules(self):
        """Step 3: Configure risk rules"""
        self.clear_screen()

        rules_text = """
        Choose configuration mode:

        1. Quick Setup (Recommended defaults)
           • Max 5 contracts globally
           • $500 daily loss limit
           • Basic session controls

        2. Custom Setup (Configure each rule)
           • Full control over all 12 rules
           • Set specific limits and actions

        3. Import Configuration (Load from file)
           • Use existing risk_config.yaml
        """

        self.show_box("SETUP WIZARD - Step 3 of 4: Risk Rules", rules_text)

        if RICH_AVAILABLE:
            choice = Prompt.ask("Enter choice [1-3]", choices=["1", "2", "3"], default="1")
        else:
            choice = input("\nEnter choice [1-3]: ") or "1"

        if choice == "1":
            self._quick_setup()
        elif choice == "2":
            self._custom_setup()
        else:
            self._import_config()

    def _quick_setup(self):
        """Quick setup with defaults"""
        print("\nApplying recommended defaults...")
        time.sleep(1)

        defaults = [
            "Max Contracts: 5",
            "Max Contracts Per Instrument: MNQ=2, ES=1, NQ=1",
            "Daily Realized Loss: -$500",
            "Daily Unrealized Loss: -$750",
            "Trade Frequency: 3/min, 10/hour, 50/session",
            "Session Block: Enabled (9:30 AM - 4:00 PM ET)",
        ]

        if RICH_AVAILABLE:
            with Progress(console=self.console) as progress:
                task = progress.add_task("[cyan]Configuring rules...", total=len(defaults))
                for rule in defaults:
                    time.sleep(0.3)
                    progress.console.print(f"  ✓ {rule}")
                    progress.advance(task)
        else:
            for rule in defaults:
                print(f"  ✓ {rule}")
                time.sleep(0.3)

        print("\n✓ Quick setup complete - 8 rules enabled")
        time.sleep(1)

    def _custom_setup(self):
        """Custom rule configuration"""
        print("\nShowing Position Limits rules...")
        time.sleep(1)

        custom_text = """
        ┌─ Max Contracts (Global) ─────────────────────┐
        │                                               │
        │  Status:        [✓] Enabled                   │
        │  Limit:         5 contracts                   │
        │  Count Type:    Net position                  │
        │  Action:        Close all positions           │
        │                                               │
        │  Press E to edit, D to disable                │
        └───────────────────────────────────────────────┘

        Press 'n' for next category, 'b' for back
        """

        self.show_box("Risk Rules - Position Limits", custom_text)

        if RICH_AVAILABLE:
            action = Prompt.ask("Action", choices=["n", "b", "e", "d"], default="n")
        else:
            action = input("\nAction [n/b/e/d]: ") or "n"

        if action == "e":
            self._edit_rule()
        else:
            print("\n✓ Configuration saved")
            time.sleep(1)

    def _edit_rule(self):
        """Edit a specific rule"""
        edit_text = """
        Enable this rule? [Y/n]: Y

        Maximum contracts allowed:
        Current: 5
        """

        self.show_box("Edit Rule - Max Contracts", edit_text)

        if RICH_AVAILABLE:
            new_limit = Prompt.ask("New limit", default="5")
        else:
            new_limit = input("\nNew limit: ") or "5"

        print(f"\n✓ Limit updated to {new_limit}")
        time.sleep(1)

    def _import_config(self):
        """Import existing configuration"""
        print("\nLooking for config/risk_config.yaml...")
        time.sleep(1)
        print("✓ Configuration file found")
        time.sleep(0.5)
        print("✓ Loaded 8 enabled rules")
        time.sleep(1)

    def install_service(self):
        """Step 4: Install and test service"""
        self.clear_screen()

        self.show_box("SETUP WIZARD - Step 4 of 4: Service Installation",
                     "Installing Windows Service...")

        steps = [
            ("Creating service: RiskManagerService", 1),
            ("Setting startup type: Automatic", 0.5),
            ("Configuring service account", 0.5),
            ("Starting service", 1),
        ]

        if RICH_AVAILABLE:
            with Progress(console=self.console) as progress:
                task = progress.add_task("[cyan]Installing...", total=len(steps))
                for step, delay in steps:
                    time.sleep(delay)
                    progress.console.print(f"  ✓ {step}")
                    progress.advance(task)
        else:
            for step, delay in steps:
                time.sleep(delay)
                print(f"  ✓ {step}")

        print("\nService started successfully!")
        print("\nRunning connection tests...")
        time.sleep(1)

        tests = [
            ("TopstepX API: Connected (45ms)", "green"),
            ("SignalR WebSocket: Connected (32ms)", "green"),
            ("Database: Initialized", "green"),
            ("Account access: Verified", "green"),
            ("Event subscription: Active", "green"),
        ]

        for test, color in tests:
            time.sleep(0.5)
            if RICH_AVAILABLE:
                self.console.print(f"  ✓ {test}", style=color)
            else:
                print(f"  ✓ {test}")

        print("\nAll tests passed! ✓")
        time.sleep(1)

    def show_completion(self):
        """Show setup completion screen"""
        self.clear_screen()

        completion_text = f"""
        Setup complete! Risk Manager is now running.

        Configuration Summary:
        ──────────────────────
        Username:       {self.username}
        Account:        {self.account_name} ({self.account_id})
        Rules Enabled:  8 of 12
        Service Status: RUNNING

        Next Steps:
        ──────────────────────
        To view live status, run:
          python -m src.cli.trader.main

        To reconfigure, run:
          python -m src.cli.admin.main

        Documentation:
          docs/ARCHITECTURE_INDEX.md
        """

        self.show_box("🎉 Setup Complete!", completion_text, "green")

        if RICH_AVAILABLE:
            Prompt.ask("\nPress ENTER to exit", default="")
        else:
            input("\nPress ENTER to exit: ")

    def run(self):
        """Run the complete setup wizard"""
        try:
            self.show_welcome()
            self.configure_authentication()
            self.select_account()
            self.configure_rules()
            self.install_service()
            self.show_completion()
        except KeyboardInterrupt:
            print("\n\nSetup cancelled by user")
            sys.exit(0)


def show_main_menu():
    """Demonstrate the main admin menu"""
    print("\n" + "=" * 60)
    print(" " * 15 + "MAIN ADMIN MENU DEMO")
    print("=" * 60)

    menu_text = """
╔════════════════════════════════════════════════════════╗
║          RISK MANAGER - ADMIN CONTROL PANEL           ║
║                      v1.0.0                            ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  SETUP & CONFIGURATION                                ║
║  ─────────────────────                                ║
║  1. Initial Setup Wizard                              ║
║  2. Configure Authentication                          ║
║  3. Select Monitored Account                          ║
║  4. Configure Risk Rules                              ║
║                                                        ║
║  SERVICE MANAGEMENT                                   ║
║  ─────────────────────                                ║
║  5. Service Control (Start/Stop/Restart)              ║
║  6. Test Connection                                   ║
║  7. View Logs                                         ║
║                                                        ║
║  SYSTEM                                               ║
║  ─────────────────────                                ║
║  8. Change Admin Password                             ║
║  9. Exit                                              ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Service Status: ● RUNNING  | Uptime: 3h 24m          ║
║  Account: Main Trading (1234) | Rules: 8 enabled      ║
╠════════════════════════════════════════════════════════╣
║  Enter choice [1-9]: _                                ║
╚════════════════════════════════════════════════════════╝
    """

    print(menu_text)


def show_service_control():
    """Demonstrate service control panel"""
    print("\n" + "=" * 60)
    print(" " * 15 + "SERVICE CONTROL DEMO")
    print("=" * 60)

    service_text = """
╔════════════════════════════════════════════════════════╗
║              SERVICE CONTROL PANEL                     ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  SERVICE STATUS                                       ║
║  ──────────────                                       ║
║  State:         ● RUNNING                             ║
║  PID:           12345                                 ║
║  Uptime:        3h 24m 15s                            ║
║  Started:       2025-01-20 14:30:00                   ║
║  CPU Usage:     2.3%                                  ║
║  Memory:        45.2 MB                               ║
║                                                        ║
║  CONNECTION STATUS                                    ║
║  ──────────────                                       ║
║  TopstepX API:      ✓ Connected (latency: 45ms)      ║
║  SignalR Stream:    ✓ Connected (latency: 32ms)      ║
║  Database:          ✓ OK (state.db)                   ║
║  Account Access:    ✓ Verified (account 1234)        ║
║                                                        ║
║  MONITORING STATUS                                    ║
║  ──────────────                                       ║
║  Account:           Main Trading (1234)               ║
║  Enabled Rules:     8 of 12                           ║
║  Active Lockouts:   0                                 ║
║  Events Today:      142 processed                     ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  1. Start Service                                     ║
║  2. Stop Service                                      ║
║  3. Restart Service                                   ║
║  4. View Live Logs (tail -f)                          ║
║  5. Test Connection                                   ║
║  6. Back to Main Menu                                 ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Enter choice [1-6]: _                                ║
╚════════════════════════════════════════════════════════╝
    """

    print(service_text)


def main():
    """Main entry point for demo"""
    print("\n" + "=" * 60)
    print(" " * 10 + "RISK MANAGER CLI - INTERACTIVE DEMO")
    print("=" * 60)
    print("\nThis demo simulates the CLI interface without backend.")
    print("\nChoose demo mode:")
    print("  1. Full Setup Wizard (recommended)")
    print("  2. Show Main Menu")
    print("  3. Show Service Control Panel")
    print("  4. Exit")

    choice = input("\nEnter choice [1-4]: ") or "1"

    if choice == "1":
        demo = CLIDemo()
        demo.run()
    elif choice == "2":
        show_main_menu()
    elif choice == "3":
        show_service_control()
    else:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
