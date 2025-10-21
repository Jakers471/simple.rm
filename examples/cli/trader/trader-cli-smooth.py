#!/usr/bin/env python3
"""
Trader CLI - Live Trading Dashboard (SMOOTH VERSION)
Only updates changed values - NO flickering!

Features:
- Smooth clock updates (no full screen redraw)
- Real-time P&L tracking without flicker
- Only updates what changed
- Buffer-based rendering for smooth display
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# ============================================================================
# COLOR CODES
# ============================================================================

class Colors:
    RESET = '\033[0m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BRIGHT_WHITE = '\033[1;97m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    MAGENTA = '\033[95m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


# ============================================================================
# SIMULATED DATA
# ============================================================================

class TradingState:
    """Trading state with change tracking"""

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
        self.current_contracts = 3
        self.max_contracts = 5

        # Track what changed
        self.changed = set()

    def simulate_tick(self):
        """Simulate market movement"""
        import random

        old_unrealized = self.unrealized_pnl

        # Update unrealized P&L slightly
        self.unrealized_pnl += random.uniform(-0.5, 0.5)

        # Update positions
        for pos in self.positions:
            old_current = pos['current']
            pos['current'] += random.uniform(-0.5, 0.5)
            multiplier = 20 if 'MNQ' in pos['symbol'] else 50
            pos['pnl'] = (pos['current'] - pos['entry']) * pos['qty'] * multiplier

            if abs(old_current - pos['current']) > 0.01:
                self.changed.add('positions')

        if abs(old_unrealized - self.unrealized_pnl) > 0.01:
            self.changed.add('pnl')

        # Always update clock
        self.changed.add('clock')

    def clear_changed(self):
        """Clear change tracking"""
        self.changed.clear()


state = TradingState()
running = True
last_values = {}


# ============================================================================
# RENDERING UTILITIES
# ============================================================================

def move_cursor(row: int, col: int):
    """Move cursor to position"""
    print(f'\033[{row};{col}H', end='', flush=False)


def hide_cursor():
    """Hide cursor"""
    print('\033[?25l', end='', flush=False)


def show_cursor():
    """Show cursor"""
    print('\033[?25h', end='', flush=True)


def clear_screen():
    """Clear entire screen"""
    print('\033[2J\033[H', end='', flush=True)


def clear_line(row: int, col: int, length: int):
    """Clear specific area"""
    move_cursor(row, col)
    print(' ' * length, end='', flush=False)


def draw_text(row: int, col: int, text: str, key: str = None):
    """Draw text only if changed"""
    global last_values

    if key and last_values.get(key) == text:
        return  # No change, skip

    move_cursor(row, col)
    print(text, end='', flush=False)

    if key:
        last_values[key] = text


def draw_box_border(row: int, col: int, width: int, height: int, title: str, color: str):
    """Draw box border (only once at startup)"""
    # Top
    move_cursor(row, col)
    print(f"{color}╔{'═' * (width - 2)}╗{Colors.RESET}", flush=False)

    # Title
    if title:
        move_cursor(row, col + 2)
        print(f"{color}║{Colors.RESET} {Colors.BOLD}{title}{Colors.RESET} ", end='', flush=False)
        move_cursor(row, col + width - 1)
        print(f"{color}║{Colors.RESET}", flush=False)
        move_cursor(row + 1, col)
        print(f"{color}╠{'═' * (width - 2)}╣{Colors.RESET}", flush=False)
        content_start = row + 2
    else:
        content_start = row + 1

    # Sides
    for i in range(content_start, row + height - 1):
        move_cursor(i, col)
        print(f"{color}║{Colors.RESET}", end='', flush=False)
        move_cursor(i, col + width - 1)
        print(f"{color}║{Colors.RESET}", flush=False)

    # Bottom
    move_cursor(row + height - 1, col)
    print(f"{color}╚{'═' * (width - 2)}╝{Colors.RESET}", flush=False)


# ============================================================================
# UPDATE FUNCTIONS (Only update changed values)
# ============================================================================

def update_clock(row: int, col: int):
    """Update only the clock"""
    current_time = datetime.now().strftime("%I:%M:%S %p")
    text = f"{Colors.BOLD}🕐 {current_time}{Colors.RESET}"
    draw_text(row, col, text, key='clock')


def update_pnl(start_row: int, start_col: int):
    """Update only P&L values"""
    # Realized P&L
    realized_color = Colors.GREEN if state.realized_pnl >= 0 else Colors.RED
    text = f"{realized_color}{Colors.BOLD}${state.realized_pnl:>9.2f}{Colors.RESET}"
    draw_text(start_row + 3, start_col + 25, text, key='realized_pnl')

    # Unrealized P&L
    unrealized_color = Colors.GREEN if state.unrealized_pnl >= 0 else Colors.RED
    text = f"{unrealized_color}{Colors.BOLD}${state.unrealized_pnl:>9.2f}{Colors.RESET}"
    draw_text(start_row + 4, start_col + 25, text, key='unrealized_pnl')

    # Net P&L
    net_pnl = state.realized_pnl + state.unrealized_pnl
    net_color = Colors.GREEN if net_pnl >= 0 else Colors.RED
    text = f"{net_color}{Colors.BOLD}${net_pnl:>9.2f}{Colors.RESET}"
    draw_text(start_row + 5, start_col + 25, text, key='net_pnl')


def update_positions(start_row: int, start_col: int, width: int):
    """Update only position values"""
    if not state.positions:
        return

    for idx, pos in enumerate(state.positions):
        row = start_row + 4 + idx
        pnl_color = Colors.GREEN if pos['pnl'] >= 0 else Colors.RED

        # Only update current price and P&L
        price_text = f"{pos['current']:<10.2f}"
        draw_text(row, start_col + 23, price_text, key=f'pos_price_{idx}')

        pnl_text = f"{pnl_color}{pos['pnl']:>+8.2f}{Colors.RESET}"
        draw_text(row, start_col + 34, pnl_text, key=f'pos_pnl_{idx}')

    # Update total
    total_pnl = sum(p['pnl'] for p in state.positions)
    total_color = Colors.GREEN if total_pnl >= 0 else Colors.RED
    text = f"{Colors.BOLD}Total Unrealized: {total_color}${total_pnl:>8.2f}{Colors.RESET}"
    draw_text(start_row + 4 + len(state.positions) + 1, start_col + 3, text, key='pos_total')


def update_recent_activity(start_row: int, start_col: int):
    """Update activity log with timestamp"""
    now = datetime.now()
    events = [
        (now - timedelta(seconds=2), f"Position update: MNQ @ {state.positions[0]['current']:.2f}", Colors.CYAN),
        (now - timedelta(seconds=15), "✓ Max Contracts check passed (3/5)", Colors.GREEN),
        (now - timedelta(minutes=1), f"P&L: ${(state.realized_pnl + state.unrealized_pnl):.2f}", Colors.CYAN),
    ]

    for idx, (timestamp, message, color) in enumerate(events[:3]):
        time_str = timestamp.strftime("%H:%M:%S")
        text = f"{Colors.DIM}[{time_str}]{Colors.RESET} {color}{message}{Colors.RESET}"
        clear_line(start_row + 3 + idx, start_col + 3, 60)
        draw_text(start_row + 3 + idx, start_col + 3, text)


# ============================================================================
# INITIAL SCREEN DRAW (Only once)
# ============================================================================

def draw_initial_screen():
    """Draw the entire screen once at startup"""
    clear_screen()
    hide_cursor()

    height, width = get_terminal_size()
    col_width = width // 2 - 4
    left_col = 2
    right_col = width // 2 + 2

    # Header (static)
    title = "RISK MANAGER - LIVE TRADING DASHBOARD"
    title_col = (width - len(title)) // 2
    move_cursor(1, title_col)
    print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.RESET}", flush=False)

    current_date = datetime.now().strftime("%A, %B %d, %Y")
    date_col = (width - len(current_date)) // 2
    move_cursor(3, date_col)
    print(f"{Colors.DIM}{current_date}{Colors.RESET}", flush=False)

    # Draw all box borders
    draw_box_border(5, left_col, col_width, 8, "TRADING STATUS", Colors.GREEN)
    draw_box_border(14, left_col, col_width, 12, "TODAY'S P&L", Colors.CYAN)
    draw_box_border(27, left_col, col_width, 12, "OPEN POSITIONS", Colors.YELLOW)
    draw_box_border(5, right_col, col_width, 13, "RISK RULES STATUS", Colors.MAGENTA)
    draw_box_border(19, right_col, col_width, 10, "RECENT ACTIVITY", Colors.BLUE)

    # Status box (static content)
    move_cursor(8, left_col + 3)
    print(f"{Colors.GREEN}{Colors.BOLD}🟢 OK TO TRADE{Colors.RESET}", flush=False)
    move_cursor(9, left_col + 3)
    print(f"{Colors.GREEN}✓{Colors.RESET} Within session hours", flush=False)
    move_cursor(10, left_col + 3)
    print(f"{Colors.DIM}Session:{Colors.RESET} 09:30 AM - 04:00 PM", flush=False)

    # P&L labels (static)
    move_cursor(17, left_col + 3)
    print(f"{Colors.DIM}Realized P&L:{Colors.RESET}", flush=False)
    move_cursor(18, left_col + 3)
    print(f"{Colors.DIM}Unrealized P&L:{Colors.RESET}", flush=False)
    move_cursor(19, left_col + 3)
    print(f"{Colors.BOLD}Net P&L:{Colors.RESET}", flush=False)

    move_cursor(21, left_col + 3)
    print(f"{Colors.DIM}Daily Loss Limit: ${state.daily_loss_limit:,.2f}{Colors.RESET}", flush=False)
    move_cursor(24, left_col + 3)
    print(f"{Colors.DIM}Trades Today:{Colors.RESET} {Colors.CYAN}{Colors.BOLD}{state.trade_count}{Colors.RESET}", flush=False)

    # Positions header (static)
    move_cursor(30, left_col + 3)
    print(f"{Colors.BOLD}Symbol  Qty  Entry      Current    P&L{Colors.RESET}", flush=False)

    # Position rows (static parts)
    for idx, pos in enumerate(state.positions):
        row = 31 + idx
        qty_display = f"+{pos['qty']}" if pos['qty'] > 0 else str(pos['qty'])
        move_cursor(row, left_col + 3)
        print(f"{Colors.CYAN}{pos['symbol']:<7}{Colors.RESET} {qty_display:<4} {pos['entry']:<10.2f} ", end='', flush=False)

    # Risk rules (static)
    move_cursor(8, right_col + 3)
    print(f"{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Max Contracts{Colors.RESET}", flush=False)
    move_cursor(9, right_col + 5)
    print(f"{state.current_contracts}/{state.max_contracts} contracts", flush=False)

    move_cursor(11, right_col + 3)
    print(f"{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Daily Loss Limit{Colors.RESET}", flush=False)
    move_cursor(12, right_col + 5)
    print(f"${abs(state.realized_pnl):,.2f} / ${abs(state.daily_loss_limit):,.2f}", flush=False)

    move_cursor(14, right_col + 3)
    print(f"{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Trade Frequency{Colors.RESET}", flush=False)
    move_cursor(15, right_col + 5)
    print(f"2/3 trades/min", flush=False)

    # Footer (static)
    controls = f"{Colors.DIM}Press {Colors.RESET}{Colors.BOLD}Q{Colors.RESET}{Colors.DIM} to quit  |  Updates every 500ms{Colors.RESET}"
    move_cursor(height - 2, 10)
    print(controls, flush=False)

    # Initial flush
    sys.stdout.flush()


def get_terminal_size():
    """Get terminal size"""
    try:
        size = os.get_terminal_size()
        return size.lines, size.columns
    except:
        return 40, 120


# ============================================================================
# UPDATE LOOP (Only changed values)
# ============================================================================

def update_changed_values():
    """Update only what changed"""
    height, width = get_terminal_size()
    col_width = width // 2 - 4
    left_col = 2
    right_col = width // 2 + 2

    # Always update clock
    clock_col = (width - 20) // 2
    update_clock(2, clock_col)

    # Update P&L if changed
    if 'pnl' in state.changed:
        update_pnl(14, left_col)

    # Update positions if changed
    if 'positions' in state.changed:
        update_positions(27, left_col, col_width)

    # Update activity every update
    update_recent_activity(19, right_col)

    # Flush all updates at once
    sys.stdout.flush()


# ============================================================================
# BACKGROUND THREADS
# ============================================================================

def tick_thread():
    """Market simulation"""
    while running:
        state.simulate_tick()
        time.sleep(0.5)  # Tick every 500ms


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


# ============================================================================
# MAIN
# ============================================================================

def main():
    global running

    import tty
    import termios

    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())

        # Draw entire screen ONCE
        draw_initial_screen()

        # Start background threads
        market = threading.Thread(target=tick_thread, daemon=True)
        user_input = threading.Thread(target=input_thread, daemon=True)
        market.start()
        user_input.start()

        # Main loop - only update changed values
        while running:
            update_changed_values()
            state.clear_changed()
            time.sleep(0.5)  # Update display every 500ms

    except KeyboardInterrupt:
        running = False

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        show_cursor()
        clear_screen()
        print(f"\n{Colors.CYAN}Trading dashboard closed.{Colors.RESET}\n")


if __name__ == "__main__":
    main()
