# backend/app/services/email_service.py - COMPLETE VERSION
"""
Email Service - Send email notifications for alerts
Supports: Price Alerts, Daily Digest, Weekly Summary, Milestones
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
import logging

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
    - SMTP (production) - sends real emails
    - SendGrid (optional) - for high volume
    """
    
    def __init__(self):
        # Email configuration from environment
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "alerts@chainlens.app")
        self.from_name = os.getenv("FROM_NAME", "ChainLens Alerts")
        
        # Check if SMTP is configured
        self.smtp_enabled = bool(self.smtp_host and self.smtp_user and self.smtp_password)
        
        if self.smtp_enabled:
            logger.info(f"[EMAIL] SMTP configured: {self.smtp_host}:{self.smtp_port}")
        else:
            logger.info("[EMAIL] SMTP not configured - emails will be logged to console")
    
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
        
        Called once per week (Sunday) for users who have it enabled.
        """
        change_emoji = "📈" if data.change_percent >= 0 else "📉"
        subject = f"{change_emoji} Weekly Summary: {'+' if data.change_percent >= 0 else ''}{data.change_percent:.2f}% this week"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .stats {{ display: flex; gap: 15px; margin: 20px 0; }}
                .stat {{ flex: 1; background: #f8f9fa; border-radius: 8px; padding: 15px; text-align: center; }}
                .stat-value {{ font-size: 24px; font-weight: bold; }}
                .stat-label {{ font-size: 12px; color: #666; }}
                .positive {{ color: #10b981; }}
                .negative {{ color: #ef4444; }}
                .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📅 Weekly Portfolio Summary</h1>
                </div>
                <div class="content">
                    <p>Hi {data.user_name},</p>
                    <p>Here's how your portfolio performed this week:</p>
                    
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-value">${data.portfolio_value_end:,.2f}</div>
                            <div class="stat-label">Current Value</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value {'positive' if data.change_percent >= 0 else 'negative'}">
                                {'+' if data.change_percent >= 0 else ''}{data.change_percent:.2f}%
                            </div>
                            <div class="stat-label">Weekly Change</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{data.alerts_triggered}</div>
                            <div class="stat-label">Alerts Triggered</div>
                        </div>
                    </div>
                    
                    <p style="text-align: center;">
                        <a href="https://chainlens.app/analytics" class="btn">View Analytics</a>
                    </p>
                </div>
                <div class="footer">
                    <p><a href="https://chainlens.app/alerts">Manage email preferences</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_content = f"""
Weekly Portfolio Summary

Hi {data.user_name},

Current Value: ${data.portfolio_value_end:,.2f}
Weekly Change: {'+' if data.change_percent >= 0 else ''}{data.change_percent:.2f}%
Alerts Triggered: {data.alerts_triggered}

View analytics: https://chainlens.app/analytics

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
        Uses SMTP if configured, otherwise logs to console.
        """
        
        # Log the email for debugging
        logger.info(f"[EMAIL] Sending to: {to_email}")
        logger.info(f"[EMAIL] Subject: {subject}")
        
        if not self.smtp_enabled:
            # Development mode - just log
            print("\n" + "=" * 60)
            print(f"📧 EMAIL (Console Mode)")
            print("=" * 60)
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print("-" * 60)
            print(plain_content)
            print("=" * 60 + "\n")
            return True
        
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
            
            logger.info(f"[EMAIL] ✅ Sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"[EMAIL] ❌ Failed to send to {to_email}: {e}")
            # In development, still return True so the flow continues
            return False


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