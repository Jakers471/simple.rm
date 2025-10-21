#!/usr/bin/env python3
"""
Beautiful CLI with Clickable Menu (NO DEPENDENCIES NEEDED!)
Works perfectly in WSL with just Python 3

Features:
- Centered, colorful menus
- Number-based selection (type 1, 2, 3, etc.)
- Beautiful borders and animations
- Dark mode color scheme
- NO pip install required!
"""

import os
import sys
import time
from typing import Optional


# ============================================================================
# COLOR CODES - ANSI escape sequences for terminal colors
# ============================================================================

class Colors:
    """Dark mode color palette using ANSI codes"""
    # Reset
    RESET = '\033[0m'

    # Text colors
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BRIGHT_WHITE = '\033[1;97m'

    # Semantic colors
    BLUE = '\033[94m'           # Authentication
    CYAN = '\033[96m'           # Account selection
    YELLOW = '\033[93m'         # Rules/warnings
    GREEN = '\033[92m'          # Service/success
    MAGENTA = '\033[95m'        # Testing
    RED = '\033[91m'            # Danger/errors

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')


def get_terminal_width():
    """Get terminal width for centering"""
    try:
        columns = os.get_terminal_size().columns
        return columns
    except:
        return 80


def center_text(text: str, width: Optional[int] = None) -> str:
    """Center text in terminal"""
    if width is None:
        width = get_terminal_width()
    lines = text.split('\n')
    centered = []
    for line in lines:
        # Remove ANSI codes for length calculation
        clean_line = line
        for code in [Colors.RESET, Colors.WHITE, Colors.GRAY, Colors.BRIGHT_WHITE,
                     Colors.BLUE, Colors.CYAN, Colors.YELLOW, Colors.GREEN,
                     Colors.MAGENTA, Colors.RED, Colors.BOLD, Colors.DIM]:
            clean_line = clean_line.replace(code, '')

        padding = (width - len(clean_line)) // 2
        centered.append(' ' * padding + line)
    return '\n'.join(centered)


def print_centered(text: str):
    """Print centered text"""
    print(center_text(text))


def print_box(title: str, content: str, color: str = Colors.CYAN, width: int = 60):
    """Print a beautiful box with content"""
    box_width = width

    # Top border
    top = f"{color}╔{'═' * (box_width - 2)}╗{Colors.RESET}"

    # Title
    title_line = f"{color}║{Colors.RESET} {Colors.BOLD}{title}{Colors.RESET}"
    padding = box_width - len(title) - 4
    title_line += ' ' * padding + f"{color}║{Colors.RESET}"

    # Separator
    separator = f"{color}╠{'═' * (box_width - 2)}╣{Colors.RESET}"

    # Content lines
    content_lines = []
    for line in content.split('\n'):
        clean_line = line
        for code in [Colors.RESET, Colors.WHITE, Colors.GRAY, Colors.BRIGHT_WHITE,
                     Colors.BLUE, Colors.CYAN, Colors.YELLOW, Colors.GREEN,
                     Colors.MAGENTA, Colors.RED, Colors.BOLD, Colors.DIM]:
            clean_line = clean_line.replace(code, '')

        line_padding = box_width - len(clean_line) - 4
        content_line = f"{color}║{Colors.RESET} {line}" + ' ' * line_padding + f"{color}║{Colors.RESET}"
        content_lines.append(content_line)

    # Bottom border
    bottom = f"{color}╚{'═' * (box_width - 2)}╝{Colors.RESET}"

    # Print centered box
    print_centered(top)
    print_centered(title_line)
    print_centered(separator)
    for line in content_lines:
        print_centered(line)
    print_centered(bottom)


def animate_loading(message: str, duration: float = 1.5):
    """Show loading animation"""
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    end_time = time.time() + duration

    while time.time() < end_time:
        for frame in frames:
            if time.time() >= end_time:
                break
            print_centered(f"{Colors.YELLOW}{frame} {message}{Colors.RESET}")
            time.sleep(0.1)
            print('\033[A\033[K', end='')  # Move up and clear line

    print_centered(f"{Colors.GREEN}✓ {message} - Complete!{Colors.RESET}")


def show_success(message: str):
    """Show success message"""
    print_centered(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def show_error(message: str):
    """Show error message"""
    print_centered(f"{Colors.RED}✗ {message}{Colors.RESET}")


def show_info(message: str):
    """Show info message"""
    print_centered(f"{Colors.CYAN}ℹ {message}{Colors.RESET}")


def get_input(prompt: str) -> str:
    """Get user input with colored prompt"""
    width = get_terminal_width()
    padding = (width - len(prompt) - 3) // 2
    print(' ' * padding + f"{Colors.CYAN}{prompt}{Colors.RESET} ", end='')
    return input()


def pause():
    """Wait for user to press enter"""
    get_input("Press ENTER to continue...")


# ============================================================================
# SCREENS
# ============================================================================

def show_header():
    """Show main header"""
    logo = f"""{Colors.BOLD}{Colors.CYAN}
██████╗ ██╗███████╗██╗  ██╗
██╔══██╗██║██╔════╝██║ ██╔╝
██████╔╝██║███████╗█████╔╝
██╔══██╗██║╚════██║██╔═██╗
██║  ██║██║███████║██║  ██╗
╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝
{Colors.RESET}"""

    subtitle = f"{Colors.DIM}Risk Manager - Setup & Configuration v1.0.0{Colors.RESET}"

    print_centered(logo)
    print()
    print_centered(subtitle)
    print()


def show_main_menu():
    """Main menu screen"""
    clear_screen()
    show_header()

    menu_items = f"""
{Colors.BLUE}{Colors.BOLD}1.{Colors.RESET} {Colors.BLUE}🔐 Configure Authentication{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}2.{Colors.RESET} {Colors.CYAN}👤 Select Account{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}3.{Colors.RESET} {Colors.YELLOW}⚙️  Configure Risk Rules{Colors.RESET}
{Colors.GREEN}{Colors.BOLD}4.{Colors.RESET} {Colors.GREEN}🚀 Service Control{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}5.{Colors.RESET} {Colors.MAGENTA}🔍 Test Connection{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}6.{Colors.RESET} {Colors.CYAN}📊 View Dashboard{Colors.RESET}

{Colors.RED}{Colors.BOLD}0.{Colors.RESET} {Colors.RED}Exit{Colors.RESET}
"""

    print_box("Quick Actions", menu_items.strip(), Colors.CYAN, 60)
    print()

    choice = get_input("Enter choice [0-6]:")
    return choice


def show_authentication():
    """Authentication screen"""
    clear_screen()
    show_header()

    print_box("Authentication Configuration",
              "Enter your TopstepX API credentials",
              Colors.BLUE, 60)
    print()

    username = get_input("Username:")
    api_key = get_input("API Key (hidden):")

    print()
    animate_loading("Validating credentials", 1.5)
    print()

    show_success("Authentication successful!")
    show_info("JWT token obtained (valid 24h)")

    print()
    pause()


def show_account_selection():
    """Account selection screen"""
    clear_screen()
    show_header()

    accounts = f"""
{Colors.BOLD}1.{Colors.RESET} Main Trading Account
   ID: 1234 | Balance: $10,250 | {Colors.GREEN}Active{Colors.RESET}

{Colors.BOLD}2.{Colors.RESET} Practice Account
   ID: 1235 | Balance: $5,000 | {Colors.GREEN}Active{Colors.RESET}

{Colors.DIM}3. Demo Account
   ID: 1236 | Balance: $2,500 | Paused{Colors.RESET}
"""

    print_box("Select Account to Monitor", accounts.strip(), Colors.CYAN, 60)
    print()

    choice = get_input("Select account [1-3]:")

    if choice in ['1', '2']:
        print()
        animate_loading("Configuring account", 1.0)
        print()
        show_success(f"Account {choice} selected!")
        print()
        pause()


def show_risk_rules():
    """Risk rules configuration screen"""
    clear_screen()
    show_header()

    rules = f"""
{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}1. Max Contracts (Global){Colors.RESET}
   Limit: 5 contracts | Action: Close all

{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}2. Max Contracts Per Instrument{Colors.RESET}
   MNQ: 2, ES: 1 | Action: Reduce to limit

{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}3. Daily Realized Loss Limit{Colors.RESET}
   Limit: -$500 | Reset: 5:00 PM ET

{Colors.DIM}⭕ 4. Session Block (Outside Hours)
   Hours: 9:30 AM - 4:00 PM ET | Disabled{Colors.RESET}

{Colors.YELLOW}{Colors.BOLD}E.{Colors.RESET} Edit Rule  |  {Colors.RED}{Colors.BOLD}T.{Colors.RESET} Toggle  |  {Colors.BOLD}0.{Colors.RESET} Back
"""

    print_box("Risk Rules Configuration", rules.strip(), Colors.YELLOW, 65)
    print()

    choice = get_input("Select rule or action:")

    if choice in ['1', '2', '3', '4']:
        print()
        show_info(f"Opening editor for rule {choice}...")
        print()
        pause()


def show_service_control():
    """Service control screen"""
    clear_screen()
    show_header()

    status = f"""
{Colors.GREEN}● RUNNING{Colors.RESET}
PID: 12345 | Uptime: 3h 24m | CPU: 2.3% | Memory: 45.2 MB

{Colors.BOLD}Connections:{Colors.RESET}
{Colors.GREEN}✓{Colors.RESET} TopstepX API - Connected (45ms)
{Colors.GREEN}✓{Colors.RESET} SignalR WebSocket - Connected (32ms)
{Colors.GREEN}✓{Colors.RESET} Database - OK (state.db)
"""

    print_box("Service Status", status.strip(), Colors.GREEN, 60)
    print()

    actions = f"""
{Colors.GREEN}{Colors.BOLD}1.{Colors.RESET} {Colors.GREEN}▶️  Start Service{Colors.RESET}
{Colors.RED}{Colors.BOLD}2.{Colors.RESET} {Colors.RED}⏹️  Stop Service{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}3.{Colors.RESET} {Colors.YELLOW}🔄 Restart Service{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}4.{Colors.RESET} {Colors.CYAN}📋 View Logs{Colors.RESET}

{Colors.BOLD}0.{Colors.RESET} Back
"""

    print_box("Actions", actions.strip(), Colors.GREEN, 40)
    print()

    choice = get_input("Select action [0-4]:")

    if choice in ['1', '2', '3']:
        print()
        action_name = {
            '1': 'Starting service',
            '2': 'Stopping service',
            '3': 'Restarting service'
        }[choice]
        animate_loading(action_name, 1.5)
        print()
        show_success("Operation complete!")
        print()
        pause()
    elif choice == '4':
        show_logs()


def show_logs():
    """Show service logs"""
    clear_screen()
    show_header()

    logs = f"""
{Colors.DIM}[14:45:12]{Colors.RESET} INFO  Event received: GatewayUserPosition
{Colors.DIM}[14:45:12]{Colors.RESET} DEBUG Position updated: MNQ +2 @ 21000.5
{Colors.DIM}[14:45:13]{Colors.RESET} INFO  Rule check: MaxContractsPerInstr
{Colors.GREEN}[14:45:13] INFO  ✓ Within limit (2/2 allowed){Colors.RESET}
{Colors.DIM}[14:45:15]{Colors.RESET} INFO  Event received: GatewayUserTrade
{Colors.DIM}[14:45:15]{Colors.RESET} DEBUG Trade: MNQ SELL 1 @ 21001.0
{Colors.DIM}[14:45:15]{Colors.RESET} INFO  P&L updated: -$45.50 (realized)
{Colors.GREEN}[14:45:15] INFO  ✓ Within limit (-$45.50 / -$500){Colors.RESET}
{Colors.DIM}[14:45:20]{Colors.RESET} INFO  SignalR heartbeat: OK
"""

    print_box("Live Service Logs", logs.strip(), Colors.CYAN, 70)
    print()
    pause()


def show_connection_test():
    """Connection test screen"""
    clear_screen()
    show_header()

    print_box("Connection Test", "Running diagnostic tests...", Colors.MAGENTA, 60)
    print()

    tests = [
        ("Testing TopstepX API", 1.0),
        ("Testing SignalR WebSocket", 1.0),
        ("Testing Account Access", 1.0),
    ]

    for test_name, duration in tests:
        animate_loading(test_name, duration)
        time.sleep(0.3)

    print()
    show_success("All tests passed!")
    print()
    pause()


def show_dashboard():
    """Dashboard screen"""
    clear_screen()
    show_header()

    metrics = f"""
{Colors.RED}Realized P&L:    -$245.50{Colors.RESET}
{Colors.GREEN}Unrealized P&L:  +$120.00{Colors.RESET}
{Colors.CYAN}Total Trades:    14{Colors.RESET}
"""

    print_box("Today's Performance", metrics.strip(), Colors.CYAN, 50)
    print()

    positions = f"""
{Colors.GREEN}MNQ: +2 @ 21000.5{Colors.RESET} (P&L: +$85.00)
{Colors.GREEN}ES: +1 @ 5850.25{Colors.RESET} (P&L: +$35.00)
"""

    print_box("Open Positions", positions.strip(), Colors.CYAN, 50)
    print()
    pause()


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application loop"""
    while True:
        choice = show_main_menu()

        if choice == '0':
            clear_screen()
            print_centered(f"{Colors.GREEN}Thank you for using Risk Manager!{Colors.RESET}")
            print()
            sys.exit(0)
        elif choice == '1':
            show_authentication()
        elif choice == '2':
            show_account_selection()
        elif choice == '3':
            show_risk_rules()
        elif choice == '4':
            show_service_control()
        elif choice == '5':
            show_connection_test()
        elif choice == '6':
            show_dashboard()
        else:
            print_centered(f"{Colors.RED}Invalid choice. Please try again.{Colors.RESET}")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print_centered(f"{Colors.YELLOW}Setup cancelled by user{Colors.RESET}")
        print()
        sys.exit(0)
