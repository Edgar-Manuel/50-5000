"""
Lead generation and scraping module
Finds qualified B2B prospects for AI services
"""
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger
from config.settings import settings


@dataclass
class Lead:
    """Lead data structure"""
    name: str
    email: Optional[str]
    job_title: str
    company_name: str
    company_domain: Optional[str]
    linkedin_url: Optional[str]
    industry: Optional[str]
    company_size: Optional[int]
    location: Optional[str]
    recent_activity: Optional[List[str]] = None
    score: float = 0.0


class LeadScraper:
    """Scrapes and enriches leads from multiple sources"""

    def __init__(self):
        self.icp = {
            "company_size": [10, 500],
            "industries": ["SaaS", "Marketing Agency", "Consulting", "E-commerce"],
            "job_titles": ["CEO", "CMO", "Head of Marketing", "Founder", "Marketing Director"],
        }

    def scrape_leads(self, target_count: int = 100) -> List[Lead]:
        """
        Scrape leads from multiple sources

        Args:
            target_count: Number of leads to collect

        Returns:
            List of Lead objects
        """
        logger.info(f"Starting lead scraping for {target_count} leads")

        leads = []

        # Source 1: Apollo.io (if configured)
        if settings.apollo_api_key:
            apollo_leads = self._scrape_apollo(target_count // 2)
            leads.extend(apollo_leads)
            logger.info(f"Scraped {len(apollo_leads)} leads from Apollo")

        # Source 2: LinkedIn Sales Navigator (manual export or API)
        # Note: LinkedIn has strict ToS, this should use official API or manual exports

        # Source 3: Public databases (GitHub sponsors, Product Hunt makers, etc)
        public_leads = self._scrape_public_sources(target_count // 4)
        leads.extend(public_leads)

        # Enrich all leads
        enriched_leads = [self._enrich_lead(lead) for lead in leads]

        # Score and sort
        scored_leads = [self._score_lead(lead) for lead in enriched_leads]
        scored_leads.sort(key=lambda x: x.score, reverse=True)

        logger.info(f"Successfully scraped and scored {len(scored_leads)} leads")

        return scored_leads[:target_count]

    def _scrape_apollo(self, limit: int) -> List[Lead]:
        """
        Scrape leads from Apollo.io

        Args:
            limit: Max number of leads to fetch

        Returns:
            List of Lead objects
        """
        if not settings.apollo_api_key:
            logger.warning("Apollo API key not configured")
            return []

        # Apollo API endpoint (example - adjust based on actual API)
        url = "https://api.apollo.io/v1/people/search"

        headers = {
            "Authorization": f"Bearer {settings.apollo_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "person_titles": self.icp["job_titles"],
            "organization_num_employees_ranges": [f"{self.icp['company_size'][0]},{self.icp['company_size'][1]}"],
            "page": 1,
            "per_page": min(limit, 100)
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            leads = []
            for person in data.get("people", []):
                lead = Lead(
                    name=person.get("name", ""),
                    email=person.get("email"),
                    job_title=person.get("title", ""),
                    company_name=person.get("organization", {}).get("name", ""),
                    company_domain=person.get("organization", {}).get("website_url"),
                    linkedin_url=person.get("linkedin_url"),
                    industry=person.get("organization", {}).get("industry"),
                    company_size=person.get("organization", {}).get("estimated_num_employees"),
                    location=person.get("city")
                )
                leads.append(lead)

            return leads

        except Exception as e:
            logger.error(f"Error scraping Apollo: {e}")
            return []

    def _scrape_public_sources(self, limit: int) -> List[Lead]:
        """
        Scrape leads from public sources (Product Hunt, GitHub, etc)

        Args:
            limit: Max number of leads

        Returns:
            List of Lead objects
        """
        leads = []

        # Example: Product Hunt makers (public data)
        # This is a placeholder - you'd implement actual scraping logic

        logger.info(f"Scraped {len(leads)} leads from public sources")
        return leads

    def _enrich_lead(self, lead: Lead) -> Lead:
        """
        Enrich lead with additional data

        Args:
            lead: Lead object to enrich

        Returns:
            Enriched Lead object
        """
        # Find email if missing
        if not lead.email and lead.company_domain:
            lead.email = self._find_email(lead.name, lead.company_domain)

        # Get recent LinkedIn activity (if possible)
        if lead.linkedin_url:
            lead.recent_activity = self._get_linkedin_activity(lead.linkedin_url)

        return lead

    def _find_email(self, name: str, domain: str) -> Optional[str]:
        """
        Find email using Hunter.io or pattern matching

        Args:
            name: Person's name
            domain: Company domain

        Returns:
            Email address or None
        """
        if not settings.hunter_api_key:
            # Fallback: common email patterns
            first_name = name.split()[0].lower()
            last_name = name.split()[-1].lower() if len(name.split()) > 1 else ""

            # Try common patterns
            patterns = [
                f"{first_name}@{domain}",
                f"{first_name}.{last_name}@{domain}",
                f"{first_name[0]}{last_name}@{domain}",
            ]

            # In real implementation, you'd verify these
            return patterns[0] if patterns else None

        # Use Hunter.io API
        try:
            url = f"https://api.hunter.io/v2/email-finder"
            params = {
                "domain": domain,
                "first_name": name.split()[0],
                "last_name": name.split()[-1] if len(name.split()) > 1 else "",
                "api_key": settings.hunter_api_key
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            return data.get("data", {}).get("email")

        except Exception as e:
            logger.error(f"Error finding email with Hunter: {e}")
            return None

    def _get_linkedin_activity(self, linkedin_url: str) -> List[str]:
        """
        Get recent LinkedIn posts (would need LinkedIn API or scraping)

        Args:
            linkedin_url: LinkedIn profile URL

        Returns:
            List of recent post texts
        """
        # Placeholder - would need proper LinkedIn API integration
        # LinkedIn has strict ToS, use official API or manual research
        return []

    def _score_lead(self, lead: Lead) -> Lead:
        """
        Score lead based on qualification criteria

        Args:
            lead: Lead to score

        Returns:
            Lead with score assigned
        """
        score = 0.0

        # +30 if has verified email
        if lead.email and "@" in lead.email:
            score += 30

        # +20 if right company size
        if lead.company_size and self.icp["company_size"][0] <= lead.company_size <= self.icp["company_size"][1]:
            score += 20

        # +20 if in target industry
        if lead.industry and any(ind.lower() in lead.industry.lower() for ind in self.icp["industries"]):
            score += 20

        # +15 if has recent activity
        if lead.recent_activity and len(lead.recent_activity) > 0:
            score += 15

        # +15 if has LinkedIn profile
        if lead.linkedin_url:
            score += 15

        lead.score = score
        return lead


# Example usage
if __name__ == "__main__":
    scraper = LeadScraper()
    leads = scraper.scrape_leads(target_count=10)

    for lead in leads[:5]:
        print(f"{lead.name} ({lead.job_title}) at {lead.company_name} - Score: {lead.score}")
