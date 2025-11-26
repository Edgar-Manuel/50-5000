"""
Service delivery - Content generation module
Generates high-quality content for clients using AI
"""
import openai
from anthropic import Anthropic
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger
from config.settings import settings


@dataclass
class LinkedInPost:
    """LinkedIn post structure"""
    content: str
    hashtags: List[str]
    scheduled_date: Optional[str] = None
    quality_score: float = 0.0


@dataclass
class Article:
    """SEO article structure"""
    title: str
    content: str
    meta_description: str
    keywords: List[str]
    word_count: int
    quality_score: float = 0.0


class ContentGenerator:
    """Generates various types of content for service delivery"""

    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)

    def generate_linkedin_post(
        self,
        topic: str,
        company_context: str,
        tone: str = "professional",
        include_hook: bool = True
    ) -> LinkedInPost:
        """
        Generate a LinkedIn post

        Args:
            topic: Post topic
            company_context: Company/industry context
            tone: Writing tone
            include_hook: Whether to include attention-grabbing hook

        Returns:
            LinkedInPost object
        """
        logger.info(f"Generating LinkedIn post about: {topic}")

        prompt = f"""Write a LinkedIn post for a {company_context}.

Topic: {topic}
Tone: {tone}
Include hook: {include_hook}

Requirements:
- Start with an attention-grabbing first line (hook)
- Make it actionable and valuable (not just theory)
- Include a specific example or stat
- Use short paragraphs (1-2 sentences max)
- End with a question or CTA to encourage engagement
- Length: 150-200 words
- No hashtags in body (we'll add separately)
- Professional but conversational

Format:
[Hook line]

[2-3 paragraphs of value]

[Closing question/CTA]

Write the post:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert LinkedIn content creator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )

            content = response.choices[0].message.content.strip()

            # Generate relevant hashtags
            hashtags = self._generate_hashtags(topic, company_context)

            # Quality check
            quality_score = self._assess_linkedin_quality(content)

            post = LinkedInPost(
                content=content,
                hashtags=hashtags,
                quality_score=quality_score
            )

            logger.info(f"Generated LinkedIn post with quality score: {quality_score}")
            return post

        except Exception as e:
            logger.error(f"Error generating LinkedIn post: {e}")
            raise

    def generate_linkedin_article(
        self,
        topic: str,
        target_length: int = 1200,
        include_stats: bool = True
    ) -> Article:
        """
        Generate a long-form LinkedIn article

        Args:
            topic: Article topic
            target_length: Target word count
            include_stats: Whether to include statistics

        Returns:
            Article object
        """
        logger.info(f"Generating LinkedIn article: {topic}")

        # First, create outline
        outline_prompt = f"""Create an outline for a LinkedIn article about: {topic}

Requirements:
- 5-7 main sections
- Each section should have 2-3 subsections
- Professional, actionable content
- Target length: {target_length} words

Provide just the outline with section headings:"""

        try:
            outline_response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": outline_prompt}],
                temperature=0.7,
                max_tokens=300
            )

            outline = outline_response.choices[0].message.content

            # Generate full article based on outline
            article_prompt = f"""Write a professional LinkedIn article based on this outline:

{outline}

Topic: {topic}
Target length: {target_length} words
Include statistics: {include_stats}

Requirements:
- Professional but conversational tone
- Use concrete examples
- Include actionable takeaways
- Format with proper markdown (##, ###, bullet points)
- Include an engaging introduction
- End with a clear conclusion/call-to-action

Write the full article:"""

            article_response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=3000,
                messages=[{"role": "user", "content": article_prompt}]
            )

            content = article_response.content[0].text

            # Generate title
            title = self._generate_article_title(topic)

            # Generate meta description
            meta = self._generate_meta_description(content)

            # Extract keywords
            keywords = self._extract_keywords(topic, content)

            word_count = len(content.split())

            article = Article(
                title=title,
                content=content,
                meta_description=meta,
                keywords=keywords,
                word_count=word_count,
                quality_score=self._assess_article_quality(content, target_length)
            )

            logger.info(f"Generated article: {word_count} words, quality: {article.quality_score}")
            return article

        except Exception as e:
            logger.error(f"Error generating article: {e}")
            raise

    def generate_seo_article(
        self,
        keyword: str,
        competitor_outlines: Optional[List[str]] = None,
        min_words: int = 1500
    ) -> Article:
        """
        Generate SEO-optimized article

        Args:
            keyword: Target keyword
            competitor_outlines: Outlines from top-ranking competitors
            min_words: Minimum word count

        Returns:
            Article object
        """
        logger.info(f"Generating SEO article for keyword: {keyword}")

        # Create comprehensive outline
        outline_prompt = f"""Create an SEO-optimized article outline for the keyword: "{keyword}"

Target: Outrank current top-10 results
Minimum length: {min_words} words

{f'Competitor outlines to beat: {competitor_outlines}' if competitor_outlines else ''}

Requirements:
- Start with compelling H1 (include keyword)
- 8-12 H2 sections
- Each H2 should have 2-4 H3 subsections
- Include: Introduction, Main content sections, FAQ section, Conclusion
- Incorporate keyword naturally throughout headings
- Focus on search intent and user value

Provide the outline:"""

        try:
            # Generate outline
            outline_response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=800,
                messages=[{"role": "user", "content": outline_prompt}]
            )

            outline = outline_response.content[0].text

            # Generate full article
            article_prompt = f"""Write a comprehensive SEO article based on this outline:

{outline}

Target keyword: "{keyword}"
Minimum length: {min_words} words

SEO Requirements:
- Use target keyword in: title, first paragraph, at least 3 H2s, conclusion
- Keyword density: 1-2% (natural, not stuffed)
- Include related keywords and semantic variations
- Write for humans first, search engines second
- Include specific examples and actionable advice
- Use bullet points and numbered lists where appropriate
- Add a FAQ section (5-7 questions)

Content Requirements:
- Expert, authoritative tone
- Back claims with data when possible
- Be comprehensive - cover topic thoroughly
- Format with proper markdown
- Include internal linking suggestions [like this]

Write the complete article:"""

            article_response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                messages=[{"role": "user", "content": article_prompt}]
            )

            content = article_response.content[0].text

            # Generate SEO metadata
            title = self._generate_seo_title(keyword, content)
            meta = self._generate_meta_description(content, keyword=keyword)
            keywords_list = self._extract_keywords(keyword, content)

            word_count = len(content.split())

            article = Article(
                title=title,
                content=content,
                meta_description=meta,
                keywords=keywords_list,
                word_count=word_count,
                quality_score=self._assess_article_quality(content, min_words)
            )

            logger.info(f"Generated SEO article: {word_count} words, quality: {article.quality_score}")
            return article

        except Exception as e:
            logger.error(f"Error generating SEO article: {e}")
            raise

    def generate_email_sequence(
        self,
        purpose: str,
        num_emails: int = 7,
        audience: str = "B2B prospects"
    ) -> List[Dict[str, str]]:
        """
        Generate email nurture sequence

        Args:
            purpose: Purpose of the sequence (e.g., "lead nurturing", "onboarding")
            num_emails: Number of emails in sequence
            audience: Target audience description

        Returns:
            List of email dictionaries
        """
        logger.info(f"Generating {num_emails}-email sequence for: {purpose}")

        prompt = f"""Create a {num_emails}-email sequence for {purpose}.

Audience: {audience}

Requirements:
- Each email should build on the previous one
- Mix of education, value, and soft selling
- Clear CTAs
- Personalization placeholders: {{{{first_name}}}}, {{{{company}}}}
- Subject lines that get opens (no spam words)

Format for each email:
EMAIL [number]: [brief description]
SUBJECT: [subject line]
PREVIEW: [preview text]
BODY:
[email body with {{{{personalization}}}}]

CTA: [call to action]
WAIT: [days until next email]

---

Generate all {num_emails} emails:"""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=3500,
                messages=[{"role": "user", "content": prompt}]
            )

            sequence_text = response.content[0].text

            # Parse into structured format
            emails = self._parse_email_sequence(sequence_text)

            logger.info(f"Generated {len(emails)}-email sequence")
            return emails

        except Exception as e:
            logger.error(f"Error generating email sequence: {e}")
            raise

    def _generate_hashtags(self, topic: str, context: str, count: int = 5) -> List[str]:
        """Generate relevant hashtags"""
        prompt = f"""Generate {count} relevant LinkedIn hashtags for:
Topic: {topic}
Context: {context}

Requirements:
- Mix of popular and niche
- Relevant to B2B audience
- No overly generic tags like #success #motivation

Format: Just list the hashtags with # symbol, one per line"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=100
            )

            hashtags_text = response.choices[0].message.content.strip()
            hashtags = [tag.strip() for tag in hashtags_text.split('\n') if tag.strip().startswith('#')]

            return hashtags[:count]

        except Exception as e:
            logger.error(f"Error generating hashtags: {e}")
            return []

    def _generate_article_title(self, topic: str) -> str:
        """Generate compelling article title"""
        prompt = f"""Generate a compelling article title for: {topic}

Requirements:
- Clear and specific
- Benefit-driven
- 50-60 characters
- Professional tone

Generate ONE title (no quotes):"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=30
            )

            return response.choices[0].message.content.strip().strip('"\'')

        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return topic

    def _generate_seo_title(self, keyword: str, content: str) -> str:
        """Generate SEO-optimized title"""
        prompt = f"""Generate an SEO-optimized title for an article about: {keyword}

Requirements:
- Include the exact keyword: "{keyword}"
- 50-60 characters (for SERP display)
- Compelling for human readers
- Professional tone

Generate ONE title (no quotes):"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=30
            )

            return response.choices[0].message.content.strip().strip('"\'')

        except Exception as e:
            logger.error(f"Error generating SEO title: {e}")
            return f"The Complete Guide to {keyword}"

    def _generate_meta_description(self, content: str, keyword: Optional[str] = None) -> str:
        """Generate meta description"""
        first_paragraph = content.split('\n\n')[0][:200]

        prompt = f"""Generate a meta description for this article:

First paragraph: {first_paragraph}
{f'Target keyword: {keyword}' if keyword else ''}

Requirements:
- 150-160 characters
- Include keyword if provided
- Compelling, encourages click
- Accurate summary

Generate meta description (no quotes):"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=60
            )

            return response.choices[0].message.content.strip().strip('"\'')

        except Exception as e:
            logger.error(f"Error generating meta description: {e}")
            return first_paragraph[:160]

    def _extract_keywords(self, main_keyword: str, content: str) -> List[str]:
        """Extract relevant keywords from content"""
        keywords = [main_keyword]

        # Add common variations
        words = main_keyword.split()
        if len(words) > 1:
            keywords.extend(words)

        return keywords[:10]

    def _assess_linkedin_quality(self, content: str) -> float:
        """Assess LinkedIn post quality (0-1 scale)"""
        score = 0.0

        # Check length
        word_count = len(content.split())
        if 150 <= word_count <= 250:
            score += 0.3
        elif 100 <= word_count <= 300:
            score += 0.2

        # Check for hook (short first line)
        first_line = content.split('\n')[0]
        if len(first_line.split()) <= 12:
            score += 0.2

        # Check for question/CTA at end
        if '?' in content[-100:] or any(cta in content[-100:].lower() for cta in ['what do you', 'share your', 'let me know']):
            score += 0.2

        # Check for specific examples/numbers
        if any(char.isdigit() for char in content):
            score += 0.15

        # Check paragraph structure (short paragraphs)
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) >= 3:
            score += 0.15

        return min(1.0, score)

    def _assess_article_quality(self, content: str, target_length: int) -> float:
        """Assess article quality (0-1 scale)"""
        score = 0.0

        # Check length
        word_count = len(content.split())
        length_ratio = word_count / target_length
        if 0.9 <= length_ratio <= 1.2:
            score += 0.3
        elif 0.7 <= length_ratio <= 1.4:
            score += 0.2

        # Check for structure (headers)
        header_count = content.count('##')
        if header_count >= 5:
            score += 0.2
        elif header_count >= 3:
            score += 0.1

        # Check for lists
        if '-' in content or content.count('\n-') > 3:
            score += 0.15

        # Check for examples/data
        if any(indicator in content.lower() for indicator in ['for example', 'according to', 'study shows', '%']):
            score += 0.15

        # Check for conclusion
        if any(word in content[-300:].lower() for word in ['conclusion', 'summary', 'in conclusion', 'to wrap up']):
            score += 0.2

        return min(1.0, score)

    def _parse_email_sequence(self, sequence_text: str) -> List[Dict[str, str]]:
        """Parse email sequence text into structured format"""
        emails = []

        # Simple parsing - in production, make this more robust
        email_blocks = sequence_text.split('---')

        for block in email_blocks:
            if 'SUBJECT:' in block:
                email = {}
                lines = block.split('\n')

                for i, line in enumerate(lines):
                    if line.startswith('SUBJECT:'):
                        email['subject'] = line.replace('SUBJECT:', '').strip()
                    elif line.startswith('BODY:'):
                        # Get everything after BODY: until CTA:
                        body_start = i + 1
                        body_lines = []
                        for j in range(body_start, len(lines)):
                            if lines[j].startswith('CTA:'):
                                break
                            body_lines.append(lines[j])
                        email['body'] = '\n'.join(body_lines).strip()
                    elif line.startswith('CTA:'):
                        email['cta'] = line.replace('CTA:', '').strip()
                    elif line.startswith('WAIT:'):
                        email['wait_days'] = line.replace('WAIT:', '').strip()

                if 'subject' in email and 'body' in email:
                    emails.append(email)

        return emails


# Example usage
if __name__ == "__main__":
    generator = ContentGenerator()

    # Test LinkedIn post
    post = generator.generate_linkedin_post(
        topic="AI automation in marketing",
        company_context="B2B SaaS company",
        tone="professional"
    )

    print(f"Quality Score: {post.quality_score}")
    print(f"\n{post.content}")
    print(f"\nHashtags: {' '.join(post.hashtags)}")
