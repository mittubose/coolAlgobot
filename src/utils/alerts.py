"""
Alert System
Send notifications via Telegram and Email
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
import logging

try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    Bot = None
    TelegramError = Exception


class AlertSystem:
    """Handles sending alerts via multiple channels"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize alert system

        Args:
            config: Alert configuration
        """
        self.config = config
        self.logger = logging.getLogger('alerts')

        # Setup Telegram
        self.telegram_enabled = False
        if TELEGRAM_AVAILABLE and config.get('telegram', {}).get('enabled', False):
            try:
                bot_token = config['telegram'].get('bot_token')
                self.chat_id = config['telegram'].get('chat_id')

                if bot_token and self.chat_id:
                    self.telegram_bot = Bot(token=bot_token)
                    self.telegram_enabled = True
                    self.logger.info("Telegram alerts enabled")
                else:
                    self.logger.warning("Telegram credentials missing")
            except Exception as e:
                self.logger.error(f"Failed to initialize Telegram: {e}")
        elif not TELEGRAM_AVAILABLE:
            self.logger.warning("python-telegram-bot not installed. Install with: pip install python-telegram-bot")

        # Setup Email
        self.email_enabled = config.get('email', {}).get('enabled', False)
        if self.email_enabled:
            self.email_config = config['email']
            self.logger.info("Email alerts enabled")

    def send_alert(self, title: str, message: str, level: str = 'info'):
        """
        Send alert through all enabled channels

        Args:
            title: Alert title
            message: Alert message
            level: Alert level (info, warning, error, critical)
        """
        formatted_message = f"**{title}**\n\n{message}"

        # Send to Telegram
        if self.telegram_enabled:
            self._send_telegram(formatted_message)

        # Send to Email (only for errors)
        if self.email_enabled and level in ['error', 'critical']:
            self._send_email(title, message)

    def send_trade_alert(self, trade_data: Dict[str, Any]):
        """Send alert for trade execution"""
        if not self.config.get('telegram', {}).get('send_on_trade', True):
            return

        action = trade_data.get('action', 'TRADE')
        symbol = trade_data.get('symbol', 'UNKNOWN')
        quantity = trade_data.get('quantity', 0)
        price = trade_data.get('price', 0)
        pnl = trade_data.get('pnl', 0)

        message = f"""
🔔 Trade Executed

Symbol: {symbol}
Action: {action}
Quantity: {quantity}
Price: ₹{price:.2f}
"""
        if pnl != 0:
            emoji = "✅" if pnl > 0 else "❌"
            message += f"P&L: {emoji} ₹{pnl:.2f}\n"

        self.send_alert("Trade Alert", message, 'info')

    def send_error_alert(self, error_message: str, error_data: Dict[str, Any] = None):
        """Send alert for errors"""
        if not self.config.get('telegram', {}).get('send_on_error', True):
            return

        message = f"❌ Error Occurred\n\n{error_message}"

        if error_data:
            message += "\n\nDetails:\n"
            for key, value in error_data.items():
                message += f"• {key}: {value}\n"

        self.send_alert("Error Alert", message, 'error')

    def send_daily_summary(self, summary_data: Dict[str, Any]):
        """Send daily trading summary"""
        if not self.config.get('telegram', {}).get('send_daily_summary', True):
            return

        total_trades = summary_data.get('total_trades', 0)
        winning_trades = summary_data.get('winning_trades', 0)
        losing_trades = summary_data.get('losing_trades', 0)
        total_pnl = summary_data.get('total_pnl', 0)
        win_rate = summary_data.get('win_rate', 0)

        emoji = "📈" if total_pnl > 0 else "📉" if total_pnl < 0 else "➡️"

        message = f"""
📊 Daily Trading Summary

{emoji} Total P&L: ₹{total_pnl:.2f}

Total Trades: {total_trades}
Winning: {winning_trades} ✅
Losing: {losing_trades} ❌
Win Rate: {win_rate:.1f}%

---
End of Day Report
"""
        self.send_alert("Daily Summary", message, 'info')

    def send_risk_alert(self, alert_type: str, message: str):
        """Send risk management alert"""
        if not self.config.get('telegram', {}).get('send_on_daily_loss_warning', True):
            return

        full_message = f"⚠️ Risk Alert: {alert_type}\n\n{message}"
        self.send_alert("Risk Warning", full_message, 'warning')

    def _send_telegram(self, message: str):
        """Send message via Telegram"""
        try:
            self.telegram_bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except TelegramError as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error sending Telegram: {e}")

    def _send_email(self, subject: str, body: str):
        """Send email alert"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[Scalping Bot] {subject}"
            msg['From'] = self.email_config['from_email']
            msg['To'] = self.email_config['to_email']

            # Create plain text and HTML versions
            text_part = MIMEText(body, 'plain')
            html_part = MIMEText(f"<html><body><pre>{body}</pre></body></html>", 'html')

            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(
                self.email_config['smtp_server'],
                self.email_config['smtp_port']
            ) as server:
                if self.email_config.get('use_tls', True):
                    server.starttls()

                server.login(
                    self.email_config['from_email'],
                    self.email_config['password']
                )
                server.send_message(msg)

            self.logger.info(f"Email sent: {subject}")

        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")


# Global alert system instance
_alert_system = None


def setup_alerts(config: Dict[str, Any]) -> AlertSystem:
    """Setup global alert system"""
    global _alert_system
    _alert_system = AlertSystem(config)
    return _alert_system


def get_alert_system() -> AlertSystem:
    """Get global alert system instance"""
    return _alert_system
