# Frontend Examples

This directory contains executable frontend examples for the Simple Risk Manager.

## Directory Structure

```
examples/
├── cli/
│   ├── trader/          # Trader-focused CLI interfaces
│   └── admin/           # Admin/setup CLI interfaces
├── gui/                 # Desktop GUI applications (tkinter, PyQt)
└── web/                 # Web-based interfaces (HTML/JavaScript)
```

## CLI Examples

### Trader Interfaces (`cli/trader/`)

Interactive terminal interfaces designed for traders:

- **trader-minimal.py** - Minimalist trader interface
- **trader-cli.py** - Full-featured trader CLI
- **trader-cli-smooth.py** - Smooth animations and transitions
- **trader-compact.py** - Compact layout for smaller screens
- **trader-heatmap.py** - Visual heatmap display
- **trader-orderflow.py** - Order flow visualization
- **trader-splitscreen.py** - Multi-panel split screen view
- **cli-interactive-demo.py** - Interactive demo with all features

### Admin Interfaces (`cli/admin/`)

Setup and configuration interfaces:

- **cli-clickable.py** - Interactive setup wizard with clickable menus
- **tui-dark-mode.py** - Terminal UI with dark mode theme

## GUI Examples

### Desktop Applications (`gui/`)

- **gui-dark-mode.py** - Full desktop GUI with dark mode (tkinter/PyQt)

## Web Examples

### Browser-Based Interfaces (`web/`)

- **web-gui-dark-mode.html** - Web-based GUI with dark theme

## Running Examples

All Python examples are executable. You can run them directly:

```bash
# From WSL/Linux terminal
./examples/cli/trader/trader-minimal.py

# Or drag and drop from Windows File Explorer into WSL terminal
# The file path will be automatically pasted

# Or run with python3
python3 examples/cli/trader/trader-minimal.py
```

### Requirements

Most CLI examples require:
```bash
pip install rich click
```

GUI examples may require additional packages:
```bash
pip install tkinter  # or PyQt5/PyQt6
```

## Documentation

For implementation guides and visual mockups, see the `/docs` directory:
- `docs/cli-visual-examples.md` - CLI design patterns
- `docs/trader-layouts-overview.md` - Trader interface layouts

## Notes

- All files use Unix (LF) line endings for WSL compatibility
- All Python files have executable permissions (`chmod +x`)
- Files can be drag-and-dropped from Windows File Explorer to WSL terminal
