# Trader Dashboard Layouts - Complete Guide

This document provides an overview of all 5 trader dashboard layouts designed for active day trading. Each layout is optimized for different trading styles and information preferences.

## Quick Reference

| Layout | File | Best For | Key Features |
|--------|------|----------|--------------|
| **Compact** | `trader-compact.py` | All-in-one view | Everything at a glance, sparklines, risk gauges |
| **Heatmap** | `trader-heatmap.py` | Risk-conscious traders | Visual risk zones, color-coded heat maps |
| **Order Flow** | `trader-orderflow.py` | Execution quality focus | Order book, fill analysis, slippage tracking |
| **Split-Screen** | `trader-splitscreen.py` | Chart watchers | ASCII charts + live metrics dual-pane |
| **Minimal** | `trader-minimal.py` | Distraction-free trading | Giant P&L, goal progress, essential stats only |

---

## 1. Compact View (`trader-compact.py`)

**Perfect for:** Traders who want all information visible at once without switching screens.

### Features
- **P&L Summary with Sparklines** - Historical trend visualization
- **Open Positions Table** - Live prices and position P&L
- **Risk Limit Gauges** - Visual bars for daily loss, contracts, trade frequency
- **Session Countdown** - Time remaining in trading session
- **Win Rate & Trade Statistics** - Performance metrics
- **Interactive Menu Bar** - Bottom hotkeys for quick actions

### Layout
```
┌─────────────────────────────────────────────────┐
│  P&L SUMMARY                                    │
│  ▁▂▃▄▅▆▇ Sparkline trend                       │
├─────────────────────────────────────────────────┤
│  POSITIONS                                      │
│  Symbol  Qty  Entry    Current   P&L            │
├─────────────────────────────────────────────────┤
│  RISK GAUGES                                    │
│  Daily Loss:  ██████░░░░░░░░░ 45.2%            │
│  Contracts:   ███░░░░░░░░░░░░░ 60.0%           │
├─────────────────────────────────────────────────┤
│  [1] Refresh  [2] Reset  [3] Rules  [Q] Quit   │
└─────────────────────────────────────────────────┘
```

### Use Case
When you need to monitor positions, risk limits, and performance all in one screen without scrolling or switching views.

---

## 2. Heatmap View (`trader-heatmap.py`)

**Perfect for:** Risk-conscious traders who make decisions based on visual risk indicators.

### Features
- **Giant P&L Display** - Dominant visual element showing net P&L
- **Color-Coded Risk Zones** - Green/yellow/orange/red background colors
- **Risk Heat Gauges** - Visual bars that change color based on risk level
  - Dark Green (0-40%): Safe zone
  - Green (40-60%): Moderate
  - Yellow (60-75%): Elevated
  - Orange (75-90%): High
  - Red (90-100%): Critical
- **Position Heat Map** - Individual position risk scores
- **Alert Zone** - Real-time warnings for approaching limits
- **Quick Stats Carousel** - Rotating performance metrics

### Layout
```
┌─────────────────────────────────────────────────┐
│              NET P&L TODAY                      │
│                +$275.50                         │
├─────────────────────────────────────────────────┤
│  RISK HEAT MAP                                  │
│  Daily Loss Limit:                              │
│  ██████████████████░░░░░░░░░░░░░░ 49.1%        │
│                                                 │
│  POSITION RISK                                  │
│  MNQ  ████████████████████░░░░░░ 65% (+$85)    │
│  ES   ██████████░░░░░░░░░░░░░░░░ 35% (+$35)    │
├─────────────────────────────────────────────────┤
│  ⚠ ALERTS                                       │
│  • All systems normal                           │
└─────────────────────────────────────────────────┘
```

### Use Case
When visual risk management is your priority and you want instant color-coded feedback on your risk exposure.

---

## 3. Order Flow View (`trader-orderflow.py`)

**Perfect for:** Scalpers and active traders focused on execution quality and order book dynamics.

### Features
- **Real-time Order Book** - Live bid/ask ladder with size visualization
- **Spread Indicator** - Current bid-ask spread highlighted
- **Trade Execution Timeline** - Recent fills with quality metrics:
  - Entry price vs. fill price
  - Slippage tracking
  - Fill speed in milliseconds
- **Execution Quality Metrics**:
  - Average slippage
  - Average fill speed
  - Fill rate percentage
  - Slippage distribution
- **Active Positions with Levels** - Entry, current, target, stop prices
- **Bottom Menu** - Filter symbols, time range, export data

### Layout
```
┌──────────────────┬──────────────────────────────┐
│ ORDER BOOK       │  EXECUTION QUALITY           │
│                  │                              │
│ 21002.0  25 ASK  │  Avg Slippage: $0.125       │
│ 21001.5  20 ASK  │  Avg Fill Speed: 38.5ms     │
│ 21001.0  12 ASK  │  Fill Rate: 98.5%           │
│ ──── SPREAD ──── │                              │
│ 21000.5  15 BID  │  ACTIVE POSITIONS            │
│ 21000.0  22 BID  │  MNQ +2                      │
│ 20999.5  18 BID  │  Target:  21060.0            │
│                  │  Current: 21042.5 (+$400)    │
├──────────────────┤  Entry:   21000.5            │
│ EXECUTION LOG    │  Stop:    20990.0            │
│ 14:45:12 MNQ BUY │                              │
│ 2 @ 21000.5      │                              │
│ Fill: 21000.75   │                              │
│ Slip: 0.25  45ms │                              │
└──────────────────┴──────────────────────────────┘
│  [1] Filter  [2] Time  [3] Export  [Q] Quit    │
└─────────────────────────────────────────────────┘
```

### Use Case
When execution quality matters and you want detailed analysis of fills, slippage, and order book dynamics.

---

## 4. Split-Screen View (`trader-splitscreen.py`)

**Perfect for:** Technical traders who want price action charts alongside live metrics.

### Features
- **ASCII Price Chart** - Left panel with candlestick-style bars
  - Visual price movement over time
  - SMA 20 indicator overlay
  - Entry level marker for open positions
  - Time axis with start/end timestamps
- **Volume Bars** - Below price chart showing volume distribution
- **Live Metrics Panel** - Right panel with:
  - Current price (color-coded vs. SMA)
  - High/Low/Range
  - Volume
  - Technical indicators
- **Position Panel** - Entry, size, unrealized P&L, return %
- **Statistics Panel** - Realized P&L, trades, win rate
- **Bottom Menu** - Change symbol, timeframe, indicators

### Layout
```
┌─────────────────────────┬────────────────────┐
│ MNQ - 1 MINUTE CHART    │ LIVE METRICS       │
│                         │                    │
│ 21030─┐                 │ Current Price      │
│       │  │              │ $21,025.00         │
│       │  │ │            │                    │
│ 21015─┼──┼─SMA20        │ High: $21,030      │
│     │ │  │ │            │ Low:  $21,000      │
│ ─────┼─ENTRY            │ Range: $30.00      │
│     │ │  │ │            │                    │
│ 21000─┴──┴─┴─           │ Volume: 1,245      │
│ 09:30    10:20          │                    │
│                         ├────────────────────┤
│ Volume:                 │ POSITION           │
│ ▄▄▄ ▄▄▄▄▄ ▄▄            │                    │
│                         │ Entry: $21,005     │
│                         │ Size: +2 contracts │
│                         │ Unrealized: +$400  │
│                         │ Return: +1.90%     │
│                         ├────────────────────┤
│                         │ TODAY'S STATS      │
│                         │                    │
│                         │ Realized: +$155.50 │
│                         │ Trades: 8          │
│                         │ Win Rate: 62.5%    │
└─────────────────────────┴────────────────────┘
│  [1] Symbol  [2] Timeframe  [3] Indicators  [Q] Quit
└─────────────────────────────────────────────────────┘
```

### Use Case
When you want to watch price action and charts while keeping critical metrics visible in one integrated view.

---

## 5. Minimal View (`trader-minimal.py`)

**Perfect for:** Distraction-free trading when you need maximum focus on P&L performance.

### Features
- **Giant Centered P&L Display** - Dominant visual element
- **Goal Progress Bar** - Visual progress toward daily target
- **Risk Progress Bar** - Visual representation of risk usage (when negative)
- **P&L Breakdown** - Realized vs. unrealized split
- **Essential Stats Only** - Trades, win rate, best/worst trades
- **Motivational Messages** - Context-aware encouragement/warnings:
  - Goal achieved notification
  - Positive momentum message
  - Risk warning
  - Limit approaching alert
- **Centered Layout** - All elements centered for clean look
- **Minimal Hotkeys** - Bottom menu for essential actions

### Layout
```
                    02:45:30 PM

         ┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓
         ┃                          ┃
         ┃     NET P&L TODAY        ┃
         ┃                          ┃
         ┃       +$275.50           ┃
         ┃                          ┃
         ┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛

              Realized:   +$155.50
              Unrealized: +$120.00

                 GOAL PROGRESS
         ████████████████████████░░░░░░
         $275.50 / $500.00 (55.1%)

    Trades: 8        Win Rate: 62.5%

    Best: $125.00    Worst: -$85.00

    ──────────────────────────────────

      📈 Positive day - keep the momentum!

     [R] Reset  [D] Details  [H] History  [Q] Quit
```

### Use Case
When you want zero distractions and need to focus purely on P&L performance and progress toward goals.

---

## Technical Details

### Common Features (All Layouts)
- **Pure Python 3** - No external dependencies
- **ANSI Color Codes** - Professional color scheme
- **Smooth Updates** - No screen flickering
- **Change Tracking** - Only updates modified values
- **Threading** - Separate threads for market data, input, display
- **Raw Terminal Mode** - Immediate single-key input
- **WSL Compatible** - Works perfectly in Windows Subsystem for Linux

### Color Scheme (Semantic)
- **Blue** - Headers, authentication
- **Cyan** - Information, symbols
- **Green** - Profits, success, buy side
- **Red** - Losses, danger, sell side
- **Yellow** - Warnings, alerts
- **Magenta** - Indicators, special markers
- **Gray/Dim** - Secondary info, timestamps

### Running the Dashboards

```bash
# Make executable
chmod +x trader-*.py

# Run any layout
./trader-compact.py
./trader-heatmap.py
./trader-orderflow.py
./trader-splitscreen.py
./trader-minimal.py

# Or with python3
python3 trader-compact.py
```

### Keyboard Controls
- **Q** - Quit dashboard
- **R** - Refresh/Reset (where applicable)
- **1-9** - Menu actions (layout-specific)

---

## Choosing the Right Layout

### Decision Matrix

**Choose Compact if:**
- You want everything visible at once
- You monitor multiple metrics simultaneously
- You don't want to switch between screens

**Choose Heatmap if:**
- Visual risk management is your priority
- You respond well to color-coded alerts
- You want instant risk feedback

**Choose Order Flow if:**
- Execution quality is critical to your strategy
- You're a scalper or high-frequency trader
- You analyze order book depth
- You care about slippage and fill speed

**Choose Split-Screen if:**
- You're a technical trader who relies on charts
- You want price action and metrics together
- You use indicators like SMA
- You make decisions based on chart patterns

**Choose Minimal if:**
- You get distracted easily
- P&L performance is your only focus
- You prefer clean, simple interfaces
- You have a specific daily goal target

---

## Future Enhancements

Potential additions to these layouts:

1. **Real API Integration** - Connect to actual TopstepX API
2. **Multi-Symbol Support** - Track multiple instruments
3. **Alert Sounds** - Audio notifications for warnings
4. **Export Functionality** - Save performance data to CSV
5. **Custom Themes** - User-selectable color schemes
6. **Configurable Layouts** - Drag-and-drop panel arrangement
7. **Historical Replay** - Review past trading sessions
8. **Performance Analytics** - Deeper statistical analysis

---

## Performance Notes

All layouts are optimized for:
- **Low CPU usage** - Efficient rendering (< 3% CPU)
- **Low memory** - < 50MB RAM
- **Smooth updates** - 0.5-1 second refresh rates
- **Terminal compatibility** - Works in standard terminals

Tested on:
- WSL (Windows Subsystem for Linux)
- Linux native terminals
- macOS Terminal
- SSH sessions

---

## Support

For issues, questions, or feature requests related to these trader dashboards, please refer to the main project documentation.

**Remember:** These are visual demonstrations and mockups. They simulate market data and are designed to showcase different layout options for the Risk Manager trading system.
