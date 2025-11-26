#!/usr/bin/env python3
"""
AI Services Agency Bot - Main Entry Point

Usage:
    python main.py create-campaign --name "Campaign Name" --leads 100
    python main.py run-campaign --name "Campaign Name"
    python main.py stats --name "Campaign Name"
    python main.py generate-content --type linkedin --topic "AI automation"
"""
import click
from loguru import logger
import sys

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/bot_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG"
)

from src.outreach.campaign_manager import CampaignManager
from src.delivery.content_generator import ContentGenerator
from config.settings import settings


@click.group()
def cli():
    """AI Services Agency Bot - Automated B2B outreach and content delivery"""
    pass


@cli.command()
@click.option('--name', required=True, help='Campaign name')
@click.option('--leads', default=100, help='Number of leads to target')
def create_campaign(name: str, leads: int):
    """Create a new outreach campaign"""
    logger.info(f"Creating campaign: {name}")

    manager = CampaignManager()
    campaign = manager.create_campaign(name=name, target_lead_count=leads)

    click.echo(f"\n✅ Campaign '{name}' created successfully!")
    click.echo(f"   Total leads: {len(campaign.leads)}")
    click.echo(f"   Average lead score: {sum(l.score for l in campaign.leads) / len(campaign.leads):.1f}")
    click.echo(f"\nNext step: Run campaign with:")
    click.echo(f"   python main.py run-campaign --name \"{name}\"")


@cli.command()
@click.option('--name', required=True, help='Campaign name')
@click.option('--daily-limit', default=None, type=int, help='Max emails per day')
@click.option('--dry-run', is_flag=True, help='Test without sending emails')
def run_campaign(name: str, daily_limit: int, dry_run: bool):
    """Run an outreach campaign"""
    if dry_run:
        click.echo("🧪 DRY RUN MODE - No emails will be sent\n")

    logger.info(f"Running campaign: {name}")

    manager = CampaignManager()

    if dry_run:
        # Just show what would happen
        if name in manager.campaigns:
            campaign = manager.campaigns[name]
            click.echo(f"Would send emails to {len(campaign.leads)} leads")
        else:
            click.echo(f"Campaign '{name}' not found. Create it first.")
        return

    try:
        campaign = manager.run_campaign(name, daily_limit=daily_limit)

        click.echo(f"\n✅ Campaign execution complete!")
        click.echo(f"   Emails sent today: {campaign.emails_sent}")
        click.echo(f"\nCheck stats with:")
        click.echo(f"   python main.py stats --name \"{name}\"")

    except ValueError as e:
        click.echo(f"❌ Error: {e}")
        click.echo(f"\nCreate the campaign first with:")
        click.echo(f"   python main.py create-campaign --name \"{name}\"")


@cli.command()
@click.option('--name', required=True, help='Campaign name')
def stats(name: str):
    """Show campaign statistics"""
    manager = CampaignManager()

    try:
        stats = manager.get_campaign_stats(name)

        click.echo(f"\n📊 Campaign Statistics: {name}\n")
        click.echo(f"   Status: {stats['status']}")
        click.echo(f"   Created: {stats['created_at']}\n")

        click.echo(f"   Total Leads: {stats['total_leads']}")
        click.echo(f"   Emails Sent: {stats['emails_sent']}")
        click.echo(f"   Replies: {stats['replies_received']} ({stats['reply_rate']})")
        click.echo(f"   Meetings Booked: {stats['meetings_booked']} ({stats['meeting_rate']})")
        click.echo(f"   Deals Closed: {stats['deals_closed']} ({stats['close_rate']})")
        click.echo(f"\n   💰 Revenue Generated: €{stats['revenue_generated']:,}")

    except ValueError as e:
        click.echo(f"❌ Error: {e}")


@cli.command()
@click.option('--type', required=True, type=click.Choice(['linkedin', 'article', 'seo', 'email-sequence']))
@click.option('--topic', required=True, help='Content topic')
@click.option('--context', default='B2B SaaS company', help='Company context')
@click.option('--output', default='output.txt', help='Output file')
def generate_content(type: str, topic: str, context: str, output: str):
    """Generate content for service delivery"""
    logger.info(f"Generating {type} content: {topic}")

    generator = ContentGenerator()

    try:
        if type == 'linkedin':
            post = generator.generate_linkedin_post(
                topic=topic,
                company_context=context
            )

            content = f"LINKEDIN POST\n"
            content += f"Quality Score: {post.quality_score:.2f}\n\n"
            content += f"{post.content}\n\n"
            content += f"Hashtags: {' '.join(post.hashtags)}"

        elif type == 'article':
            article = generator.generate_linkedin_article(
                topic=topic,
                target_length=1200
            )

            content = f"ARTICLE: {article.title}\n"
            content += f"Quality Score: {article.quality_score:.2f}\n"
            content += f"Words: {article.word_count}\n\n"
            content += f"{article.content}\n\n"
            content += f"Meta Description: {article.meta_description}"

        elif type == 'seo':
            article = generator.generate_seo_article(
                keyword=topic,
                min_words=1500
            )

            content = f"SEO ARTICLE: {article.title}\n"
            content += f"Quality Score: {article.quality_score:.2f}\n"
            content += f"Words: {article.word_count}\n"
            content += f"Keywords: {', '.join(article.keywords)}\n\n"
            content += f"{article.content}"

        elif type == 'email-sequence':
            emails = generator.generate_email_sequence(
                purpose=topic,
                num_emails=7
            )

            content = f"EMAIL SEQUENCE: {topic}\n\n"
            for i, email in enumerate(emails, 1):
                content += f"EMAIL {i}\n"
                content += f"Subject: {email.get('subject', 'N/A')}\n"
                content += f"Body:\n{email.get('body', 'N/A')}\n"
                content += f"CTA: {email.get('cta', 'N/A')}\n"
                content += f"Wait: {email.get('wait_days', 'N/A')}\n"
                content += "\n" + "="*60 + "\n\n"

        # Save to file
        with open(output, 'w', encoding='utf-8') as f:
            f.write(content)

        click.echo(f"\n✅ Content generated successfully!")
        click.echo(f"   Saved to: {output}")
        click.echo(f"\n📄 Preview:\n")
        click.echo(content[:500] + "...\n")

    except Exception as e:
        logger.error(f"Error generating content: {e}")
        click.echo(f"❌ Error: {e}")


@cli.command()
def test_config():
    """Test configuration and API keys"""
    click.echo("🔍 Testing configuration...\n")

    issues = []

    # Check OpenAI API
    if settings.openai_api_key:
        click.echo("✅ OpenAI API key configured")
    else:
        click.echo("❌ OpenAI API key missing")
        issues.append("Add OPENAI_API_KEY to .env")

    # Check Anthropic API
    if settings.anthropic_api_key:
        click.echo("✅ Anthropic API key configured")
    else:
        click.echo("❌ Anthropic API key missing")
        issues.append("Add ANTHROPIC_API_KEY to .env")

    # Check Email service
    if settings.resend_api_key:
        click.echo("✅ Resend API key configured")
    elif settings.sendgrid_api_key:
        click.echo("✅ SendGrid API key configured")
    else:
        click.echo("⚠️  No email service configured (Resend or SendGrid)")
        issues.append("Add RESEND_API_KEY or SENDGRID_API_KEY to .env")

    # Check Apollo (optional)
    if settings.apollo_api_key:
        click.echo("✅ Apollo API key configured")
    else:
        click.echo("ℹ️  Apollo API key not configured (optional)")

    if issues:
        click.echo(f"\n⚠️  {len(issues)} issue(s) found:")
        for issue in issues:
            click.echo(f"   - {issue}")
    else:
        click.echo("\n🎉 All configuration looks good!")


@cli.command()
def quickstart():
    """Quick start guide"""
    click.echo("""
╔═══════════════════════════════════════════════════════════════╗
║        AI Services Agency Bot - Quick Start Guide             ║
╚═══════════════════════════════════════════════════════════════╝

STEP 1: Configure API Keys
   Edit config/.env with your API keys:
   - OPENAI_API_KEY (required)
   - ANTHROPIC_API_KEY (required)
   - RESEND_API_KEY (required for sending emails)

STEP 2: Test Configuration
   python main.py test-config

STEP 3: Create Your First Campaign
   python main.py create-campaign --name "Test Campaign" --leads 10

STEP 4: Run the Campaign (dry run first)
   python main.py run-campaign --name "Test Campaign" --dry-run

STEP 5: Send Real Emails
   python main.py run-campaign --name "Test Campaign"

STEP 6: Check Results
   python main.py stats --name "Test Campaign"

BONUS: Generate Content
   python main.py generate-content --type linkedin --topic "AI automation"

Need help? Check the README.md for detailed instructions.
    """)


if __name__ == '__main__':
    cli()
