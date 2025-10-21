#!/usr/bin/env python3
"""
SPLIT-SCREEN VIEW - Charts + Metrics
Perfect for: Technical traders, chart watchers

Features:
- ASCII price chart (left half)
- Live metrics and stats (right half)
- Dual-pane layout
- Chart indicators (SMA, volume)
- Position overlay on chart
- Bottom menu bar

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
        # Price history for chart
        self.prices = deque(maxlen=50)
        self.volumes = deque(maxlen=50)

        # Initialize with some data
        base_price = 21000.0
        for i in range(50):
            self.prices.append(base_price + (i * 0.5))
            self.volumes.append(15 + (i % 10))

        # Current metrics
        self.current_price = 21025.0
        self.high = 21030.0
        self.low = 21000.0
        self.volume = 1245
        self.sma_20 = 21012.5

        # Positions
        self.entry_price = 21005.0
        self.position_size = 2
        self.unrealized_pnl = 400.00

        # Stats
        self.realized_pnl = -125.50
        self.trades_today = 8
        self.win_rate = 62.5


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


def draw_price_chart(start_row, start_col, width, height):
    """ASCII price chart"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}MNQ - 1 MINUTE CHART{Colors.RESET}", flush=False)

    prices = list(state.prices)[-width:]
    if len(prices) < 2:
        return

    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price if max_price != min_price else 1

    # Draw price scale on left
    move_cursor(start_row + 2, start_col)
    print(f"{Colors.DIM}{max_price:>8.2f}─{Colors.RESET}", flush=False)

    move_cursor(start_row + 2 + height // 2, start_col)
    mid_price = (max_price + min_price) / 2
    print(f"{Colors.DIM}{mid_price:>8.2f}─{Colors.RESET}", flush=False)

    move_cursor(start_row + 2 + height - 1, start_col)
    print(f"{Colors.DIM}{min_price:>8.2f}─{Colors.RESET}", flush=False)

    # Draw chart area
    chart_start_col = start_col + 10

    # Draw candlestick-style bars
    for col_idx, price in enumerate(prices):
        if col_idx >= width - 10:
            break

        # Normalize price to chart height
        normalized = (price - min_price) / price_range
        bar_row = start_row + 2 + height - 1 - int(normalized * (height - 1))

        # Color based on trend
        if col_idx > 0:
            color = Colors.GREEN if price >= prices[col_idx - 1] else Colors.RED
        else:
            color = Colors.CYAN

        move_cursor(bar_row, chart_start_col + col_idx)
        print(f"{color}│{Colors.RESET}", flush=False)

    # Draw entry line if we have a position
    if state.position_size > 0:
        entry_normalized = (state.entry_price - min_price) / price_range
        entry_row = start_row + 2 + height - 1 - int(entry_normalized * (height - 1))

        move_cursor(entry_row, chart_start_col)
        print(f"{Colors.YELLOW}{'─' * (width - 10)} ENTRY{Colors.RESET}", flush=False)

    # Draw SMA line
    sma_normalized = (state.sma_20 - min_price) / price_range
    sma_row = start_row + 2 + height - 1 - int(sma_normalized * (height - 1))

    move_cursor(sma_row, chart_start_col)
    print(f"{Colors.MAGENTA}{'·' * (width - 10)} SMA20{Colors.RESET}", flush=False)

    # Time axis
    move_cursor(start_row + 2 + height, start_col + 10)
    now = datetime.now()
    start_time = now - timedelta(minutes=50)
    time_labels = f"{Colors.DIM}{start_time.strftime('%H:%M')}{'─' * (width - 25)}{now.strftime('%H:%M')}{Colors.RESET}"
    print(time_labels, flush=False)


def draw_volume_bars(start_row, start_col, width, height):
    """Volume bars below chart"""
    move_cursor(start_row, start_col)
    print(f"{Colors.DIM}Volume{Colors.RESET}", flush=False)

    volumes = list(state.volumes)[-width:]
    if not volumes:
        return

    max_vol = max(volumes)

    for col_idx, vol in enumerate(volumes):
        if col_idx >= width - 10:
            break

        # Normalize volume to bar height
        normalized = vol / max_vol if max_vol > 0 else 0
        bar_height = int(normalized * height)

        # Draw from bottom up
        for h in range(bar_height):
            row = start_row + height - h
            move_cursor(row, start_col + 10 + col_idx)
            print(f"{Colors.CYAN}▄{Colors.RESET}", flush=False)


def draw_metrics_panel(start_row, start_col):
    """Right panel with live metrics"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}LIVE METRICS{Colors.RESET}", flush=False)

    # Current price
    move_cursor(start_row + 2, start_col)
    price_color = Colors.GREEN if state.current_price >= state.sma_20 else Colors.RED
    print(f"{Colors.BOLD}Current Price{Colors.RESET}", flush=False)
    move_cursor(start_row + 3, start_col)
    print(f"{price_color}{Colors.BOLD}${state.current_price:.2f}{Colors.RESET}", flush=False)

    # High/Low
    move_cursor(start_row + 5, start_col)
    print(f"{Colors.DIM}High:{Colors.RESET} {Colors.GREEN}${state.high:.2f}{Colors.RESET}", flush=False)
    move_cursor(start_row + 6, start_col)
    print(f"{Colors.DIM}Low:{Colors.RESET}  {Colors.RED}${state.low:.2f}{Colors.RESET}", flush=False)

    # Range
    move_cursor(start_row + 7, start_col)
    range_val = state.high - state.low
    print(f"{Colors.DIM}Range:{Colors.RESET} ${range_val:.2f}", flush=False)

    # Volume
    move_cursor(start_row + 9, start_col)
    print(f"{Colors.BOLD}Volume{Colors.RESET}", flush=False)
    move_cursor(start_row + 10, start_col)
    print(f"{Colors.CYAN}{state.volume:,}{Colors.RESET}", flush=False)

    # Indicators
    move_cursor(start_row + 12, start_col)
    print(f"{Colors.BOLD}Indicators{Colors.RESET}", flush=False)
    move_cursor(start_row + 13, start_col)
    print(f"{Colors.MAGENTA}SMA 20:{Colors.RESET} ${state.sma_20:.2f}", flush=False)


def draw_position_panel(start_row, start_col):
    """Position information panel"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}POSITION{Colors.RESET}", flush=False)

    if state.position_size > 0:
        # Entry
        move_cursor(start_row + 2, start_col)
        print(f"{Colors.DIM}Entry:{Colors.RESET} ${state.entry_price:.2f}", flush=False)

        # Size
        move_cursor(start_row + 3, start_col)
        print(f"{Colors.DIM}Size:{Colors.RESET} {Colors.GREEN}+{state.position_size}{Colors.RESET} contracts", flush=False)

        # Unrealized P&L
        move_cursor(start_row + 4, start_col)
        pnl_color = Colors.GREEN if state.unrealized_pnl >= 0 else Colors.RED
        print(f"{Colors.BOLD}Unrealized:{Colors.RESET} {pnl_color}${state.unrealized_pnl:+.2f}{Colors.RESET}", flush=False)

        # P&L %
        move_cursor(start_row + 5, start_col)
        pnl_pct = (state.unrealized_pnl / (state.entry_price * state.position_size * 20)) * 100
        print(f"{Colors.DIM}Return:{Colors.RESET} {pnl_color}{pnl_pct:+.2f}%{Colors.RESET}", flush=False)

    else:
        move_cursor(start_row + 2, start_col)
        print(f"{Colors.GRAY}No open position{Colors.RESET}", flush=False)


def draw_stats_panel(start_row, start_col):
    """Trading statistics panel"""
    move_cursor(start_row, start_col)
    print(f"{Colors.BOLD}TODAY'S STATS{Colors.RESET}", flush=False)

    # Realized P&L
    move_cursor(start_row + 2, start_col)
    real_color = Colors.GREEN if state.realized_pnl >= 0 else Colors.RED
    print(f"{Colors.DIM}Realized P&L:{Colors.RESET} {real_color}${state.realized_pnl:+.2f}{Colors.RESET}", flush=False)

    # Trades
    move_cursor(start_row + 3, start_col)
    print(f"{Colors.DIM}Trades:{Colors.RESET} {Colors.CYAN}{state.trades_today}{Colors.RESET}", flush=False)

    # Win rate
    move_cursor(start_row + 4, start_col)
    wr_color = Colors.GREEN if state.win_rate >= 60 else Colors.YELLOW if state.win_rate >= 50 else Colors.RED
    print(f"{Colors.DIM}Win Rate:{Colors.RESET} {wr_color}{state.win_rate:.1f}%{Colors.RESET}", flush=False)


def draw_menu(row, col):
    """Bottom menu bar"""
    menu = (f"{Colors.CYAN}[1]{Colors.RESET} Change Symbol  "
            f"{Colors.CYAN}[2]{Colors.RESET} Timeframe  "
            f"{Colors.CYAN}[3]{Colors.RESET} Indicators  "
            f"{Colors.CYAN}[R]{Colors.RESET} Refresh  "
            f"{Colors.RED}[Q]{Colors.RESET} Quit")

    move_cursor(row, col)
    print(menu, flush=False)


def draw_screen():
    """Draw complete split-screen view"""
    clear_screen()
    hide_cursor()

    try:
        height, width = os.get_terminal_size().lines, os.get_terminal_size().columns
    except:
        height, width = 40, 120

    # Header
    move_cursor(1, 2)
    print(f"{Colors.BOLD}{Colors.CYAN}═══ SPLIT-SCREEN VIEW ═══{Colors.RESET} "
          f"{Colors.DIM}{datetime.now().strftime('%I:%M:%S %p')}{Colors.RESET}", flush=False)

    # Split screen in half
    mid_col = width // 2

    # Left side - Chart
    chart_height = 15
    draw_price_chart(3, 2, mid_col - 4, chart_height)
    draw_volume_bars(3 + chart_height + 2, 2, mid_col - 4, 4)

    # Right side - Metrics
    draw_metrics_panel(3, mid_col + 2)
    draw_position_panel(17, mid_col + 2)
    draw_stats_panel(25, mid_col + 2)

    # Footer
    draw_menu(height - 1, 2)

    sys.stdout.flush()


def tick_thread():
    """Update market data"""
    import random
    while running:
        # Update price
        state.current_price += random.uniform(-2, 2)
        state.prices.append(state.current_price)

        # Update high/low
        state.high = max(state.high, state.current_price)
        state.low = min(state.low, state.current_price)

        # Update volume
        state.volume += random.randint(1, 10)
        state.volumes.append(state.volume % 30 + 10)

        # Update SMA
        if len(state.prices) >= 20:
            state.sma_20 = sum(list(state.prices)[-20:]) / 20

        # Update unrealized P&L
        if state.position_size > 0:
            state.unrealized_pnl = (state.current_price - state.entry_price) * state.position_size * 20

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
        print(f"\n{Colors.CYAN}Split-screen view closed.{Colors.RESET}\n")


if __name__ == "__main__":
    main()
