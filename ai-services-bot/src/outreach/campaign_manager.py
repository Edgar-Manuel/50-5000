"""
Campaign Management System
Orchestrates the entire outreach process
"""
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from loguru import logger
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config.settings import settings
from src.lead_generation.scraper import Lead, LeadScraper
from src.outreach.email_generator import Email, EmailGenerator


@dataclass
class Campaign:
    """Campaign data structure"""
    name: str
    leads: List[Lead]
    emails_sent: int = 0
    replies_received: int = 0
    meetings_booked: int = 0
    deals_closed: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "active"  # active, paused, completed


class CampaignManager:
    """Manages outreach campaigns end-to-end"""

    def __init__(self):
        self.lead_scraper = LeadScraper()
        self.email_generator = EmailGenerator()
        self.campaigns: Dict[str, Campaign] = {}

    def create_campaign(
        self,
        name: str,
        target_lead_count: int = 100
    ) -> Campaign:
        """
        Create a new outreach campaign

        Args:
            name: Campaign name
            target_lead_count: Number of leads to target

        Returns:
            Campaign object
        """
        logger.info(f"Creating campaign: {name}")

        # Generate leads
        leads = self.lead_scraper.scrape_leads(target_count=target_lead_count)

        campaign = Campaign(
            name=name,
            leads=leads
        )

        self.campaigns[name] = campaign

        logger.info(f"Campaign '{name}' created with {len(leads)} leads")
        return campaign

    def run_campaign(
        self,
        campaign_name: str,
        daily_limit: Optional[int] = None
    ):
        """
        Execute campaign with daily email sending

        Args:
            campaign_name: Name of campaign to run
            daily_limit: Max emails per day (default from settings)
        """
        if campaign_name not in self.campaigns:
            raise ValueError(f"Campaign '{campaign_name}' not found")

        campaign = self.campaigns[campaign_name]
        daily_limit = daily_limit or settings.daily_email_limit

        logger.info(f"Starting campaign: {campaign_name}")

        # Track sent emails to avoid duplicates
        sent_to = set()

        # Send initial emails
        emails_today = 0

        for lead in campaign.leads:
            if emails_today >= daily_limit:
                logger.info(f"Reached daily limit ({daily_limit}). Stopping for today.")
                break

            if lead.email in sent_to:
                continue

            # Generate personalized email
            email = self.email_generator.generate_email(lead)

            if not email:
                logger.warning(f"Skipping {lead.name} - personalization score too low")
                continue

            # Send email
            success = self._send_email(email)

            if success:
                sent_to.add(lead.email)
                campaign.emails_sent += 1
                emails_today += 1

                logger.info(f"Sent email to {lead.name} ({emails_today}/{daily_limit})")

                # Schedule follow-ups
                self._schedule_followups(lead, campaign_name)

                # Rate limiting (be human-like)
                delay = random.uniform(30, 120)  # 30-120 seconds between emails
                time.sleep(delay)

        logger.info(f"Campaign '{campaign_name}' execution complete. Sent {emails_today} emails today.")

        return campaign

    def _send_email(self, email: Email) -> bool:
        """
        Send email via SMTP

        Args:
            email: Email object to send

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use Resend API if available (recommended)
            if settings.resend_api_key:
                return self._send_via_resend(email)

            # Fallback to SMTP (needs configuration)
            return self._send_via_smtp(email)

        except Exception as e:
            logger.error(f"Error sending email to {email.to}: {e}")
            return False

    def _send_via_resend(self, email: Email) -> bool:
        """Send email using Resend API"""
        import requests

        url = "https://api.resend.com/emails"

        payload = {
            "from": settings.company_email,
            "to": [email.to],
            "subject": email.subject,
            "text": email.body
        }

        headers = {
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            logger.info(f"Email sent via Resend to {email.to}")
            return True

        except Exception as e:
            logger.error(f"Resend API error: {e}")
            return False

    def _send_via_smtp(self, email: Email) -> bool:
        """Send email via SMTP (fallback)"""
        # This requires SMTP configuration in .env
        # Example with Gmail:

        smtp_server = "smtp.gmail.com"  # Configure in settings
        smtp_port = 587
        smtp_user = settings.company_email
        smtp_password = ""  # Add to settings

        if not smtp_password:
            logger.error("SMTP password not configured")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = email.to
            msg['Subject'] = email.subject

            msg.attach(MIMEText(email.body, 'plain'))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent via SMTP to {email.to}")
            return True

        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False

    def _schedule_followups(self, lead: Lead, campaign_name: str):
        """
        Schedule follow-up emails

        Args:
            lead: Lead to follow up with
            campaign_name: Campaign name
        """
        # In production, use Celery or scheduled tasks
        # For now, we'll track in database

        followup_schedule = [
            {"days": 3, "sequence": 1},
            {"days": 6, "sequence": 2},
            {"days": 10, "sequence": 3}
        ]

        for followup in followup_schedule:
            scheduled_date = datetime.now() + timedelta(days=followup["days"])

            logger.info(
                f"Scheduled follow-up {followup['sequence']} for {lead.name} on {scheduled_date.date()}"
            )

            # Store in database (implement with SQLAlchemy in production)
            # For now, just log

    def send_followup(self, lead: Lead, sequence_number: int) -> bool:
        """
        Send follow-up email

        Args:
            lead: Lead to follow up with
            sequence_number: Which follow-up (1, 2, or 3)

        Returns:
            True if sent successfully
        """
        logger.info(f"Sending follow-up #{sequence_number} to {lead.name}")

        email = self.email_generator.generate_followup(lead, sequence_number)

        if not email:
            logger.error(f"Failed to generate follow-up for {lead.name}")
            return False

        return self._send_email(email)

    def check_replies(self) -> List[Dict]:
        """
        Check for email replies

        Returns:
            List of reply objects
        """
        # This requires IMAP access to check inbox
        # Implement with imaplib or use email API

        logger.info("Checking for replies...")

        # Placeholder - implement actual reply checking
        replies = []

        return replies

    def get_campaign_stats(self, campaign_name: str) -> Dict:
        """
        Get campaign statistics

        Args:
            campaign_name: Campaign name

        Returns:
            Dictionary with stats
        """
        if campaign_name not in self.campaigns:
            raise ValueError(f"Campaign '{campaign_name}' not found")

        campaign = self.campaigns[campaign_name]

        reply_rate = (campaign.replies_received / campaign.emails_sent * 100) if campaign.emails_sent > 0 else 0
        meeting_rate = (campaign.meetings_booked / campaign.replies_received * 100) if campaign.replies_received > 0 else 0
        close_rate = (campaign.deals_closed / campaign.meetings_booked * 100) if campaign.meetings_booked > 0 else 0

        stats = {
            "campaign_name": campaign.name,
            "total_leads": len(campaign.leads),
            "emails_sent": campaign.emails_sent,
            "replies_received": campaign.replies_received,
            "reply_rate": f"{reply_rate:.1f}%",
            "meetings_booked": campaign.meetings_booked,
            "meeting_rate": f"{meeting_rate:.1f}%",
            "deals_closed": campaign.deals_closed,
            "close_rate": f"{close_rate:.1f}%",
            "revenue_generated": campaign.deals_closed * 1200,  # Average deal size
            "created_at": campaign.created_at.strftime("%Y-%m-%d"),
            "status": campaign.status
        }

        return stats

    def pause_campaign(self, campaign_name: str):
        """Pause a campaign"""
        if campaign_name in self.campaigns:
            self.campaigns[campaign_name].status = "paused"
            logger.info(f"Campaign '{campaign_name}' paused")

    def resume_campaign(self, campaign_name: str):
        """Resume a paused campaign"""
        if campaign_name in self.campaigns:
            self.campaigns[campaign_name].status = "active"
            logger.info(f"Campaign '{campaign_name}' resumed")


# Example usage
if __name__ == "__main__":
    manager = CampaignManager()

    # Create campaign
    campaign = manager.create_campaign(
        name="December 2025 - SaaS Founders",
        target_lead_count=50
    )

    # Run campaign (sends emails)
    manager.run_campaign(
        campaign_name="December 2025 - SaaS Founders",
        daily_limit=20
    )

    # Check stats
    stats = manager.get_campaign_stats("December 2025 - SaaS Founders")
    print("\nCampaign Stats:")
    for key, value in stats.items():
        print(f"{key}: {value}")
