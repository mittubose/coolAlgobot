#!/usr/bin/env python3
"""
Scalping Bot - Main Entry Point
Daily Scalping Algorithmic Trading Software for Zerodha

Usage:
    python main.py --help           Show help
    python main.py --setup          Run initial setup
    python main.py --auth           Authenticate with Zerodha
    python main.py --paper          Run in paper trading mode
    python main.py --live           Run in live trading mode (use with caution!)
    python main.py --backtest       Run backtesting
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.config_loader import ConfigLoader, get_config
from src.utils.logger import setup_logging, get_logger
from src.utils.alerts import setup_alerts
from src.auth.zerodha_auth import ZerodhaAuth


def show_banner():
    """Display welcome banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              📈  SCALPING BOT - v1.0.0  📉                   ║
║                                                               ║
║      Daily Scalping Algorithmic Trading Software             ║
║              for Zerodha Kite Connect                         ║
║                                                               ║
║  ⚠️  DISCLAIMER: Trading involves risk of loss.              ║
║      Always test thoroughly in paper mode first!             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def setup_wizard():
    """Interactive setup wizard for first-time users"""
    print("\n🚀 SCALPING BOT - SETUP WIZARD")
    print("="*60)
    print("\nThis wizard will help you configure the bot for first use.")
    print("\nStep 1: Configuration Files")
    print("-"*60)

    config_path = Path("config/config.yaml")
    secrets_path = Path("config/secrets.env")

    if config_path.exists():
        print("✅ config.yaml found")
    else:
        print("❌ config.yaml not found!")
        print("   Please ensure config/config.yaml exists")
        return False

    if not secrets_path.exists():
        example_path = Path("config/secrets.env.example")
        if example_path.exists():
            print("\n📝 Creating secrets.env from example...")
            import shutil
            shutil.copy(example_path, secrets_path)
            print("✅ Created config/secrets.env")
        else:
            print("❌ secrets.env.example not found!")
            return False

    print("\nStep 2: API Credentials")
    print("-"*60)
    print("\nYou need Zerodha Kite Connect API credentials:")
    print("1. Go to https://kite.trade")
    print("2. Login with your Zerodha account")
    print("3. Create a new app under 'Create App'")
    print("4. Copy the API Key and API Secret")
    print("\n5. Edit config/secrets.env and add:")
    print("   KITE_API_KEY=your_api_key")
    print("   KITE_API_SECRET=your_api_secret")

    input("\nPress Enter when you've updated secrets.env...")

    print("\nStep 3: Configuration")
    print("-"*60)
    print("\nReview and modify config/config.yaml:")
    print("• Set your trading capital")
    print("• Choose instruments to trade")
    print("• Configure risk parameters")
    print("• Enable/disable strategies")

    input("\nPress Enter when you've reviewed config.yaml...")

    print("\nStep 4: Authentication")
    print("-"*60)
    print("\nNext, run: python main.py --auth")
    print("This will authenticate with Zerodha and save your access token.")

    print("\n✅ Setup complete! Next steps:")
    print("   1. python main.py --auth      (authenticate)")
    print("   2. python main.py --paper     (test in paper mode)")
    print("   3. python main.py --live      (go live when ready)")

    return True


def run_authentication():
    """Run authentication flow"""
    show_banner()
    print("\n🔐 AUTHENTICATION")
    print("="*60)

    try:
        # Load configuration
        config = ConfigLoader()
        config.load()

        api_key = config.get('broker.api_key')
        api_secret = config.get('broker.api_secret')

        if not api_key or not api_secret:
            print("❌ Error: API credentials not found in config/secrets.env")
            print("\nPlease run: python main.py --setup")
            return False

        # Authenticate
        auth = ZerodhaAuth(api_key, api_secret)
        kite = auth.interactive_login()

        # Verify
        profile = kite.profile()
        print(f"\n✅ Successfully authenticated as: {profile['user_name']}")
        print(f"   Email: {profile['email']}")
        print(f"   User ID: {profile['user_id']}")

        print("\n✅ Authentication complete!")
        print("   Access token saved for future use.")
        print("\nNext steps:")
        print("   python main.py --paper    (start paper trading)")

        return True

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return False


def run_paper_trading():
    """Run paper trading mode"""
    show_banner()
    print("\n📝 PAPER TRADING MODE")
    print("="*60)
    print("\n⚠️  Note: Paper trading is simulated - no real money involved")
    print("\nThis feature is under development.")
    print("The bot will:")
    print("• Connect to live market data")
    print("• Generate trading signals")
    print("• Simulate order execution")
    print("• Track virtual P&L")
    print("\nPress Ctrl+C to stop")


def run_live_trading():
    """Run live trading mode"""
    show_banner()
    print("\n💰 LIVE TRADING MODE")
    print("="*60)
    print("\n⚠️  WARNING: This will trade with REAL MONEY!")
    print("\nBefore proceeding, ensure:")
    print("✓ You've tested extensively in paper mode")
    print("✓ You understand the risks involved")
    print("✓ You've reviewed your strategy configuration")
    print("✓ You have proper risk management in place")

    confirmation = input("\nType 'I UNDERSTAND THE RISKS' to continue: ")

    if confirmation != "I UNDERSTAND THE RISKS":
        print("\n❌ Live trading cancelled for safety")
        return False

    print("\n⚠️  Live trading feature is under development")
    return False


def run_backtest():
    """Run backtesting"""
    show_banner()
    print("\n📊 BACKTESTING MODE")
    print("="*60)
    print("\nThis feature is under development.")
    print("Backtesting will:")
    print("• Load historical data")
    print("• Simulate strategy execution")
    print("• Generate performance reports")


def show_help():
    """Display detailed help information"""
    help_text = """
╔═══════════════════════════════════════════════════════════════╗
║                    SCALPING BOT - HELP                        ║
╚═══════════════════════════════════════════════════════════════╝

GETTING STARTED
===============

1. First-time Setup:
   python main.py --setup

2. Authenticate with Zerodha:
   python main.py --auth

3. Start Paper Trading:
   python main.py --paper

4. Review Performance (when ready):
   python main.py --backtest

5. Go Live (use extreme caution):
   python main.py --live


COMMANDS
========

--setup         Run interactive setup wizard
--auth          Authenticate with Zerodha Kite Connect
--paper         Start paper trading (simulated)
--live          Start live trading (real money - use with caution!)
--backtest      Run strategy backtesting
--help          Show this help message


CONFIGURATION
=============

Configuration Files:
• config/config.yaml     - Main configuration
• config/secrets.env     - API credentials (keep secret!)

Key Settings:
• trading.mode           - 'paper' or 'live'
• trading.capital        - Starting capital
• instruments            - Stocks to trade
• strategies             - Trading strategies to use
• risk                   - Risk management parameters


DOCUMENTATION
=============

For detailed documentation, see:
• README.md              - Complete setup guide
• docs/FAQ.md            - Frequently asked questions
• docs/STRATEGY_GUIDE.md - Strategy configuration guide

Online Resources:
• Zerodha Kite Docs: https://kite.trade/docs/connect/v3/
• Support: GitHub Issues


IMPORTANT NOTES
===============

⚠️  Always test in paper mode before going live!
⚠️  Never share your API credentials or access tokens
⚠️  Keep your config/secrets.env file secure
⚠️  Review all trades and monitor performance regularly
⚠️  Understand SEBI regulations for algo trading


SAFETY FEATURES
===============

• Mandatory stop-loss on every trade
• Daily loss limits
• Maximum position size limits
• Circuit breakers for consecutive losses
• Emergency kill switch
• Comprehensive logging and audit trails


GETTING HELP
============

If you encounter issues:

1. Check docs/FAQ.md for common problems
2. Review logs in the logs/ directory
3. Verify your configuration in config/config.yaml
4. Ensure API credentials are correct
5. Check Zerodha API status

For bugs or feature requests:
Create an issue on GitHub


═══════════════════════════════════════════════════════════════

Happy Trading! 📈
Remember: Only trade what you can afford to lose.

═══════════════════════════════════════════════════════════════
"""
    print(help_text)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Scalping Bot - Daily Scalping Algorithmic Trading Software',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Use --help for detailed documentation'
    )

    parser.add_argument('--setup', action='store_true',
                        help='Run interactive setup wizard')
    parser.add_argument('--auth', action='store_true',
                        help='Authenticate with Zerodha')
    parser.add_argument('--paper', action='store_true',
                        help='Start paper trading mode')
    parser.add_argument('--live', action='store_true',
                        help='Start live trading mode')
    parser.add_argument('--backtest', action='store_true',
                        help='Run backtesting')
    parser.add_argument('--help-detailed', action='store_true',
                        help='Show detailed help')

    args = parser.parse_args()

    # Show detailed help
    if args.help_detailed or len(sys.argv) == 1:
        show_help()
        return

    # Run appropriate mode
    if args.setup:
        setup_wizard()
    elif args.auth:
        run_authentication()
    elif args.paper:
        run_paper_trading()
    elif args.live:
        run_live_trading()
    elif args.backtest:
        run_backtest()
    else:
        show_banner()
        print("\nUse --help-detailed for usage information")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting safely...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
