#!/usr/bin/env python3
"""
Scalping Bot Dashboard Launcher
Launch the web dashboard for easy monitoring and control
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.dashboard.app import run_dashboard

if __name__ == '__main__':
    run_dashboard(host='0.0.0.0', port=8050, debug=False)
