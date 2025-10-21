#!/usr/bin/env python3
"""
COMPACT TRADER VIEW - Everything at a Glance
Perfect for: Single monitor traders, quick status checks

Layout:
- Top: Current time, session countdown, account status
- Left: P&L metrics with sparklines
- Center: Open positions table
- Right: Risk gauges and alerts
- Bottom: Interactive menu bar

NO DEPENDENCIES - Pure Python 3
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
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'


class TradingState:
    def __init__(self):
        self.realized_pnl = -245.50
        self.unrealized_pnl = 120.00
        self.net_pnl = -125.50
        self.daily_high = 450.00
        self.daily_low = -350.00
        self.trade_count = 14
        self.win_rate = 57.1
        self.avg_win = 125.50
        self.avg_loss = -85.20
        self.largest_win = 350.00
        self.largest_loss = -280.00

        self.positions = [
            {"symbol": "MNQ", "qty": 2, "side": "LONG", "entry": 21000.5, "current": 21042.5, "pnl": 85.00, "pnl_pct": 0.4},
            {"symbol": "ES", "qty": 1, "side": "LONG", "entry": 5850.25, "current": 5867.75, "pnl": 35.00, "pnl_pct": 0.3},
        ]

        self.daily_loss_limit = -500.00
        self.daily_loss_used = 49.1
        self.contracts_used = 3
        self.contracts_max = 5
        self.trades_per_min = 2
        self.trades_per_min_max = 3

        self.session_start = datetime.now().replace(hour=9, minute=30, second=0)
        self.session_end = datetime.now().replace(hour=16, minute=0, second=0)

        self.is_locked_out = False
        self.last_trade_time = datetime.now() - timedelta(minutes=2)

        # P&L history for sparkline (last 20 ticks)
        self.pnl_history = [-125.50] * 20


state = TradingState()
running = True
menu_mode = False


def move_cursor(row, col):
    print(f'\033[{row};{col}H', end='', flush=False)


def hide_cursor():
    print('\033[?25l', end='', flush=False)


def show_cursor():
    print('\033[?25h', end='', flush=True)


def clear_screen():
    print('\033[2J\033[H', end='', flush=True)


def draw_sparkline(values, width=20, color=Colors.CYAN):
    """Draw mini sparkline chart"""
    if not values or len(values) < 2:
        return ' ' * width

    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        return '─' * width

    chars = ' ▁▂▃▄▅▆▇█'

    sparkline = ''
    for val in values[-width:]:
        normalized = (val - min_val) / (max_val - min_val)
        idx = int(normalized * (len(chars) - 1))
        sparkline += chars[idx]

    return f"{color}{sparkline}{Colors.RESET}"


def draw_gauge(value, max_value, width=20, label=""):
    """Draw horizontal gauge bar"""
    pct = min(100, (value / max_value) * 100)
    filled = int(width * (pct / 100))

    if pct < 50:
        color = Colors.GREEN
    elif pct < 80:
        color = Colors.YELLOW
    else:
        color = Colors.RED

    bar = f"{color}{'█' * filled}{Colors.DIM}{'░' * (width - filled)}{Colors.RESET}"
    pct_text = f"{pct:5.1f}%"

    return f"{label:<15} {bar} {pct_text}"


def get_session_remaining():
    """Get time remaining in session"""
    now = datetime.now()
    if now > state.session_end:
        return "After Hours", Colors.RED
    elif now < state.session_start:
        return "Pre-Market", Colors.YELLOW

    remaining = state.session_end - now
    hours = int(remaining.total_seconds() // 3600)
    minutes = int((remaining.total_seconds() % 3600) // 60)

    return f"{hours:02d}:{minutes:02d}", Colors.GREEN


def draw_header():
    """Top status bar"""
    now = datetime.now()
    current_time = now.strftime("%I:%M:%S %p")
    session_time, session_color = get_session_remaining()

    # Account status indicator
    if state.is_locked_out:
        status = f"{Colors.BG_RED}{Colors.WHITE} LOCKED OUT {Colors.RESET}"
    elif state.daily_loss_used > 90:
        status = f"{Colors.BG_YELLOW}{Colors.WHITE} WARNING {Colors.RESET}"
    else:
        status = f"{Colors.BG_GREEN}{Colors.WHITE} ACTIVE {Colors.RESET}"

    move_cursor(1, 2)
    print(f"{status}  {Colors.BOLD}⏰ {current_time}{Colors.RESET}  "
          f"{Colors.DIM}Session:{Colors.RESET} {session_color}{session_time}{Colors.RESET}  "
          f"{Colors.DIM}Account: Main Trading (1234){Colors.RESET}", end='', flush=False)


def draw_pnl_section(start_row, start_col):
    """P&L metrics with sparkline"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════╗{Colors.RESET}", flush=False)

    move_cursor(start_row + 1, start_col)
    print(f"{Colors.CYAN}║{Colors.RESET} {Colors.BOLD}P&L SUMMARY{Colors.RESET}              {Colors.CYAN}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 2, start_col)
    print(f"{Colors.CYAN}╠══════════════════════════════╣{Colors.RESET}", flush=False)

    # Net P&L with sparkline
    net_color = Colors.GREEN if state.net_pnl >= 0 else Colors.RED
    move_cursor(start_row + 3, start_col)
    print(f"{Colors.CYAN}║{Colors.RESET} {Colors.BOLD}Net:{Colors.RESET} {net_color}{state.net_pnl:>8.2f}{Colors.RESET}            {Colors.CYAN}║{Colors.RESET}", flush=False)

    sparkline = draw_sparkline(state.pnl_history, 20)
    move_cursor(start_row + 4, start_col)
    print(f"{Colors.CYAN}║{Colors.RESET} {sparkline}         {Colors.CYAN}║{Colors.RESET}", flush=False)

    # Realized/Unrealized
    realized_color = Colors.GREEN if state.realized_pnl >= 0 else Colors.RED
    unrealized_color = Colors.GREEN if state.unrealized_pnl >= 0 else Colors.RED

    move_cursor(start_row + 5, start_col)
    print(f"{Colors.CYAN}║{Colors.RESET} {Colors.DIM}Real:{Colors.RESET} {realized_color}{state.realized_pnl:>7.2f}{Colors.RESET}           {Colors.CYAN}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 6, start_col)
    print(f"{Colors.CYAN}║{Colors.RESET} {Colors.DIM}Unrl:{Colors.RESET} {unrealized_color}{state.unrealized_pnl:>7.2f}{Colors.RESET}           {Colors.CYAN}║{Colors.RESET}", flush=False)

    # Win rate and trades
    move_cursor(start_row + 7, start_col)
    print(f"{Colors.CYAN}╠══════════════════════════════╣{Colors.RESET}", flush=False)

    move_cursor(start_row + 8, start_col)
    print(f"{Colors.CYAN}║{Colors.RESET} {Colors.DIM}Trades:{Colors.RESET} {state.trade_count}  {Colors.DIM}WinRate:{Colors.RESET} {state.win_rate:.1f}% {Colors.CYAN}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 9, start_col)
    print(f"{Colors.CYAN}║{Colors.RESET} {Colors.DIM}Avg Win:{Colors.RESET} {Colors.GREEN}+${state.avg_win:.0f}{Colors.RESET}         {Colors.CYAN}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 10, start_col)
    print(f"{Colors.CYAN}║{Colors.RESET} {Colors.DIM}Avg Loss:{Colors.RESET} {Colors.RED}${state.avg_loss:.0f}{Colors.RESET}         {Colors.CYAN}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 11, start_col)
    print(f"{Colors.CYAN}╚══════════════════════════════╝{Colors.RESET}", flush=False)


def draw_positions_table(start_row, start_col, width):
    """Positions table"""
    move_cursor(start_row, start_col)
    print(f"{Colors.YELLOW}╔{'═' * (width - 2)}╗{Colors.RESET}", flush=False)

    move_cursor(start_row + 1, start_col)
    print(f"{Colors.YELLOW}║{Colors.RESET} {Colors.BOLD}OPEN POSITIONS{Colors.RESET}" + ' ' * (width - 18) + f"{Colors.YELLOW}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 2, start_col)
    print(f"{Colors.YELLOW}╠{'═' * (width - 2)}╣{Colors.RESET}", flush=False)

    # Header
    move_cursor(start_row + 3, start_col)
    print(f"{Colors.YELLOW}║{Colors.RESET} {Colors.BOLD}{'Symbol':<7} {'Side':<5} {'Qty':<4} {'Entry':<10} {'Current':<10} {'P&L':<10}{Colors.RESET} {Colors.YELLOW}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 4, start_col)
    print(f"{Colors.YELLOW}╠{'═' * (width - 2)}╣{Colors.RESET}", flush=False)

    # Positions
    for idx, pos in enumerate(state.positions):
        row = start_row + 5 + idx
        pnl_color = Colors.GREEN if pos['pnl'] >= 0 else Colors.RED
        side_color = Colors.GREEN if pos['side'] == 'LONG' else Colors.RED

        move_cursor(row, start_col)
        print(f"{Colors.YELLOW}║{Colors.RESET} "
              f"{Colors.CYAN}{pos['symbol']:<7}{Colors.RESET} "
              f"{side_color}{pos['side']:<5}{Colors.RESET} "
              f"{pos['qty']:<4} "
              f"{pos['entry']:<10.2f} "
              f"{pos['current']:<10.2f} "
              f"{pnl_color}{pos['pnl']:>+7.2f} ({pos['pnl_pct']:>+.1f}%){Colors.RESET} "
              f"{Colors.YELLOW}║{Colors.RESET}", flush=False)

    # Fill empty rows
    for idx in range(len(state.positions), 3):
        row = start_row + 5 + idx
        move_cursor(row, start_col)
        print(f"{Colors.YELLOW}║{Colors.RESET}" + ' ' * (width - 2) + f"{Colors.YELLOW}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 8, start_col)
    print(f"{Colors.YELLOW}╚{'═' * (width - 2)}╝{Colors.RESET}", flush=False)


def draw_risk_gauges(start_row, start_col):
    """Risk limit gauges"""
    move_cursor(start_row, start_col)
    print(f"{Colors.MAGENTA}╔══════════════════════════════════╗{Colors.RESET}", flush=False)

    move_cursor(start_row + 1, start_col)
    print(f"{Colors.MAGENTA}║{Colors.RESET} {Colors.BOLD}RISK LIMITS{Colors.RESET}                    {Colors.MAGENTA}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 2, start_col)
    print(f"{Colors.MAGENTA}╠══════════════════════════════════╣{Colors.RESET}", flush=False)

    # Daily loss gauge
    loss_pct = abs(state.realized_pnl / state.daily_loss_limit) * 100
    loss_filled = int(20 * (loss_pct / 100))
    loss_color = Colors.GREEN if loss_pct < 50 else (Colors.YELLOW if loss_pct < 80 else Colors.RED)
    loss_bar = f"{loss_color}{'█' * loss_filled}{Colors.DIM}{'░' * (20 - loss_filled)}{Colors.RESET}"

    move_cursor(start_row + 3, start_col)
    print(f"{Colors.MAGENTA}║{Colors.RESET} {Colors.DIM}Daily Loss{Colors.RESET}               {Colors.MAGENTA}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 4, start_col)
    print(f"{Colors.MAGENTA}║{Colors.RESET} {loss_bar} {loss_pct:5.1f}% {Colors.MAGENTA}║{Colors.RESET}", flush=False)

    # Contracts gauge
    contracts_pct = (state.contracts_used / state.contracts_max) * 100
    contracts_filled = int(20 * (contracts_pct / 100))
    contracts_color = Colors.GREEN if contracts_pct < 60 else (Colors.YELLOW if contracts_pct < 80 else Colors.RED)
    contracts_bar = f"{contracts_color}{'█' * contracts_filled}{Colors.DIM}{'░' * (20 - contracts_filled)}{Colors.RESET}"

    move_cursor(start_row + 5, start_col)
    print(f"{Colors.MAGENTA}║{Colors.RESET} {Colors.DIM}Contracts{Colors.RESET}                {Colors.MAGENTA}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 6, start_col)
    print(f"{Colors.MAGENTA}║{Colors.RESET} {contracts_bar} {state.contracts_used}/{state.contracts_max}   {Colors.MAGENTA}║{Colors.RESET}", flush=False)

    # Trade frequency
    freq_pct = (state.trades_per_min / state.trades_per_min_max) * 100
    freq_filled = int(20 * (freq_pct / 100))
    freq_color = Colors.GREEN if freq_pct < 70 else Colors.YELLOW
    freq_bar = f"{freq_color}{'█' * freq_filled}{Colors.DIM}{'░' * (20 - freq_filled)}{Colors.RESET}"

    move_cursor(start_row + 7, start_col)
    print(f"{Colors.MAGENTA}║{Colors.RESET} {Colors.DIM}Trade Freq{Colors.RESET}               {Colors.MAGENTA}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 8, start_col)
    print(f"{Colors.MAGENTA}║{Colors.RESET} {freq_bar} {state.trades_per_min}/{state.trades_per_min_max}/m {Colors.MAGENTA}║{Colors.RESET}", flush=False)

    # Last trade time
    time_since_trade = datetime.now() - state.last_trade_time
    mins = int(time_since_trade.total_seconds() / 60)

    move_cursor(start_row + 9, start_col)
    print(f"{Colors.MAGENTA}║{Colors.RESET} {Colors.DIM}Last Trade:{Colors.RESET} {mins}m ago           {Colors.MAGENTA}║{Colors.RESET}", flush=False)

    move_cursor(start_row + 10, start_col)
    print(f"{Colors.MAGENTA}╚══════════════════════════════════╝{Colors.RESET}", flush=False)


def draw_menu_bar():
    """Interactive bottom menu"""
    import os
    try:
        height = os.get_terminal_size().lines
    except:
        height = 40

    menu_items = [
        (f"{Colors.BOLD}[1]{Colors.RESET} Refresh", Colors.CYAN),
        (f"{Colors.BOLD}[2]{Colors.RESET} Reset Day", Colors.YELLOW),
        (f"{Colors.BOLD}[3]{Colors.RESET} Rules", Colors.MAGENTA),
        (f"{Colors.BOLD}[4]{Colors.RESET} History", Colors.BLUE),
        (f"{Colors.BOLD}[Q]{Colors.RESET} Quit", Colors.RED),
    ]

    move_cursor(height - 1, 2)
    print(f"{Colors.BG_YELLOW}{Colors.WHITE} MENU {Colors.RESET} ", end='', flush=False)

    for item, color in menu_items:
        print(f" {color}{item}{Colors.RESET} ", end='', flush=False)


def draw_initial_screen():
    """Draw complete compact dashboard"""
    clear_screen()
    hide_cursor()

    # Header
    draw_header()

    # Layout: P&L left, Positions center, Risk right
    draw_pnl_section(3, 2)
    draw_positions_table(3, 36, 60)
    draw_risk_gauges(3, 98)

    # Menu bar
    draw_menu_bar()

    sys.stdout.flush()


def update_display():
    """Update only changed values"""
    draw_header()
    draw_pnl_section(3, 2)
    draw_positions_table(3, 36, 60)
    draw_risk_gauges(3, 98)
    sys.stdout.flush()


def tick_thread():
    """Simulate market ticks"""
    import random
    while running:
        # Update positions
        for pos in state.positions:
            pos['current'] += random.uniform(-1, 1)
            multiplier = 20 if 'MNQ' in pos['symbol'] else 50
            pos['pnl'] = (pos['current'] - pos['entry']) * pos['qty'] * multiplier
            pos['pnl_pct'] = ((pos['current'] - pos['entry']) / pos['entry']) * 100

        # Update P&L
        state.unrealized_pnl = sum(p['pnl'] for p in state.positions)
        state.net_pnl = state.realized_pnl + state.unrealized_pnl

        # Update P&L history
        state.pnl_history.append(state.net_pnl)
        state.pnl_history = state.pnl_history[-20:]

        time.sleep(1)


def input_thread():
    """Handle user input"""
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

        draw_initial_screen()

        market = threading.Thread(target=tick_thread, daemon=True)
        user_input = threading.Thread(target=input_thread, daemon=True)
        market.start()
        user_input.start()

        while running:
            update_display()
            time.sleep(0.5)

    except KeyboardInterrupt:
        running = False

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        show_cursor()
        clear_screen()
        print(f"\n{Colors.CYAN}Dashboard closed.{Colors.RESET}\n")


if __name__ == "__main__":
    main()
