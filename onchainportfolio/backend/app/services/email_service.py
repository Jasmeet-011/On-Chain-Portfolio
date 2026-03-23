# backend/app/services/email_service.py - COMPLETE VERSION
"""
Email Service - Send email notifications for alerts
Supports: Price Alerts, Daily Digest, Weekly Summary, Milestones
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config import settings
from app.models.alert_models import (
    PriceAlertEmailData,
    DailyDigestEmailData,
    WeeklySummaryEmailData,
    MilestoneEmailData
)

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending email notifications.

    Supports multiple backends:
    - Console (development) - just logs emails
    - SendGrid (primary) - uses SendGrid Python SDK if SENDGRID_API_KEY is set
    - SMTP (fallback) - sends real emails via SMTP if SendGrid is not configured
    """

    def __init__(self):
        # Email configuration from settings (config-based, not raw os.getenv)
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email
        self.from_name = settings.from_name
        self.sendgrid_api_key = settings.sendgrid_api_key

        # Check if SendGrid is configured
        self.sendgrid_enabled = bool(self.sendgrid_api_key)

        # Check if SMTP is configured
        self.smtp_enabled = bool(self.smtp_host and self.smtp_user and self.smtp_password)

        if self.sendgrid_enabled:
            logger.info("[EMAIL] SendGrid configured — will use as primary sender")
        elif self.smtp_enabled:
            logger.info(f"[EMAIL] SMTP configured: {self.smtp_host}:{self.smtp_port}")
        else:
            logger.info("[EMAIL] No email transport configured — emails will be logged to console")

    # ============================================================
    # PRICE ALERT EMAILS
    # ============================================================

    def send_price_alert(self, data: PriceAlertEmailData) -> bool:
        """
        Send price alert notification email.

        Called when a token price crosses the user's target.
        """
        subject = f"🚨 Price Alert: {data.token_symbol} is now ${data.current_price:.2f}"

        # Determine if price went up or down
        direction = "above" if data.alert_type == "above" else "below"
        emoji = "📈" if data.alert_type == "above" else "📉"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 30px; }}
                .price-box {{ background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; }}
                .current-price {{ font-size: 36px; font-weight: bold; color: #1a1a2e; }}
                .target-price {{ color: #666; margin-top: 10px; }}
                .change {{ font-size: 14px; margin-top: 5px; }}
                .change.positive {{ color: #10b981; }}
                .change.negative {{ color: #ef4444; }}
                .details {{ background: #f8f9fa; border-radius: 8px; padding: 15px; margin: 20px 0; }}
                .details-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .details-row:last-child {{ border-bottom: none; }}
                .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; margin-top: 20px; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{emoji} Price Alert Triggered</h1>
                </div>
                <div class="content">
                    <p>Hi {data.user_name},</p>
                    <p>Your price alert for <strong>{data.token_symbol}</strong> has been triggered!</p>

                    <div class="price-box">
                        <div class="current-price">${data.current_price:.4f}</div>
                        <div class="target-price">Target: {direction} ${data.target_price:.4f}</div>
                        <div class="change {'positive' if data.change_percent >= 0 else 'negative'}">
                            24h Change: {'+' if data.change_percent >= 0 else ''}{data.change_percent:.2f}%
                        </div>
                    </div>

                    <div class="details">
                        <div class="details-row">
                            <span>Token</span>
                            <strong>{data.token_symbol}</strong>
                        </div>
                        <div class="details-row">
                            <span>Chain</span>
                            <strong>{data.chain.upper()}</strong>
                        </div>
                        <div class="details-row">
                            <span>Condition</span>
                            <strong>Price {direction} ${data.target_price:.4f}</strong>
                        </div>
                        <div class="details-row">
                            <span>Alert Type</span>
                            <strong>{'Recurring' if data.is_recurring else 'One-time'}</strong>
                        </div>
                    </div>

                    <p style="text-align: center;">
                        <a href="https://chainlens.app/alerts" class="btn">View All Alerts</a>
                    </p>
                </div>
                <div class="footer">
                    <p>You received this email because you set up a price alert on ChainLens.</p>
                    <p>To manage your alerts, visit your <a href="https://chainlens.app/alerts">alerts dashboard</a>.</p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_content = f"""
Price Alert Triggered!

Hi {data.user_name},

Your price alert for {data.token_symbol} has been triggered!

Current Price: ${data.current_price:.4f}
Target: {direction} ${data.target_price:.4f}
24h Change: {'+' if data.change_percent >= 0 else ''}{data.change_percent:.2f}%

Chain: {data.chain.upper()}
Alert Type: {'Recurring' if data.is_recurring else 'One-time'}

View all alerts: https://chainlens.app/alerts

---
ChainLens - Your Multi-Chain Portfolio Tracker
        """

        return self._send_email(
            to_email=data.user_email,
            subject=subject,
            html_content=html_content,
            plain_content=plain_content
        )

    # ============================================================
    # DAILY DIGEST EMAILS
    # ============================================================

    def send_daily_digest(self, data: DailyDigestEmailData) -> bool:
        """
        Send daily portfolio digest email.

        Called once per day for users who have it enabled.
        """
        change_emoji = "📈" if data.change_percent >= 0 else "📉"
        subject = f"{change_emoji} Daily Digest: Portfolio ${data.portfolio_value:,.2f} ({'+' if data.change_percent >= 0 else ''}{data.change_percent:.2f}%)"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .value-box {{ background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; }}
                .total-value {{ font-size: 36px; font-weight: bold; color: #1a1a2e; }}
                .change {{ font-size: 18px; margin-top: 10px; }}
                .positive {{ color: #10b981; }}
                .negative {{ color: #ef4444; }}
                .movers {{ display: flex; gap: 20px; margin: 20px 0; }}
                .mover {{ flex: 1; background: #f8f9fa; border-radius: 8px; padding: 15px; text-align: center; }}
                .mover-label {{ font-size: 12px; color: #666; margin-bottom: 5px; }}
                .mover-symbol {{ font-size: 18px; font-weight: bold; }}
                .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Your Daily Portfolio Digest</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.8;">{datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                <div class="content">
                    <p>Good morning, {data.user_name}!</p>
                    <p>Here's your portfolio summary for the last 24 hours:</p>

                    <div class="value-box">
                        <div class="total-value">${data.portfolio_value:,.2f}</div>
                        <div class="change {'positive' if data.change_percent >= 0 else 'negative'}">
                            {'+' if data.change_24h >= 0 else ''}${data.change_24h:,.2f} ({'+' if data.change_percent >= 0 else ''}{data.change_percent:.2f}%)
                        </div>
                    </div>

                    <div class="movers">
                        <div class="mover">
                            <div class="mover-label">🚀 Top Gainer</div>
                            <div class="mover-symbol">{data.top_gainer.get('symbol', 'N/A') if data.top_gainer else 'N/A'}</div>
                            <div class="positive">+{data.top_gainer.get('change_percent', 0):.2f}%</div>
                        </div>
                        <div class="mover">
                            <div class="mover-label">📉 Top Loser</div>
                            <div class="mover-symbol">{data.top_loser.get('symbol', 'N/A') if data.top_loser else 'N/A'}</div>
                            <div class="negative">{data.top_loser.get('change_percent', 0):.2f}%</div>
                        </div>
                    </div>

                    <p style="text-align: center;">
                        <a href="https://chainlens.app" class="btn">View Full Portfolio</a>
                    </p>
                </div>
                <div class="footer">
                    <p>You're receiving this daily digest because you enabled it in your settings.</p>
                    <p><a href="https://chainlens.app/alerts">Manage email preferences</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_content = f"""
Daily Portfolio Digest - {datetime.now().strftime('%B %d, %Y')}

Hi {data.user_name},

Portfolio Value: ${data.portfolio_value:,.2f}
24h Change: {'+' if data.change_24h >= 0 else ''}${data.change_24h:,.2f} ({'+' if data.change_percent >= 0 else ''}{data.change_percent:.2f}%)

Top Gainer: {data.top_gainer.get('symbol', 'N/A') if data.top_gainer else 'N/A'} (+{data.top_gainer.get('change_percent', 0):.2f}%)
Top Loser: {data.top_loser.get('symbol', 'N/A') if data.top_loser else 'N/A'} ({data.top_loser.get('change_percent', 0):.2f}%)

View portfolio: https://chainlens.app

---
ChainLens - Your Multi-Chain Portfolio Tracker
        """

        return self._send_email(
            to_email=data.user_email,
            subject=subject,
            html_content=html_content,
            plain_content=plain_content
        )

    # ============================================================
    # WEEKLY SUMMARY EMAILS
    # ============================================================

    def send_weekly_summary(self, data: WeeklySummaryEmailData) -> bool:
        """
        Send weekly portfolio summary email.
        Includes: portfolio value, weekly change, performers, and portfolio suggestions.
        """
        change_emoji = "📈" if data.change_percent >= 0 else "📉"
        change_sign = "+" if data.change_percent >= 0 else ""
        change_color = "#10b981" if data.change_percent >= 0 else "#ef4444"
        subject = f"{change_emoji} Weekly Portfolio: {change_sign}{data.change_percent:.2f}% | ${data.portfolio_value_end:,.2f}"

        # Build performers HTML
        performers_html = ""
        if data.best_performer:
            performers_html += f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #e4e4e7;">
                <span style="color:#52525b; font-size:14px;">🏆 Best performer</span>
                <span style="font-weight:600; color:#10b981;">{data.best_performer['symbol']} {'+' if data.best_performer['change_percent'] >= 0 else ''}{data.best_performer['change_percent']:.2f}%</span>
            </div>"""
        if data.worst_performer:
            performers_html += f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0;">
                <span style="color:#52525b; font-size:14px;">📉 Worst performer</span>
                <span style="font-weight:600; color:#ef4444;">{data.worst_performer['symbol']} {'+' if data.worst_performer['change_percent'] >= 0 else ''}{data.worst_performer['change_percent']:.2f}%</span>
            </div>"""

        # Build suggestions HTML
        suggestions = data.suggestions or []
        priority_colors = {"high": "#ef4444", "medium": "#f59e0b", "low": "#10b981"}
        suggestions_html = ""
        if suggestions:
            suggestion_items = ""
            for s in suggestions[:3]:
                priority = s.get("priority", "medium")
                color = priority_colors.get(priority, "#f59e0b")
                suggestion_items += f"""
                <div style="padding:12px; background:#fafafa; border-left:3px solid {color}; border-radius:0 6px 6px 0; margin-bottom:10px;">
                    <div style="font-weight:600; font-size:14px; color:#18181b;">{s.get('title', '')}</div>
                    <div style="font-size:13px; color:#71717a; margin-top:4px;">{s.get('reason', '')}</div>
                </div>"""
            suggestions_html = f"""
            <div style="margin-top:24px;">
                <h3 style="font-size:15px; font-weight:600; color:#18181b; margin:0 0 12px;">💡 Portfolio Suggestions</h3>
                {suggestion_items}
            </div>"""

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#f4f4f5; margin:0; padding:20px;">
            <div style="max-width:600px; margin:0 auto; background:white; border-radius:12px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,0.08);">

                <!-- Header -->
                <div style="background:linear-gradient(135deg,#18181b 0%,#27272a 100%); color:white; padding:32px 30px; text-align:center;">
                    <p style="margin:0 0 4px; font-size:12px; text-transform:uppercase; letter-spacing:1px; opacity:0.5;">Weekly Report</p>
                    <h1 style="margin:0; font-size:22px; font-weight:700;">Portfolio Summary</h1>
                    <p style="margin:8px 0 0; opacity:0.5; font-size:13px;">{datetime.now().strftime('%B %d, %Y')}</p>
                </div>

                <!-- Value Card -->
                <div style="padding:30px 30px 0;">
                    <div style="background:#f8f8f9; border-radius:10px; padding:24px; text-align:center; margin-bottom:24px;">
                        <p style="margin:0 0 4px; font-size:12px; color:#a1a1aa; text-transform:uppercase; letter-spacing:0.5px;">Total Portfolio Value</p>
                        <p style="margin:0; font-size:36px; font-weight:700; color:#18181b;">${data.portfolio_value_end:,.2f}</p>
                        <p style="margin:8px 0 0; font-size:16px; font-weight:600; color:{change_color};">
                            {change_emoji} {change_sign}{data.change_percent:.2f}% this week ({change_sign}${abs(data.change_week):,.2f})
                        </p>
                    </div>

                    <!-- Stats Row -->
                    <div style="display:flex; gap:12px; margin-bottom:24px;">
                        <div style="flex:1; background:#f8f8f9; border-radius:8px; padding:16px; text-align:center;">
                            <p style="margin:0 0 4px; font-size:11px; color:#a1a1aa; text-transform:uppercase;">Tokens</p>
                            <p style="margin:0; font-size:22px; font-weight:700; color:#18181b;">{data.total_tokens}</p>
                        </div>
                        <div style="flex:1; background:#f8f8f9; border-radius:8px; padding:16px; text-align:center;">
                            <p style="margin:0 0 4px; font-size:11px; color:#a1a1aa; text-transform:uppercase;">Alerts Fired</p>
                            <p style="margin:0; font-size:22px; font-weight:700; color:#18181b;">{data.alerts_triggered}</p>
                        </div>
                    </div>

                    <!-- Performers -->
                    {f'<div style="background:#f8f8f9; border-radius:8px; padding:16px; margin-bottom:24px;">{performers_html}</div>' if performers_html else ''}

                    <!-- Suggestions -->
                    {suggestions_html}

                    <!-- CTA -->
                    <div style="text-align:center; margin:28px 0;">
                        <a href="{settings.app_url}/analytics" style="display:inline-block; background:#18181b; color:white; padding:13px 28px; border-radius:8px; text-decoration:none; font-weight:600; font-size:14px;">View Full Analytics →</a>
                    </div>
                </div>

                <!-- Footer -->
                <div style="background:#f8f8f9; padding:20px 30px; text-align:center; border-top:1px solid #e4e4e7;">
                    <p style="margin:0; color:#a1a1aa; font-size:12px;">
                        ChainLens · <a href="{settings.app_url}/alerts" style="color:#71717a;">Manage alerts</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        # Suggestions plain text
        suggestions_plain = ""
        if suggestions:
            suggestions_plain = "\n\nPortfolio Suggestions:\n"
            for i, s in enumerate(suggestions[:3], 1):
                suggestions_plain += f"{i}. {s.get('title', '')} — {s.get('reason', '')}\n"

        plain_content = f"""Weekly Portfolio Summary — {datetime.now().strftime('%B %d, %Y')}

Hi {data.user_name},

Current Value: ${data.portfolio_value_end:,.2f}
Weekly Change: {change_sign}{data.change_percent:.2f}% ({change_sign}${abs(data.change_week):,.2f})
Tokens Held: {data.total_tokens}
Alerts Fired: {data.alerts_triggered}
{f"Best Performer: {data.best_performer['symbol']} {'+' if data.best_performer['change_percent'] >= 0 else ''}{data.best_performer['change_percent']:.2f}%" if data.best_performer else ""}
{f"Worst Performer: {data.worst_performer['symbol']} {'+' if data.worst_performer['change_percent'] >= 0 else ''}{data.worst_performer['change_percent']:.2f}%" if data.worst_performer else ""}
{suggestions_plain}
View full analytics: {settings.app_url}/analytics

---
ChainLens · Manage alerts: {settings.app_url}/alerts
        """

        return self._send_email(
            to_email=data.user_email,
            subject=subject,
            html_content=html_content,
            plain_content=plain_content
        )

    # ============================================================
    # MILESTONE EMAILS
    # ============================================================

    def send_milestone_alert(self, data: MilestoneEmailData) -> bool:
        """Send milestone notification email (ATH, etc.)"""

        subject = f"🎉 Milestone: {data.token_symbol} - {data.message}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; text-align: center; }}
                .price {{ font-size: 48px; font-weight: bold; color: #1a1a2e; }}
                .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Milestone Reached!</h1>
                </div>
                <div class="content">
                    <p>Hi {data.user_name},</p>
                    <h2>{data.message}</h2>
                    <div class="price">${data.current_price:,.4f}</div>
                    {f'<p>Previous record: ${data.previous_record:,.4f}</p>' if data.previous_record else ''}
                    <p style="margin-top: 30px;">
                        <a href="https://chainlens.app" class="btn">View Portfolio</a>
                    </p>
                </div>
                <div class="footer">
                    <p><a href="https://chainlens.app/alerts">Manage notifications</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_content = f"""
Milestone Reached!

Hi {data.user_name},

{data.message}

Current Price: ${data.current_price:,.4f}
{f'Previous Record: ${data.previous_record:,.4f}' if data.previous_record else ''}

View portfolio: https://chainlens.app

---
ChainLens
        """

        return self._send_email(
            to_email=data.user_email,
            subject=subject,
            html_content=html_content,
            plain_content=plain_content
        )

    # ============================================================
    # EMAIL VERIFICATION
    # ============================================================

    def send_verification_email(self, to_email: str, user_name: str, verify_url: str) -> bool:
        """Send an email verification link to a new user."""
        subject = "Verify your ChainLens email address"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #18181b 0%, #27272a 100%); color: white; padding: 36px 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }}
                .header p {{ margin: 8px 0 0; opacity: 0.6; font-size: 14px; }}
                .content {{ padding: 36px 30px; }}
                .verify-btn {{ display: block; width: fit-content; margin: 28px auto; background: #18181b; color: white; padding: 14px 36px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px; }}
                .url-box {{ background: #f4f4f5; border-radius: 6px; padding: 12px 16px; word-break: break-all; font-size: 12px; color: #71717a; margin: 20px 0; }}
                .footer {{ background: #f4f4f5; padding: 20px 30px; text-align: center; color: #a1a1aa; font-size: 12px; }}
                .footer a {{ color: #71717a; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>ChainLens</h1>
                    <p>Multi-Chain Portfolio Tracker</p>
                </div>
                <div class="content">
                    <p style="font-size:16px; color:#18181b;">Hi {user_name},</p>
                    <p style="color:#52525b;">Thanks for signing up! Please verify your email address to unlock all features including price alerts.</p>
                    <a href="{verify_url}" class="verify-btn">Verify Email Address</a>
                    <p style="color:#71717a; font-size:13px; text-align:center;">This link expires in 24 hours.</p>
                    <p style="color:#a1a1aa; font-size:12px; margin-top:24px;">If the button above doesn't work, copy and paste this URL into your browser:</p>
                    <div class="url-box">{verify_url}</div>
                    <p style="color:#a1a1aa; font-size:12px;">If you didn't create a ChainLens account, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>ChainLens · <a href="https://chainlens.app">chainlens.app</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_content = f"""Hi {user_name},

Please verify your ChainLens email address by visiting:
{verify_url}

This link expires in 24 hours.

If you didn't create a ChainLens account, ignore this email.

---
ChainLens - Your Multi-Chain Portfolio Tracker
        """

        return self._send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            plain_content=plain_content
        )

    # ============================================================
    # TEST EMAIL
    # ============================================================

    def send_test_email(self, to_email: str, user_name: str = "User") -> bool:
        """Send a test email to verify configuration"""

        subject = "🧪 ChainLens Test Email"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; text-align: center; }}
                .checkmark {{ font-size: 64px; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Test Email</h1>
                </div>
                <div class="content">
                    <div class="checkmark">✅</div>
                    <h2>Email Configuration Working!</h2>
                    <p>Hi {user_name},</p>
                    <p>If you're seeing this, your email notifications are properly configured.</p>
                    <p style="color: #666; font-size: 14px;">Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
                <div class="footer">
                    <p>ChainLens - Your Multi-Chain Portfolio Tracker</p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_content = f"""
Test Email - ChainLens

Hi {user_name},

If you're seeing this, your email notifications are properly configured.

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

---
ChainLens
        """

        return self._send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            plain_content=plain_content
        )

    # ============================================================
    # SENDGRID SENDER
    # ============================================================

    def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str, plain_content: str = "") -> bool:
        """
        Send email using the SendGrid Python SDK.
        Returns True on success, False on failure.
        """
        try:
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_content or None,
            )

            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)

            if response.status_code in (200, 201, 202):
                logger.info(f"[EMAIL] SendGrid sent successfully to {to_email} (status {response.status_code})")
                return True
            else:
                logger.error(f"[EMAIL] SendGrid returned unexpected status {response.status_code} for {to_email}")
                return False

        except Exception as e:
            logger.error(f"[EMAIL] SendGrid failed for {to_email}: {e}")
            return False

    # ============================================================
    # INTERNAL EMAIL SENDING
    # ============================================================

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: str
    ) -> bool:
        """
        Internal method to send email.
        Priority: SendGrid (if API key set) → SMTP (if configured) → Console log.
        """

        # Log the email for debugging
        logger.info(f"[EMAIL] Sending to: {to_email}")
        logger.info(f"[EMAIL] Subject: {subject}")

        # 1. Try SendGrid first if configured
        if self.sendgrid_enabled:
            success = self._send_via_sendgrid(to_email, subject, html_content, plain_content)
            if success:
                return True
            logger.warning("[EMAIL] SendGrid failed — falling back to SMTP")

        # 2. Try SMTP if configured
        if self.smtp_enabled:
            try:
                # Create message
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{self.from_name} <{self.from_email}>"
                msg["To"] = to_email

                # Attach plain text and HTML versions
                part1 = MIMEText(plain_content, "plain")
                part2 = MIMEText(html_content, "html")
                msg.attach(part1)
                msg.attach(part2)

                # Send via SMTP
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.from_email, to_email, msg.as_string())

                logger.info(f"[EMAIL] SMTP sent successfully to {to_email}")
                return True

            except Exception as e:
                logger.error(f"[EMAIL] SMTP failed for {to_email}: {e}")
                return False

        # 3. Development/console mode — no transport configured
        print("\n" + "=" * 60)
        print(f"📧 EMAIL (Console Mode)")
        print("=" * 60)
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print("-" * 60)
        print(plain_content)
        print("=" * 60 + "\n")
        return True


# ============================================================
# EMAIL PREFERENCES SERVICE (Keep for backward compatibility)
# ============================================================

class EmailPreferencesService:
    """Service for managing email notification preferences"""

    def __init__(self, preferences_collection):
        self.preferences = preferences_collection

    def get_preferences(self, user_id: str):
        """Get user's email preferences (create defaults if not exists)"""
        from app.models.alert_models import EmailPreferencesResponse
        from datetime import datetime

        prefs = self.preferences.find_one({"user_id": user_id})

        if not prefs:
            # Create default preferences
            default_prefs = {
                "user_id": user_id,
                "price_alerts_enabled": True,
                "daily_digest_enabled": True,
                "weekly_summary_enabled": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = self.preferences.insert_one(default_prefs)
            prefs = self.preferences.find_one({"_id": result.inserted_id})

        return EmailPreferencesResponse(
            user_id=prefs["user_id"],
            price_alerts_enabled=prefs.get("price_alerts_enabled", True),
            daily_digest_enabled=prefs.get("daily_digest_enabled", True),
            weekly_summary_enabled=prefs.get("weekly_summary_enabled", True),
            updated_at=prefs.get("updated_at")
        )

    def update_preferences(self, user_id: str, user_email: str, preferences: dict):
        """Update user's email preferences"""
        from app.models.alert_models import EmailPreferencesResponse
        from datetime import datetime

        update_data = {
            k: v for k, v in preferences.items() if v is not None
        }
        update_data["updated_at"] = datetime.utcnow()

        self.preferences.update_one(
            {"user_id": user_id},
            {
                "$set": update_data,
                "$setOnInsert": {
                    "user_id": user_id,
                    "user_email": user_email,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        return self.get_preferences(user_id)
