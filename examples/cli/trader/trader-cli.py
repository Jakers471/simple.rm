#!/usr/bin/env python3
"""
Trader CLI - Live Trading Dashboard
Real-time display with running clocks, P&L tracking, and position monitoring

NO DEPENDENCIES - Pure Python 3!

Features:
- Live clock updates
- Real-time P&L tracking
- Position monitoring
- Lockout status with countdown timers
- Rule status indicators
- Auto-refreshing display
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# ============================================================================
# COLOR CODES - ANSI escape sequences
# ============================================================================

class Colors:
    """Dark mode color palette"""
    RESET = '\033[0m'

    # Text colors
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BRIGHT_WHITE = '\033[1;97m'

    # Semantic colors
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    MAGENTA = '\033[95m'
    RED = '\033[91m'

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    BLINK = '\033[5m'


# ============================================================================
# SIMULATED DATA (Replace with real backend calls)
# ============================================================================

class TradingState:
    """Simulated trading state"""

    def __init__(self):
        self.realized_pnl = -245.50
        self.unrealized_pnl = 120.00
        self.trade_count = 14
        self.positions = [
            {"symbol": "MNQ", "qty": 2, "entry": 21000.5, "current": 21042.5, "pnl": 85.00},
            {"symbol": "ES", "qty": 1, "entry": 5850.25, "current": 5867.75, "pnl": 35.00},
        ]
        self.is_locked_out = False
        self.lockout_reason = None
        self.lockout_until = None
        self.daily_loss_limit = -500.00
        self.daily_loss_used_pct = 49.1
        self.session_start = datetime.now().replace(hour=9, minute=30, second=0)
        self.session_end = datetime.now().replace(hour=16, minute=0, second=0)
        self.trades_per_min_limit = 3
        self.trades_per_min_count = 2
        self.max_contracts = 5
        self.current_contracts = 3

    def simulate_tick(self):
        """Simulate market movement"""
        import random

        # Randomly update P&L
        self.unrealized_pnl += random.uniform(-5, 5)

        # Update positions
        for pos in self.positions:
            pos['current'] += random.uniform(-2, 2)
            pos['pnl'] = (pos['current'] - pos['entry']) * pos['qty'] * (100 if 'MNQ' in pos['symbol'] else 50)


# Global state
state = TradingState()
running = True


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clear_screen():
    """Clear terminal"""
    print('\033[2J\033[H', end='')


def move_cursor(row: int, col: int):
    """Move cursor to position"""
    print(f'\033[{row};{col}H', end='')


def hide_cursor():
    """Hide terminal cursor"""
    print('\033[?25l', end='')


def show_cursor():
    """Show terminal cursor"""
    print('\033[?25h', end='')


def get_terminal_size():
    """Get terminal dimensions"""
    try:
        size = os.get_terminal_size()
        return size.lines, size.columns
    except:
        return 40, 120


def draw_box(row: int, col: int, width: int, height: int, title: str = "", color: str = Colors.CYAN):
    """Draw a box at position"""
    move_cursor(row, col)
    print(f"{color}╔{'═' * (width - 2)}╗{Colors.RESET}")

    if title:
        move_cursor(row, col + 2)
        print(f"{color}║{Colors.RESET} {Colors.BOLD}{title}{Colors.RESET} ", end='')
        move_cursor(row, col + width - 1)
        print(f"{color}║{Colors.RESET}")
        move_cursor(row + 1, col)
        print(f"{color}╠{'═' * (width - 2)}╣{Colors.RESET}")
        start_row = row + 2
    else:
        start_row = row + 1

    for i in range(start_row, row + height - 1):
        move_cursor(i, col)
        print(f"{color}║{Colors.RESET}", end='')
        move_cursor(i, col + width - 1)
        print(f"{color}║{Colors.RESET}")

    move_cursor(row + height - 1, col)
    print(f"{color}╚{'═' * (width - 2)}╝{Colors.RESET}")


def draw_text(row: int, col: int, text: str):
    """Draw text at position"""
    move_cursor(row, col)
    print(text, end='')


def draw_progress_bar(row: int, col: int, width: int, percentage: float, color: str = Colors.GREEN):
    """Draw a progress bar"""
    filled = int(width * (percentage / 100))
    empty = width - filled

    bar_color = color
    if percentage > 75:
        bar_color = Colors.YELLOW
    if percentage > 90:
        bar_color = Colors.RED

    move_cursor(row, col)
    print(f"{bar_color}{'█' * filled}{Colors.DIM}{'░' * empty}{Colors.RESET} {percentage:.1f}%", end='')


# ============================================================================
# DASHBOARD SECTIONS
# ============================================================================

def draw_header(start_row: int, width: int):
    """Draw main header with live clock"""
    current_time = datetime.now().strftime("%I:%M:%S %p")
    current_date = datetime.now().strftime("%A, %B %d, %Y")

    # Title
    title = "RISK MANAGER - LIVE TRADING DASHBOARD"
    title_col = (width - len(title)) // 2
    draw_text(start_row, title_col, f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.RESET}")

    # Clock
    clock_text = f"🕐 {current_time}"
    clock_col = (width - len(clock_text)) // 2
    draw_text(start_row + 1, clock_col, f"{Colors.BOLD}{clock_text}{Colors.RESET}")

    # Date
    date_col = (width - len(current_date)) // 2
    draw_text(start_row + 2, date_col, f"{Colors.DIM}{current_date}{Colors.RESET}")


def draw_lockout_status(start_row: int, start_col: int, width: int):
    """Draw lockout status box"""
    height = 8

    if state.is_locked_out and state.lockout_until:
        draw_box(start_row, start_col, width, height, "LOCKOUT STATUS", Colors.RED)

        # Status
        draw_text(start_row + 3, start_col + 3, f"{Colors.RED}{Colors.BOLD}🔴 LOCKED OUT{Colors.RESET}")

        # Reason
        draw_text(start_row + 4, start_col + 3, f"{Colors.DIM}Reason:{Colors.RESET} {state.lockout_reason}")

        # Countdown
        remaining = state.lockout_until - datetime.now()
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        seconds = int(remaining.total_seconds() % 60)

        draw_text(start_row + 5, start_col + 3, f"{Colors.YELLOW}Unlocks in:{Colors.RESET} {hours:02d}:{minutes:02d}:{seconds:02d}")
        draw_text(start_row + 6, start_col + 3, f"{Colors.DIM}Reset at:{Colors.RESET} {state.lockout_until.strftime('%I:%M %p')}")

    else:
        draw_box(start_row, start_col, width, height, "TRADING STATUS", Colors.GREEN)

        # Status
        draw_text(start_row + 3, start_col + 3, f"{Colors.GREEN}{Colors.BOLD}🟢 OK TO TRADE{Colors.RESET}")

        # Session info
        now = datetime.now()
        if state.session_start <= now <= state.session_end:
            draw_text(start_row + 4, start_col + 3, f"{Colors.GREEN}✓{Colors.RESET} Within session hours")
        else:
            draw_text(start_row + 4, start_col + 3, f"{Colors.YELLOW}⚠{Colors.RESET} Outside session hours")

        draw_text(start_row + 5, start_col + 3, f"{Colors.DIM}Session:{Colors.RESET} {state.session_start.strftime('%I:%M %p')} - {state.session_end.strftime('%I:%M %p')}")


def draw_pnl_display(start_row: int, start_col: int, width: int):
    """Draw P&L metrics"""
    height = 12
    draw_box(start_row, start_col, width, height, "TODAY'S P&L", Colors.CYAN)

    # Realized P&L
    realized_color = Colors.GREEN if state.realized_pnl >= 0 else Colors.RED
    draw_text(start_row + 3, start_col + 3, f"{Colors.DIM}Realized P&L:{Colors.RESET}")
    draw_text(start_row + 3, start_col + 25, f"{realized_color}{Colors.BOLD}${state.realized_pnl:,.2f}{Colors.RESET}")

    # Unrealized P&L
    unrealized_color = Colors.GREEN if state.unrealized_pnl >= 0 else Colors.RED
    draw_text(start_row + 4, start_col + 3, f"{Colors.DIM}Unrealized P&L:{Colors.RESET}")
    draw_text(start_row + 4, start_col + 25, f"{unrealized_color}{Colors.BOLD}${state.unrealized_pnl:,.2f}{Colors.RESET}")

    # Net P&L
    net_pnl = state.realized_pnl + state.unrealized_pnl
    net_color = Colors.GREEN if net_pnl >= 0 else Colors.RED
    draw_text(start_row + 5, start_col + 3, f"{Colors.BOLD}Net P&L:{Colors.RESET}")
    draw_text(start_row + 5, start_col + 25, f"{net_color}{Colors.BOLD}${net_pnl:,.2f}{Colors.RESET}")

    # Daily loss limit
    draw_text(start_row + 7, start_col + 3, f"{Colors.DIM}Daily Loss Limit:{Colors.RESET} ${state.daily_loss_limit:,.2f}")
    draw_text(start_row + 8, start_col + 3, f"{Colors.DIM}Used:{Colors.RESET}")
    draw_progress_bar(start_row + 9, start_col + 3, width - 7, state.daily_loss_used_pct)

    # Trade count
    draw_text(start_row + 10, start_col + 3, f"{Colors.DIM}Trades Today:{Colors.RESET} {Colors.CYAN}{Colors.BOLD}{state.trade_count}{Colors.RESET}")


def draw_positions(start_row: int, start_col: int, width: int):
    """Draw open positions"""
    height = 12
    draw_box(start_row, start_col, width, height, "OPEN POSITIONS", Colors.YELLOW)

    if not state.positions:
        draw_text(start_row + 3, start_col + 3, f"{Colors.DIM}No open positions{Colors.RESET}")
    else:
        # Header
        draw_text(start_row + 3, start_col + 3, f"{Colors.BOLD}Symbol  Qty  Entry      Current    P&L{Colors.RESET}")

        # Positions
        for idx, pos in enumerate(state.positions):
            row = start_row + 4 + idx
            pnl_color = Colors.GREEN if pos['pnl'] >= 0 else Colors.RED
            qty_display = f"+{pos['qty']}" if pos['qty'] > 0 else str(pos['qty'])

            draw_text(row, start_col + 3,
                     f"{Colors.CYAN}{pos['symbol']:<7}{Colors.RESET} "
                     f"{qty_display:<4} "
                     f"{pos['entry']:<10.2f} "
                     f"{pos['current']:<10.2f} "
                     f"{pnl_color}{pos['pnl']:>+8.2f}{Colors.RESET}")

        # Total
        total_pnl = sum(p['pnl'] for p in state.positions)
        total_color = Colors.GREEN if total_pnl >= 0 else Colors.RED
        draw_text(start_row + 4 + len(state.positions) + 1, start_col + 3,
                 f"{Colors.BOLD}Total Unrealized P&L: {total_color}${total_pnl:,.2f}{Colors.RESET}")


def draw_risk_rules(start_row: int, start_col: int, width: int):
    """Draw active risk rules status"""
    height = 13
    draw_box(start_row, start_col, width, height, "RISK RULES STATUS", Colors.MAGENTA)

    # Max Contracts
    contracts_pct = (state.current_contracts / state.max_contracts) * 100
    draw_text(start_row + 3, start_col + 3, f"{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Max Contracts{Colors.RESET}")
    draw_text(start_row + 4, start_col + 5, f"{state.current_contracts}/{state.max_contracts} contracts")
    draw_progress_bar(start_row + 5, start_col + 5, width - 10, contracts_pct, Colors.GREEN)

    # Daily Loss
    draw_text(start_row + 7, start_col + 3, f"{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Daily Loss Limit{Colors.RESET}")
    draw_text(start_row + 8, start_col + 5, f"${abs(state.realized_pnl):,.2f} / ${abs(state.daily_loss_limit):,.2f}")
    draw_progress_bar(start_row + 9, start_col + 5, width - 10, state.daily_loss_used_pct, Colors.GREEN)

    # Trade Frequency
    freq_pct = (state.trades_per_min_count / state.trades_per_min_limit) * 100
    draw_text(start_row + 11, start_col + 3, f"{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Trade Frequency{Colors.RESET}")
    draw_text(start_row + 12, start_col + 5, f"{state.trades_per_min_count}/{state.trades_per_min_limit} trades/min")


def draw_recent_activity(start_row: int, start_col: int, width: int):
    """Draw recent enforcement activity log"""
    height = 10
    draw_box(start_row, start_col, width, height, "RECENT ACTIVITY", Colors.BLUE)

    # Mock recent events
    events = [
        (datetime.now() - timedelta(seconds=15), "Position updated: MNQ +2 @ 21042.5", Colors.CYAN),
        (datetime.now() - timedelta(seconds=45), "✓ Max Contracts check passed (3/5)", Colors.GREEN),
        (datetime.now() - timedelta(minutes=2), "Trade executed: MNQ SELL 1 @ 21001.0", Colors.CYAN),
        (datetime.now() - timedelta(minutes=5), "✓ Daily Loss check passed (-$245.50)", Colors.GREEN),
        (datetime.now() - timedelta(minutes=10), "SignalR heartbeat: OK", Colors.DIM),
    ]

    for idx, (timestamp, message, color) in enumerate(events):
        if idx >= 5:
            break
        time_str = timestamp.strftime("%H:%M:%S")
        draw_text(start_row + 3 + idx, start_col + 3, f"{Colors.DIM}[{time_str}]{Colors.RESET} {color}{message}{Colors.RESET}")


def draw_controls(start_row: int, start_col: int, width: int):
    """Draw control instructions"""
    controls = f"{Colors.DIM}Press {Colors.RESET}{Colors.BOLD}Q{Colors.RESET}{Colors.DIM} to quit  |  Auto-refresh: 1s{Colors.RESET}"
    controls_col = start_col + (width - len("Press Q to quit  |  Auto-refresh: 1s")) // 2
    draw_text(start_row, controls_col, controls)


# ============================================================================
# MAIN DISPLAY LOOP
# ============================================================================

def update_display():
    """Redraw entire dashboard"""
    height, width = get_terminal_size()

    # Clear and hide cursor
    clear_screen()
    hide_cursor()

    # Header
    draw_header(1, width)

    # Calculate layout
    col_width = width // 2 - 4
    left_col = 2
    right_col = width // 2 + 2

    # Left column
    draw_lockout_status(5, left_col, col_width)
    draw_pnl_display(14, left_col, col_width)
    draw_positions(27, left_col, col_width)

    # Right column
    draw_risk_rules(5, right_col, col_width)
    draw_recent_activity(19, right_col, col_width)

    # Footer
    draw_controls(height - 2, 0, width)

    # Flush output
    sys.stdout.flush()


def tick_thread():
    """Background thread for market simulation"""
    while running:
        state.simulate_tick()
        time.sleep(2)


def input_thread():
    """Background thread for user input"""
    global running
    import select

    while running:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            char = sys.stdin.read(1)
            if char.lower() == 'q':
                running = False
                break
        time.sleep(0.1)


def main():
    """Main application"""
    global running

    # Set terminal to raw mode for immediate input
    import tty
    import termios

    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())

        # Start background threads
        market_thread = threading.Thread(target=tick_thread, daemon=True)
        market_thread.start()

        user_input_thread = threading.Thread(target=input_thread, daemon=True)
        user_input_thread.start()

        # Main display loop
        while running:
            update_display()
            time.sleep(1)  # Refresh every second

    except KeyboardInterrupt:
        running = False

    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        show_cursor()
        clear_screen()
        print(f"\n{Colors.CYAN}Trading dashboard closed.{Colors.RESET}\n")


if __name__ == "__main__":
    main()
