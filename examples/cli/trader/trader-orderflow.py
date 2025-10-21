#!/usr/bin/env python3
"""
ORDER FLOW VIEW - Execution Quality Dashboard
Perfect for: Active day traders, scalpers, execution-focused

Features:
- Real-time order book visualization
- Trade execution timeline
- Entry/exit points tracking
- Fill quality metrics
- Slippage analysis
- Bottom action menu

NO DEPENDENCIES
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
from collections import deque


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
        # Order book
        self.bids = [(21000.5, 15), (21000.0, 22), (20999.5, 18)]
        self.asks = [(21001.0, 12), (21001.5, 20), (21002.0, 25)]

        # Recent trades
        self.trades = deque(maxlen=10)
        self.trades.append({
            "time": datetime.now() - timedelta(seconds=5),
            "symbol": "MNQ",
            "side": "BUY",
            "qty": 2,
            "price": 21000.5,
            "fill_price": 21000.75,
            "slippage": 0.25,
            "speed_ms": 45
        })
        self.trades.append({
            "time": datetime.now() - timedelta(seconds=25),
            "symbol": "ES",
            "side": "SELL",
            "qty": 1,
            "price": 5850.25,
            "fill_price": 5850.25,
            "slippage": 0.0,
            "speed_ms": 32
        })

        # Execution metrics
        self.avg_slippage = 0.125
        self.avg_fill_speed = 38.5
        self.fill_rate = 98.5
        self.total_executions = 14


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


def draw_order_book(start_row, start_col):
    """Order book ladder"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}ORDER BOOK - MNQ{Colors.RESET}", flush=False)

    # Header
    move_cursor(start_row + 2, start_col)
    print(f"{Colors.DIM}   Price      Size    |    Price      Size{Colors.RESET}", flush=False)

    # Asks (sell orders) - reversed so highest on top
    for idx, (price, size) in enumerate(reversed(state.asks)):
        row = start_row + 3 + idx
        move_cursor(row, start_col)
        print(f"{Colors.RED}{price:>10.2f}  {size:>4}{Colors.RESET}    |", flush=False)

    # Spread line
    move_cursor(start_row + 6, start_col)
    spread = state.asks[0][0] - state.bids[0][0]
    print(f"{Colors.YELLOW}{'─' * 20} SPREAD: ${spread:.2f} {'─' * 20}{Colors.RESET}", flush=False)

    # Bids (buy orders)
    for idx, (price, size) in enumerate(state.bids):
        row = start_row + 7 + idx
        move_cursor(row, start_col)
        print(f"{Colors.GREEN}{price:>10.2f}  {size:>4}{Colors.RESET}    |", flush=False)

        # Show bid visual bar on right side
        move_cursor(row, start_col + 28)
        bar_width = min(30, int(size * 1.5))
        print(f"{Colors.GREEN}{'█' * bar_width}{Colors.RESET}", flush=False)


def draw_execution_timeline(start_row, start_col):
    """Recent trade executions"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}EXECUTION TIMELINE{Colors.RESET}", flush=False)

    move_cursor(start_row + 2, start_col)
    print(f"{Colors.DIM}Time     Symbol Side  Qty  Entry     Fill      Slip    Speed{Colors.RESET}", flush=False)

    for idx, trade in enumerate(list(state.trades)[-8:]):
        row = start_row + 3 + idx
        time_str = trade['time'].strftime("%H:%M:%S")
        side_color = Colors.GREEN if trade['side'] == 'BUY' else Colors.RED
        slip_color = Colors.GREEN if trade['slippage'] == 0 else Colors.YELLOW if trade['slippage'] < 0.5 else Colors.RED
        speed_color = Colors.GREEN if trade['speed_ms'] < 50 else Colors.YELLOW if trade['speed_ms'] < 100 else Colors.RED

        move_cursor(row, start_col)
        print(f"{Colors.DIM}{time_str}{Colors.RESET} "
              f"{Colors.CYAN}{trade['symbol']:<6}{Colors.RESET} "
              f"{side_color}{trade['side']:<4}{Colors.RESET} "
              f"{trade['qty']:>3}  "
              f"{trade['price']:<9.2f} "
              f"{trade['fill_price']:<9.2f} "
              f"{slip_color}{trade['slippage']:>5.2f}{Colors.RESET}  "
              f"{speed_color}{trade['speed_ms']:>4.0f}ms{Colors.RESET}", flush=False)


def draw_execution_metrics(start_row, start_col):
    """Execution quality metrics"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}EXECUTION QUALITY{Colors.RESET}", flush=False)

    # Average slippage
    move_cursor(start_row + 2, start_col)
    slip_color = Colors.GREEN if state.avg_slippage < 0.2 else Colors.YELLOW if state.avg_slippage < 0.5 else Colors.RED
    print(f"{Colors.DIM}Avg Slippage:{Colors.RESET} {slip_color}${state.avg_slippage:.3f}{Colors.RESET}", flush=False)

    # Fill speed
    move_cursor(start_row + 3, start_col)
    speed_color = Colors.GREEN if state.avg_fill_speed < 50 else Colors.YELLOW if state.avg_fill_speed < 100 else Colors.RED
    print(f"{Colors.DIM}Avg Fill Speed:{Colors.RESET} {speed_color}{state.avg_fill_speed:.1f}ms{Colors.RESET}", flush=False)

    # Fill rate
    move_cursor(start_row + 4, start_col)
    rate_color = Colors.GREEN if state.fill_rate > 95 else Colors.YELLOW if state.fill_rate > 90 else Colors.RED
    print(f"{Colors.DIM}Fill Rate:{Colors.RESET} {rate_color}{state.fill_rate:.1f}%{Colors.RESET}", flush=False)

    # Total executions
    move_cursor(start_row + 5, start_col)
    print(f"{Colors.DIM}Total Executions:{Colors.RESET} {Colors.CYAN}{state.total_executions}{Colors.RESET}", flush=False)

    # Slippage distribution
    move_cursor(start_row + 7, start_col)
    print(f"{Colors.BOLD}Slippage Distribution{Colors.RESET}", flush=False)

    move_cursor(start_row + 8, start_col)
    print(f"{Colors.GREEN}█{Colors.RESET} Perfect (0): 6 trades", flush=False)

    move_cursor(start_row + 9, start_col)
    print(f"{Colors.YELLOW}█{Colors.RESET} Minor (<0.5): 7 trades", flush=False)

    move_cursor(start_row + 10, start_col)
    print(f"{Colors.RED}█{Colors.RESET} High (>0.5): 1 trade", flush=False)


def draw_position_markers(start_row, start_col):
    """Current positions with entry/exit markers"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}ACTIVE POSITIONS{Colors.RESET}", flush=False)

    positions = [
        {"symbol": "MNQ", "qty": 2, "entry": 21000.5, "current": 21042.5, "target": 21060.0, "stop": 20990.0},
        {"symbol": "ES", "qty": 1, "entry": 5850.25, "current": 5867.75, "target": 5875.0, "stop": 5845.0},
    ]

    for idx, pos in enumerate(positions):
        row = start_row + 2 + (idx * 5)

        # Symbol and qty
        move_cursor(row, start_col)
        print(f"{Colors.CYAN}{pos['symbol']}{Colors.RESET} {Colors.GREEN}+{pos['qty']}{Colors.RESET}", flush=False)

        # Price levels
        move_cursor(row + 1, start_col)
        print(f"  {Colors.GREEN}Target:{Colors.RESET}  {pos['target']:.2f}", flush=False)

        move_cursor(row + 2, start_col)
        pnl = (pos['current'] - pos['entry']) * pos['qty'] * (20 if 'MNQ' in pos['symbol'] else 50)
        pnl_color = Colors.GREEN if pnl >= 0 else Colors.RED
        print(f"  {Colors.CYAN}Current:{Colors.RESET} {pos['current']:.2f} {pnl_color}({pnl:+.2f}){Colors.RESET}", flush=False)

        move_cursor(row + 3, start_col)
        print(f"  {Colors.BLUE}Entry:{Colors.RESET}   {pos['entry']:.2f}", flush=False)

        move_cursor(row + 4, start_col)
        print(f"  {Colors.RED}Stop:{Colors.RESET}    {pos['stop']:.2f}", flush=False)


def draw_menu(row, col):
    """Bottom menu bar"""
    menu = (f"{Colors.CYAN}[1]{Colors.RESET} Filter Symbols  "
            f"{Colors.CYAN}[2]{Colors.RESET} Time Range  "
            f"{Colors.CYAN}[3]{Colors.RESET} Export Data  "
            f"{Colors.CYAN}[R]{Colors.RESET} Refresh  "
            f"{Colors.RED}[Q]{Colors.RESET} Quit")

    move_cursor(row, col)
    print(menu, flush=False)


def draw_screen():
    """Draw complete order flow view"""
    clear_screen()
    hide_cursor()

    # Header
    move_cursor(1, 2)
    print(f"{Colors.BOLD}{Colors.BLUE}═══ ORDER FLOW VIEW ═══{Colors.RESET} "
          f"{Colors.DIM}{datetime.now().strftime('%I:%M:%S %p')}{Colors.RESET}", flush=False)

    # Layout - 3 columns
    draw_order_book(3, 2)
    draw_execution_timeline(13, 2)
    draw_execution_metrics(3, 65)
    draw_position_markers(15, 65)

    # Footer
    try:
        height = os.get_terminal_size().lines
    except:
        height = 40

    draw_menu(height - 1, 2)

    sys.stdout.flush()


def tick_thread():
    """Update market data"""
    import random
    while running:
        # Update order book
        for i in range(len(state.bids)):
            state.bids[i] = (state.bids[i][0] + random.uniform(-0.5, 0.5),
                            max(5, state.bids[i][1] + random.randint(-3, 3)))

        for i in range(len(state.asks)):
            state.asks[i] = (state.asks[i][0] + random.uniform(-0.5, 0.5),
                            max(5, state.asks[i][1] + random.randint(-3, 3)))

        # Sort
        state.bids.sort(reverse=True, key=lambda x: x[0])
        state.asks.sort(key=lambda x: x[0])

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
        print(f"\n{Colors.BLUE}Order flow view closed.{Colors.RESET}\n")


if __name__ == "__main__":
    main()
