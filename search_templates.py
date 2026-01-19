"""
Pre-built search templates for finding different types of leads.
"""
from typing import Dict, List


class SearchTemplates:
    """Collection of search query templates for different lead types."""

    # Common email domains to search for
    EMAIL_DOMAINS = [
        "@gmail.com", "@outlook.com", "@hotmail.com", "@live.com",
        "@yahoo.com", "@icloud.com", "@me.com", "@aol.com",
        "@comcast.net", "@verizon.net", "@att.net"
    ]

    # Common social media sites
    SOCIAL_SITES = [
        "instagram.com",
        "facebook.com",
        "twitter.com",
        "linkedin.com",
        "reddit.com",
        "tiktok.com",
        "nextdoor.com",
        "youtube.com",
        "pinterest.com",
        "craigslist.org"
    ]

    @staticmethod
    def get_template(template_name: str) -> Dict:
        """
        Get a search template by name.

        Returns a dictionary with:
        - keywords: List of search keywords
        - sites: Sites to search
        - exclude_terms: Terms to exclude
        - description: What this search finds
        """
        templates = {
            # SERVICE PROVIDERS (e.g., realtors, contractors)
            "realtors": {
                "keywords": ["realtor", "real estate agent", "real estate"],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["job", "hiring", "career"],
                "description": "Find real estate agents and realtors"
            },

            "contractors": {
                "keywords": ["contractor", "home improvement", "handyman", "renovation"],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["job", "hiring", "career"],
                "description": "Find contractors and home improvement professionals"
            },

            # POTENTIAL CLIENTS - HOME BUYERS
            "home_buyers": {
                "keywords": [
                    "just bought a house",
                    "new homeowner",
                    "bought my first home",
                    "closed on my house",
                    "new home purchase",
                    "house closing",
                    "finally a homeowner"
                ],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["realtor", "agent", "for sale", "listing"],
                "description": "Find people who recently bought homes"
            },

            "first_time_buyers": {
                "keywords": [
                    "first time home buyer",
                    "first home",
                    "buying my first house",
                    "looking to buy a home",
                    "house hunting",
                    "pre-approved for mortgage"
                ],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["realtor", "agent", "tips", "advice"],
                "description": "Find first-time home buyers"
            },

            # POTENTIAL CLIENTS - HOME SELLERS
            "home_sellers": {
                "keywords": [
                    "selling my house",
                    "need to sell my home",
                    "house for sale",
                    "looking for a realtor",
                    "need a real estate agent",
                    "want to list my house"
                ],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["realtor", "agent", "I can help"],
                "description": "Find people looking to sell their homes"
            },

            "downsizing": {
                "keywords": [
                    "downsizing our home",
                    "empty nester",
                    "moving to smaller house",
                    "selling family home",
                    "too much house"
                ],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["realtor", "agent"],
                "description": "Find people downsizing/selling homes"
            },

            # POTENTIAL CLIENTS - HOME IMPROVEMENT
            "renovation_needed": {
                "keywords": [
                    "need renovation",
                    "fixer upper",
                    "home improvement needed",
                    "need to remodel",
                    "kitchen renovation",
                    "bathroom remodel",
                    "need contractor"
                ],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["contractor", "business", "hire me"],
                "description": "Find people needing home renovations"
            },

            "home_repair": {
                "keywords": [
                    "need handyman",
                    "home repair needed",
                    "looking for contractor",
                    "roof repair",
                    "plumbing issue",
                    "electrical problem",
                    "need help with"
                ],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["contractor", "business", "hire me"],
                "description": "Find people needing home repairs"
            },

            # POTENTIAL CLIENTS - MOVERS
            "relocating": {
                "keywords": [
                    "moving to",
                    "relocating to",
                    "transferring to",
                    "new job in",
                    "just moved to",
                    "looking for housing in"
                ],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["realtor", "agent", "moving company"],
                "description": "Find people relocating to new areas"
            },

            # POTENTIAL CLIENTS - INVESTORS
            "investors": {
                "keywords": [
                    "investment property",
                    "rental property",
                    "looking to invest in real estate",
                    "building portfolio",
                    "fix and flip",
                    "house flipping"
                ],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["course", "coaching", "mentor"],
                "description": "Find real estate investors"
            },

            # POTENTIAL CLIENTS - URGENT SELLERS
            "urgent_sellers": {
                "keywords": [
                    "need to sell fast",
                    "quick sale needed",
                    "divorce selling house",
                    "inherited house",
                    "foreclosure",
                    "sell house quickly"
                ],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["buy houses", "we buy", "cash offer"],
                "description": "Find people who need to sell quickly"
            },
        }

        if template_name not in templates:
            available = ", ".join(templates.keys())
            raise ValueError(
                f"Template '{template_name}' not found. "
                f"Available templates: {available}"
            )

        return templates[template_name]

    @staticmethod
    def list_templates() -> Dict[str, str]:
        """Get a dictionary of all template names and their descriptions."""
        template_names = [
            "realtors", "contractors",
            "home_buyers", "first_time_buyers",
            "home_sellers", "downsizing",
            "renovation_needed", "home_repair",
            "relocating", "investors", "urgent_sellers"
        ]

        return {
            name: SearchTemplates.get_template(name)["description"]
            for name in template_names
        }

    @staticmethod
    def list_by_category() -> Dict[str, List[str]]:
        """Get templates organized by category."""
        return {
            "Service Providers": [
                "realtors",
                "contractors"
            ],
            "Home Buyers": [
                "home_buyers",
                "first_time_buyers"
            ],
            "Home Sellers": [
                "home_sellers",
                "downsizing",
                "urgent_sellers"
            ],
            "Home Improvement": [
                "renovation_needed",
                "home_repair"
            ],
            "Other": [
                "relocating",
                "investors"
            ]
        }
