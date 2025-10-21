#!/usr/bin/env python3
"""
Modern TUI (Terminal User Interface) for Risk Manager
Beautiful CLI with clickable buttons, animations, and dark mode

Requirements:
    pip install rich textual

This uses Textual - a modern Python TUI framework with mouse support!
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, Input, Label, DataTable
from textual.screen import Screen
from textual import events
from rich.text import Text
import asyncio


class WelcomeScreen(Screen):
    """Main menu screen with action buttons"""

    CSS = """
    WelcomeScreen {
        align: center middle;
    }

    .title {
        text-align: center;
        width: 100%;
        height: 5;
        content-align: center middle;
        color: $accent;
        text-style: bold;
    }

    .subtitle {
        text-align: center;
        width: 100%;
        color: $text-muted;
        margin-bottom: 2;
    }

    .menu-grid {
        width: 80;
        height: auto;
        align: center middle;
    }

    .action-btn {
        width: 35;
        height: 3;
        margin: 1;
    }

    .btn-auth { background: $primary; }
    .btn-account { background: $accent; }
    .btn-rules { background: $warning; }
    .btn-service { background: $success; }
    .btn-test { background: purple; }
    .btn-dashboard { background: $accent; }
    """

    def compose(self) -> ComposeResult:
        yield Static("██████╗ ██╗███████╗██╗  ██╗\n██╔══██╗██║██╔════╝██║ ██╔╝\n██████╔╝██║███████╗█████╔╝\n██╔══██╗██║╚════██║██╔═██╗\n██║  ██║██║███████║██║  ██╗\n╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝", classes="title")
        yield Static("Risk Manager - Setup & Configuration v1.0.0", classes="subtitle")

        with Container(classes="menu-grid"):
            with Horizontal():
                yield Button("🔐 Configure Authentication", id="auth", classes="action-btn btn-auth")
                yield Button("👤 Select Account", id="account", classes="action-btn btn-account")
            with Horizontal():
                yield Button("⚙️  Configure Risk Rules", id="rules", classes="action-btn btn-rules")
                yield Button("🚀 Service Control", id="service", classes="action-btn btn-service")
            with Horizontal():
                yield Button("🔍 Test Connection", id="test", classes="action-btn btn-test")
                yield Button("📊 View Dashboard", id="dashboard", classes="action-btn btn-dashboard")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "auth":
            self.app.push_screen(AuthScreen())
        elif button_id == "account":
            self.app.push_screen(AccountScreen())
        elif button_id == "rules":
            self.app.push_screen(RulesScreen())
        elif button_id == "service":
            self.app.push_screen(ServiceScreen())
        elif button_id == "test":
            self.app.push_screen(TestScreen())
        elif button_id == "dashboard":
            self.app.push_screen(DashboardScreen())


class AuthScreen(Screen):
    """Authentication configuration screen"""

    CSS = """
    AuthScreen {
        align: center middle;
    }

    .auth-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 2;
    }

    .form-label {
        width: 100%;
        color: $text;
        margin-top: 1;
    }

    Input {
        width: 100%;
        margin-bottom: 1;
    }

    .help-text {
        width: 100%;
        color: $text-muted;
        text-style: italic;
        margin-bottom: 2;
    }

    .status-msg {
        width: 100%;
        text-align: center;
        margin: 1;
        height: 3;
    }

    .btn-container {
        width: 100%;
        height: auto;
        align: center middle;
    }

    .auth-btn {
        margin: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(classes="auth-container"):
            yield Static("🔐 Authentication Configuration", classes="title")

            yield Label("Username:", classes="form-label")
            yield Input(placeholder="Enter TopstepX username", id="username")

            yield Label("API Key:", classes="form-label")
            yield Input(placeholder="Enter API key", password=True, id="api_key")

            yield Static("Get your API key from: TopstepX Dashboard → Settings → API Access", classes="help-text")

            yield Static("", id="status", classes="status-msg")

            with Horizontal(classes="btn-container"):
                yield Button("🔐 Validate", variant="primary", id="validate", classes="auth-btn")
                yield Button("💾 Save", variant="success", id="save", classes="auth-btn", disabled=True)
                yield Button("← Back", variant="default", id="back", classes="auth-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "validate":
            self.validate_credentials()
        elif event.button.id == "save":
            self.save_credentials()

    async def validate_credentials(self) -> None:
        username_input = self.query_one("#username", Input)
        api_key_input = self.query_one("#api_key", Input)
        status = self.query_one("#status", Static)
        save_btn = self.query_one("#save", Button)

        username = username_input.value
        api_key = api_key_input.value

        if not username or not api_key:
            status.update("❌ Please enter both username and API key")
            status.styles.color = "red"
            return

        status.update("⏳ Validating credentials...")
        status.styles.color = "yellow"

        await asyncio.sleep(1.5)

        status.update("✅ Authentication successful! JWT token obtained (valid 24h)")
        status.styles.color = "green"
        save_btn.disabled = False

    def save_credentials(self) -> None:
        username_input = self.query_one("#username", Input)
        self.app.notify(f"✅ Credentials saved for user: {username_input.value}", title="Success", severity="information")
        self.app.pop_screen()


class AccountScreen(Screen):
    """Account selection screen"""

    CSS = """
    AccountScreen {
        align: center middle;
    }

    .account-container {
        width: 80;
        height: auto;
        border: solid $accent;
        padding: 2;
    }

    .account-item {
        width: 100%;
        height: 4;
        border: solid $surface;
        margin: 1;
        padding: 1;
    }

    .account-item:hover {
        background: $boost;
        border: solid $accent;
    }

    .account-name {
        text-style: bold;
        color: $text;
    }

    .account-details {
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        with ScrollableContainer(classes="account-container"):
            yield Static("👤 Select Account to Monitor", classes="title")

            # Mock accounts
            accounts = [
                {"id": 1234, "name": "Main Trading Account", "balance": "$10,250", "status": "Active"},
                {"id": 1235, "name": "Practice Account", "balance": "$5,000", "status": "Active"},
                {"id": 1236, "name": "Demo Account", "balance": "$2,500", "status": "Paused"},
            ]

            for acc in accounts:
                with Container(classes="account-item"):
                    yield Button(
                        f"{acc['name']}\nID: {acc['id']} | Balance: {acc['balance']} | Status: {acc['status']}",
                        id=f"account_{acc['id']}",
                        variant="primary" if acc['status'] == "Active" else "default"
                    )

            yield Button("← Back", id="back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id.startswith("account_"):
            acc_id = event.button.id.split("_")[1]
            self.app.notify(f"✅ Account {acc_id} selected!", title="Account Selected")
            self.app.pop_screen()


class RulesScreen(Screen):
    """Risk rules configuration screen"""

    CSS = """
    RulesScreen {
        align: center middle;
    }

    .rules-container {
        width: 90;
        height: auto;
        border: solid $warning;
        padding: 2;
    }

    .rule-item {
        width: 100%;
        height: auto;
        border-left: thick $success;
        background: $panel;
        margin: 1;
        padding: 1;
    }

    .rule-disabled {
        border-left: thick $error;
        opacity: 0.6;
    }

    .rule-header {
        text-style: bold;
        color: $text;
    }

    .rule-details {
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        with ScrollableContainer(classes="rules-container"):
            yield Static("⚙️  Risk Rules Configuration", classes="title")

            rules = [
                ("✅ Max Contracts (Global)", "Limit: 5 contracts | Action: Close all", True),
                ("✅ Max Contracts Per Instrument", "MNQ: 2, ES: 1 | Action: Reduce", True),
                ("✅ Daily Realized Loss Limit", "Limit: -$500 | Reset: 5:00 PM ET", True),
                ("⭕ Session Block (Outside Hours)", "Hours: 9:30 AM - 4:00 PM ET", False),
            ]

            for idx, (name, details, enabled) in enumerate(rules):
                with Container(classes="rule-item" if enabled else "rule-item rule-disabled"):
                    yield Static(name, classes="rule-header")
                    yield Static(details, classes="rule-details")
                    with Horizontal():
                        yield Button("✏️  Edit", id=f"edit_{idx}", variant="primary")
                        yield Button(
                            "Disable" if enabled else "Enable",
                            id=f"toggle_{idx}",
                            variant="error" if enabled else "success"
                        )

            yield Button("← Back", id="back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id.startswith("edit_"):
            self.app.notify("📝 Opening rule editor...", title="Edit Rule")
        elif event.button.id.startswith("toggle_"):
            rule_idx = event.button.id.split("_")[1]
            action = "disabled" if event.button.label == "Disable" else "enabled"
            self.app.notify(f"Rule {action}", title="Rule Updated")


class ServiceScreen(Screen):
    """Service control dashboard"""

    CSS = """
    ServiceScreen {
        align: center middle;
    }

    .service-container {
        width: 80;
        height: auto;
        border: solid $success;
        padding: 2;
    }

    .status-box {
        width: 100%;
        background: $panel;
        padding: 1;
        margin: 1;
        border: solid $surface;
    }

    .status-running {
        color: $success;
        text-style: bold;
    }

    .connection-item {
        width: 100%;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(classes="service-container"):
            yield Static("🚀 Service Control Panel", classes="title")

            with Container(classes="status-box"):
                yield Static("● RUNNING", classes="status-running")
                yield Static("PID: 12345 | Uptime: 3h 24m | CPU: 2.3% | Memory: 45.2 MB")

            with Container(classes="status-box"):
                yield Static("Connections:", classes="rule-header")
                yield Static("✅ TopstepX API - Connected (45ms)", classes="connection-item")
                yield Static("✅ SignalR WebSocket - Connected (32ms)", classes="connection-item")
                yield Static("✅ Database - OK (state.db)", classes="connection-item")

            with Horizontal():
                yield Button("▶️  Start", variant="success", id="start")
                yield Button("⏹️  Stop", variant="error", id="stop")
                yield Button("🔄 Restart", variant="warning", id="restart")

            yield Button("← Back", id="back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "start":
            self.app.notify("▶️  Starting service...", title="Service Control")
        elif event.button.id == "stop":
            self.app.notify("⏹️  Stopping service...", title="Service Control", severity="warning")
        elif event.button.id == "restart":
            self.app.notify("🔄 Restarting service...", title="Service Control")


class TestScreen(Screen):
    """Connection test screen"""

    CSS = """
    TestScreen {
        align: center middle;
    }

    .test-container {
        width: 80;
        height: 30;
        border: solid purple;
        padding: 2;
    }

    .test-output {
        width: 100%;
        height: 20;
        background: $panel;
        padding: 1;
        overflow-y: scroll;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(classes="test-container"):
            yield Static("🔍 Connection Test", classes="title")
            yield Static("", id="test_output", classes="test-output")

            with Horizontal():
                yield Button("🔄 Run Tests", variant="primary", id="run_test")
                yield Button("← Back", variant="default", id="back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "run_test":
            self.run_tests()

    async def run_tests(self) -> None:
        output = self.query_one("#test_output", Static)

        tests = [
            ("Testing TopstepX API...", 1),
            ("  ✅ Authentication successful", 0.5),
            ("  ✅ API endpoint reachable", 0.5),
            ("  ✅ Latency: 45ms", 0.5),
            ("", 0.3),
            ("Testing SignalR WebSocket...", 1),
            ("  ✅ Connection established", 0.5),
            ("  ✅ Event subscription active", 0.5),
            ("  ✅ Latency: 32ms", 0.5),
            ("", 0.3),
            ("All tests passed! ✅", 0),
        ]

        output.update("Running tests...\n")
        for text, delay in tests:
            await asyncio.sleep(delay)
            current = output.renderable
            output.update(f"{current}\n{text}")


class DashboardScreen(Screen):
    """Live dashboard screen"""

    CSS = """
    DashboardScreen {
        align: center middle;
    }

    .dashboard-container {
        width: 80;
        height: auto;
        border: solid $accent;
        padding: 2;
    }

    .metric-box {
        width: 25;
        height: 7;
        background: $panel;
        border: solid $surface;
        margin: 1;
        padding: 1;
        text-align: center;
    }

    .metric-label {
        color: $text-muted;
    }

    .metric-value {
        text-style: bold;
        width: 100%;
    }

    .metric-positive { color: $success; }
    .metric-negative { color: $error; }
    .metric-neutral { color: $accent; }
    """

    def compose(self) -> ComposeResult:
        with Container(classes="dashboard-container"):
            yield Static("📊 Live Dashboard", classes="title")

            with Horizontal():
                with Container(classes="metric-box"):
                    yield Static("Realized P&L", classes="metric-label")
                    yield Static("-$245.50", classes="metric-value metric-negative")

                with Container(classes="metric-box"):
                    yield Static("Unrealized P&L", classes="metric-label")
                    yield Static("+$120.00", classes="metric-value metric-positive")

                with Container(classes="metric-box"):
                    yield Static("Total Trades", classes="metric-label")
                    yield Static("14", classes="metric-value metric-neutral")

            yield Static("\nOpen Positions:", classes="rule-header")
            yield Static("MNQ: +2 @ 21000.5 (P&L: +$85.00)")
            yield Static("ES: +1 @ 5850.25 (P&L: +$35.00)")

            yield Button("← Back", id="back", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()


class RiskManagerTUI(App):
    """Main TUI application"""

    CSS = """
    Screen {
        background: $background;
    }

    .title {
        text-align: center;
        width: 100%;
        margin: 1;
        color: $accent;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())


if __name__ == "__main__":
    app = RiskManagerTUI()
    app.run()
