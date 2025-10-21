#!/usr/bin/env python3
"""
MINIMAL VIEW - Performance Focused
Perfect for: Distraction-free trading, scalpers who need focus

Features:
- Giant P&L display (main focus)
- Minimal distractions
- Essential info only
- Clean, simple layout
- Quick glance metrics
- Bottom hotkeys

NO DEPENDENCIES
"""

import os
import sys
import time
import threading
from datetime import datetime


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


class State:
    def __init__(self):
        self.net_pnl = 275.50
        self.realized_pnl = 155.50
        self.unrealized_pnl = 120.00

        self.trades_today = 8
        self.win_rate = 62.5
        self.biggest_win = 125.00
        self.biggest_loss = -85.00

        self.daily_goal = 500.00
        self.risk_limit = -500.00


state = State()
running = True
last_values = {}


def move_cursor(row, col):
    print(f'\033[{row};{col}H', end='', flush=False)


def hide_cursor():
    print('\033[?25l', end='', flush=False)


def show_cursor():
    print('\033[?25h', end='', flush=True)


def clear_screen():
    print('\033[2J\033[H', end='', flush=True)


def center_text(text, width):
    """Center text in given width"""
    lines = text.split('\n')
    centered = []
    for line in lines:
        # Remove color codes for length calculation
        clean_line = line
        for code in [Colors.RESET, Colors.WHITE, Colors.GRAY, Colors.BLUE, Colors.CYAN,
                     Colors.YELLOW, Colors.GREEN, Colors.MAGENTA, Colors.RED, Colors.BOLD, Colors.DIM]:
            clean_line = clean_line.replace(code, '')

        padding = (width - len(clean_line)) // 2
        centered.append(' ' * padding + line)
    return '\n'.join(centered)


def draw_giant_pnl(start_row, width):
    """Giant centered P&L display"""
    pnl_color = Colors.GREEN if state.net_pnl >= 0 else Colors.RED
    sign = "+" if state.net_pnl >= 0 else ""

    # Giant ASCII art numbers
    pnl_display = f"""
{pnl_color}{Colors.BOLD}
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                          ┃
┃     NET P&L TODAY        ┃
┃                          ┃
┃   {sign}${abs(state.net_pnl):.2f}         ┃
┃                          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛
{Colors.RESET}
    """

    centered = center_text(pnl_display.strip(), width)
    for idx, line in enumerate(centered.split('\n')):
        move_cursor(start_row + idx, 1)
        print(line, flush=False)


def draw_goal_progress(start_row, width):
    """Daily goal progress bar"""
    progress_pct = (state.net_pnl / state.daily_goal) * 100
    risk_pct = abs(state.net_pnl / state.risk_limit) * 100 if state.net_pnl < 0 else 0

    # Goal bar
    bar_width = 60
    filled = int(bar_width * min(1.0, abs(progress_pct) / 100))

    if state.net_pnl >= 0:
        color = Colors.GREEN
        label = "GOAL PROGRESS"
    else:
        color = Colors.RED
        label = "RISK USED"

    move_cursor(start_row, (width - bar_width) // 2)
    print(f"{Colors.DIM}{label}{Colors.RESET}", flush=False)

    move_cursor(start_row + 1, (width - bar_width) // 2)
    bar = f"{color}{'█' * filled}{Colors.DIM}{'░' * (bar_width - filled)}{Colors.RESET}"
    print(bar, flush=False)

    move_cursor(start_row + 2, (width - bar_width) // 2)
    if state.net_pnl >= 0:
        print(f"{Colors.DIM}${state.net_pnl:.2f} / ${state.daily_goal:.2f} ({progress_pct:.1f}%){Colors.RESET}", flush=False)
    else:
        print(f"{Colors.DIM}${abs(state.net_pnl):.2f} / ${abs(state.risk_limit):.2f} ({risk_pct:.1f}%){Colors.RESET}", flush=False)


def draw_breakdown(start_row, width):
    """P&L breakdown"""
    content_width = 40

    move_cursor(start_row, (width - content_width) // 2)
    realized_color = Colors.GREEN if state.realized_pnl >= 0 else Colors.RED
    print(f"{Colors.DIM}Realized:{Colors.RESET}   {realized_color}${state.realized_pnl:>+10.2f}{Colors.RESET}", flush=False)

    move_cursor(start_row + 1, (width - content_width) // 2)
    unrealized_color = Colors.GREEN if state.unrealized_pnl >= 0 else Colors.RED
    print(f"{Colors.DIM}Unrealized:{Colors.RESET} {unrealized_color}${state.unrealized_pnl:>+10.2f}{Colors.RESET}", flush=False)


def draw_quick_stats(start_row, width):
    """Essential stats"""
    content_width = 60

    # Trades
    move_cursor(start_row, (width - content_width) // 2)
    print(f"{Colors.CYAN}Trades:{Colors.RESET} {state.trades_today}", flush=False)

    # Win rate
    move_cursor(start_row, (width - content_width) // 2 + 20)
    wr_color = Colors.GREEN if state.win_rate >= 60 else Colors.YELLOW if state.win_rate >= 50 else Colors.RED
    print(f"{Colors.CYAN}Win Rate:{Colors.RESET} {wr_color}{state.win_rate:.1f}%{Colors.RESET}", flush=False)

    # Best/Worst
    move_cursor(start_row + 2, (width - content_width) // 2)
    print(f"{Colors.GREEN}Best:{Colors.RESET} ${state.biggest_win:.2f}", flush=False)

    move_cursor(start_row + 2, (width - content_width) // 2 + 20)
    print(f"{Colors.RED}Worst:{Colors.RESET} ${state.biggest_loss:.2f}", flush=False)


def draw_clock(start_row, width):
    """Centered clock"""
    current_time = datetime.now().strftime("%I:%M:%S %p")
    move_cursor(start_row, (width - len(current_time)) // 2)
    print(f"{Colors.BOLD}{Colors.CYAN}{current_time}{Colors.RESET}", flush=False)


def draw_hotkeys(row, width):
    """Bottom hotkeys"""
    hotkeys = f"{Colors.DIM}[R] Reset Day  |  [D] Details  |  [H] History  |  [Q] Quit{Colors.RESET}"

    # Remove color codes for centering
    clean = hotkeys
    for code in [Colors.RESET, Colors.DIM, Colors.BOLD]:
        clean = clean.replace(code, '')

    move_cursor(row, (width - len(clean)) // 2)
    print(hotkeys, flush=False)


def draw_screen():
    """Draw complete minimal view"""
    clear_screen()
    hide_cursor()

    try:
        height, width = os.get_terminal_size().lines, os.get_terminal_size().columns
    except:
        height, width = 40, 120

    # Clock at top
    draw_clock(2, width)

    # Giant P&L (centered)
    draw_giant_pnl(5, width)

    # Breakdown
    draw_breakdown(15, width)

    # Goal progress
    draw_goal_progress(18, width)

    # Quick stats
    draw_quick_stats(22, width)

    # Separator
    move_cursor(26, (width - 60) // 2)
    print(f"{Colors.DIM}{'─' * 60}{Colors.RESET}", flush=False)

    # Motivational message based on P&L
    move_cursor(28, 1)
    if state.net_pnl >= state.daily_goal:
        msg = f"{Colors.GREEN}{Colors.BOLD}🎯 DAILY GOAL ACHIEVED! Consider locking in profits.{Colors.RESET}"
    elif state.net_pnl > 0:
        msg = f"{Colors.GREEN}📈 Positive day - keep the momentum!{Colors.RESET}"
    elif state.net_pnl > state.risk_limit:
        msg = f"{Colors.YELLOW}⚠️  In the red - trade carefully{Colors.RESET}"
    else:
        msg = f"{Colors.RED}🛑 Approaching risk limit - consider stopping{Colors.RESET}"

    centered_msg = center_text(msg, width)
    print(centered_msg, flush=False)

    # Hotkeys
    draw_hotkeys(height - 2, width)

    sys.stdout.flush()


def tick_thread():
    """Update data"""
    import random
    while running:
        # Simulate small P&L changes
        state.unrealized_pnl += random.uniform(-2, 2)
        state.net_pnl = state.realized_pnl + state.unrealized_pnl

        time.sleep(0.5)


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
            time.sleep(0.5)

    except KeyboardInterrupt:
        running = False

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        show_cursor()
        clear_screen()
        print(f"\n{Colors.CYAN}Minimal view closed.{Colors.RESET}\n")


if __name__ == "__main__":
    main()
