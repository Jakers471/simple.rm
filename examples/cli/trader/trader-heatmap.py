#!/usr/bin/env python3
"""
RISK HEATMAP VIEW - Visual Risk Management
Perfect for: Risk-conscious traders, visual learners

Features:
- Color-coded risk zones (green/yellow/red)
- Large visual P&L display
- Risk limit heat gauges
- Position heat map
- Quick stats carousel

NO DEPENDENCIES
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta


class Colors:
    RESET = '\033[0m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    MAGENTA = '\033[95m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Backgrounds
    BG_RED = '\033[48;5;196m'
    BG_ORANGE = '\033[48;5;208m'
    BG_YELLOW = '\033[48;5;226m'
    BG_GREEN = '\033[48;5;46m'
    BG_DARK_GREEN = '\033[48;5;28m'
    BG_DARK_RED = '\033[48;5;88m'


class State:
    def __init__(self):
        self.net_pnl = -125.50
        self.realized_pnl = -245.50
        self.unrealized_pnl = 120.00

        self.daily_loss_limit = -500.00
        self.daily_loss_used_pct = 49.1

        self.max_contracts = 5
        self.current_contracts = 3

        self.trades_today = 14
        self.win_rate = 57.1

        self.positions = [
            {"symbol": "MNQ", "risk_score": 65, "pnl": 85.00},
            {"symbol": "ES", "risk_score": 35, "pnl": 35.00},
        ]


state = State()
running = True


def move_cursor(row, col):
    print(f'\033[{row};{col}H', end='', flush=False)


def hide_cursor():
    print('\033[?25l', end='', flush=False)


def show_cursor():
    print('\033[?25h', end='', flush=True)


def clear_screen():
    print('\033[2J\033[H', end='', flush=True)


def get_risk_color(percentage):
    """Get color based on risk level"""
    if percentage < 40:
        return Colors.BG_DARK_GREEN, Colors.WHITE
    elif percentage < 60:
        return Colors.BG_GREEN, Colors.WHITE
    elif percentage < 75:
        return Colors.BG_YELLOW, Colors.GRAY
    elif percentage < 90:
        return Colors.BG_ORANGE, Colors.WHITE
    else:
        return Colors.BG_RED, Colors.WHITE


def draw_giant_pnl(start_row, start_col):
    """Giant P&L display"""
    pnl_color = Colors.GREEN if state.net_pnl >= 0 else Colors.RED

    # Giant number
    pnl_str = f"${abs(state.net_pnl):.2f}"
    sign = "+" if state.net_pnl >= 0 else "-"

    move_cursor(start_row, start_col)
    print(f"{pnl_color}{Colors.BOLD}", end='', flush=False)

    # ASCII art style number
    move_cursor(start_row, start_col + 20)
    print(f" NET P&L TODAY ", end='', flush=False)

    move_cursor(start_row + 2, start_col + 15)
    print(f"{sign}{pnl_str}", end='', flush=False)
    print(f"{Colors.RESET}", end='', flush=False)

    # Breakdown
    move_cursor(start_row + 4, start_col + 10)
    realized_color = Colors.GREEN if state.realized_pnl >= 0 else Colors.RED
    print(f"{Colors.DIM}Realized:{Colors.RESET} {realized_color}${state.realized_pnl:.2f}{Colors.RESET}", end='', flush=False)

    move_cursor(start_row + 5, start_col + 10)
    unrealized_color = Colors.GREEN if state.unrealized_pnl >= 0 else Colors.RED
    print(f"{Colors.DIM}Unrealized:{Colors.RESET} {unrealized_color}${state.unrealized_pnl:.2f}{Colors.RESET}", end='', flush=False)


def draw_risk_heatmap(start_row, start_col):
    """Visual risk heat map"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}RISK HEAT MAP{Colors.RESET}", flush=False)

    # Daily Loss Risk
    loss_pct = abs(state.realized_pnl / state.daily_loss_limit) * 100
    bg_color, fg_color = get_risk_color(loss_pct)

    move_cursor(start_row + 2, start_col)
    print(f"{Colors.DIM}Daily Loss Limit:{Colors.RESET}", flush=False)

    move_cursor(start_row + 3, start_col)
    heat_blocks = int(40 * (loss_pct / 100))
    print(f"{bg_color}{fg_color}{' ' * heat_blocks}{Colors.RESET}{Colors.DIM}{'░' * (40 - heat_blocks)}{Colors.RESET}", flush=False)

    move_cursor(start_row + 4, start_col)
    print(f"  {loss_pct:.1f}% Used  |  ${abs(state.realized_pnl):.0f} of ${abs(state.daily_loss_limit):.0f}", flush=False)

    # Contract Usage Risk
    contracts_pct = (state.current_contracts / state.max_contracts) * 100
    bg_color, fg_color = get_risk_color(contracts_pct)

    move_cursor(start_row + 6, start_col)
    print(f"{Colors.DIM}Contract Usage:{Colors.RESET}", flush=False)

    move_cursor(start_row + 7, start_col)
    heat_blocks = int(40 * (contracts_pct / 100))
    print(f"{bg_color}{fg_color}{' ' * heat_blocks}{Colors.RESET}{Colors.DIM}{'░' * (40 - heat_blocks)}{Colors.RESET}", flush=False)

    move_cursor(start_row + 8, start_col)
    print(f"  {contracts_pct:.1f}% Used  |  {state.current_contracts} of {state.max_contracts} contracts", flush=False)


def draw_position_heatmap(start_row, start_col):
    """Position risk heat map"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}POSITION RISK{Colors.RESET}", flush=False)

    for idx, pos in enumerate(state.positions):
        row = start_row + 2 + (idx * 3)

        bg_color, fg_color = get_risk_color(pos['risk_score'])

        move_cursor(row, start_col)
        print(f"{pos['symbol']}", flush=False)

        move_cursor(row + 1, start_col)
        heat_blocks = int(30 * (pos['risk_score'] / 100))
        print(f"{bg_color}{fg_color}{' ' * heat_blocks}{Colors.RESET}{Colors.DIM}{'░' * (30 - heat_blocks)}{Colors.RESET}", flush=False)

        pnl_color = Colors.GREEN if pos['pnl'] >= 0 else Colors.RED
        move_cursor(row + 1, start_col + 32)
        print(f"{pnl_color}{pos['pnl']:+.2f}{Colors.RESET}", flush=False)


def draw_quick_stats(start_row, start_col):
    """Quick rotating stats"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}QUICK STATS{Colors.RESET}", flush=False)

    # Current rotation (would rotate every few seconds)
    stats = [
        f"Trades Today: {state.trades_today}",
        f"Win Rate: {state.win_rate:.1f}%",
        f"Time: {datetime.now().strftime('%I:%M:%S %p')}",
    ]

    for idx, stat in enumerate(stats):
        move_cursor(start_row + 2 + idx, start_col)
        print(f"{Colors.CYAN}▸{Colors.RESET} {stat}", flush=False)


def draw_alert_zone(start_row, start_col):
    """Alert messages"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}{Colors.YELLOW}⚠ ALERTS{Colors.RESET}", flush=False)

    # Check for warnings
    alerts = []

    if state.daily_loss_used_pct > 80:
        alerts.append(f"{Colors.RED}• Approaching daily loss limit!{Colors.RESET}")

    if state.current_contracts >= state.max_contracts * 0.8:
        alerts.append(f"{Colors.YELLOW}• High contract usage{Colors.RESET}")

    if not alerts:
        alerts.append(f"{Colors.GREEN}• All systems normal{Colors.RESET}")

    for idx, alert in enumerate(alerts[:3]):
        move_cursor(start_row + 2 + idx, start_col)
        print(alert, flush=False)


def draw_screen():
    """Draw complete heatmap view"""
    clear_screen()
    hide_cursor()

    # Header
    move_cursor(1, 2)
    print(f"{Colors.BOLD}{Colors.MAGENTA}═══ RISK HEATMAP VIEW ═══{Colors.RESET} "
          f"{Colors.DIM}{datetime.now().strftime('%I:%M:%S %p')}{Colors.RESET}", flush=False)

    # Layout
    draw_giant_pnl(3, 2)
    draw_risk_heatmap(10, 2)
    draw_position_heatmap(10, 50)
    draw_quick_stats(20, 2)
    draw_alert_zone(20, 50)

    # Footer
    try:
        height = os.get_terminal_size().lines
    except:
        height = 40

    move_cursor(height - 1, 2)
    print(f"{Colors.DIM}[Q] Quit  |  [R] Refresh  |  Updates: 1s{Colors.RESET}", flush=False)

    sys.stdout.flush()


def tick_thread():
    """Update data"""
    import random
    while running:
        for pos in state.positions:
            pos['pnl'] += random.uniform(-2, 2)
            pos['risk_score'] = max(0, min(100, pos['risk_score'] + random.uniform(-5, 5)))

        state.unrealized_pnl = sum(p['pnl'] for p in state.positions)
        state.net_pnl = state.realized_pnl + state.unrealized_pnl

        time.sleep(1)


def input_thread():
    """Handle input"""
    global running
    import select

    while running:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            char = sys.stdin.read(1)
            if char.lower() == 'q':
                running = False
        time.sleep(0.1)


def main():
    global running

    import tty
    import termios

    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())

        market = threading.Thread(target=tick_thread, daemon=True)
        user_input = threading.Thread(target=input_thread, daemon=True)
        market.start()
        user_input.start()

        while running:
            draw_screen()
            time.sleep(1)

    except KeyboardInterrupt:
        running = False

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        show_cursor()
        clear_screen()
        print(f"\n{Colors.MAGENTA}Heatmap view closed.{Colors.RESET}\n")


if __name__ == "__main__":
    main()
