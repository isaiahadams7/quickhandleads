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
                "keywords": [
                    "realtor",
                    "real estate agent",
                    "listing agent",
                    "buyer's agent",
                    "broker",
                    "real estate broker"
                ],
                "intent_phrases": [
                    "looking for a realtor",
                    "need a realtor",
                    "recommend a realtor",
                    "real estate agent recommendations",
                    "seeking a realtor",
                    "looking for a real estate agent"
                ],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["job", "hiring", "career"],
                "description": "Find real estate agents and realtors"
            },

            "contractors": {
                "keywords": [
                    "contractor",
                    "general contractor",
                    "licensed contractor",
                    "home improvement",
                    "handyman",
                    "remodeling",
                    "renovation",
                    "home renovation"
                ],
                "intent_phrases": [
                    "looking for a contractor",
                    "need a contractor",
                    "recommend a contractor",
                    "any contractor recommendations",
                    "looking for a handyman",
                    "need a handyman"
                ],
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
                    "finally a homeowner",
                    "offer accepted",
                    "under contract"
                ],
                "intent_phrases": [
                    "looking to buy a home",
                    "house hunting",
                    "first time buyer",
                    "buying a house",
                    "pre-approved for mortgage"
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
                    "pre-approved for mortgage",
                    "mortgage pre-approval"
                ],
                "intent_phrases": [
                    "first time buyer",
                    "buying my first home",
                    "looking to buy a home",
                    "house hunting",
                    "need a mortgage"
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
                    "want to list my house",
                    "sell my home",
                    "list my home"
                ],
                "intent_phrases": [
                    "need to sell my house",
                    "looking to sell my home",
                    "want to list my house",
                    "selling my home",
                    "need a realtor"
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
                    "too much house",
                    "retiring and moving",
                    "downsizing house"
                ],
                "intent_phrases": [
                    "looking to downsize",
                    "downsizing our home",
                    "moving to a smaller house",
                    "sell family home",
                    "empty nest downsizing"
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
                    "need contractor",
                    "home remodel",
                    "renovation project"
                ],
                "intent_phrases": [
                    "need a contractor",
                    "looking for a contractor",
                    "need renovation",
                    "need to remodel",
                    "remodeling contractor"
                ],
                "sites": SearchTemplates.SOCIAL_SITES,
                "exclude_terms": ["contractor", "business", "hire me"],
                "description": "Find people needing home renovations"
            },

            "home_repair": {
                "keywords": [
                    "need handyman",
                    "home repair needed",
                    "roof repair",
                    "roof leak",
                    "leaking roof",
                    "plumbing leak",
                    "plumbing issue",
                    "water heater",
                    "pipe burst",
                    "electrical problem",
                    "electrical repair",
                    "hvac repair",
                    "ac repair",
                    "furnace repair",
                    "sump pump",
                    "foundation crack",
                    "drywall repair",
                    "water damage"
                ],
                "intent_phrases": [
                    "need repair",
                    "need a handyman",
                    "looking for repair",
                    "fix my",
                    "repair needed",
                    "plumber recommendation",
                    "electrician recommendation",
                    "roof repair",
                    "plumbing issue",
                    "hvac repair",
                    "water heater repair"
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
                    "looking for housing in",
                    "moving for work",
                    "relocation"
                ],
                "intent_phrases": [
                    "moving to",
                    "relocating to",
                    "just moved to",
                    "looking for housing",
                    "relocation assistance"
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
                    "house flipping",
                    "cash buyer",
                    "real estate investor"
                ],
                "intent_phrases": [
                    "looking to invest",
                    "seeking investment property",
                    "buying rental property",
                    "fix and flip",
                    "real estate investor"
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
                    "sell house quickly",
                    "motivated seller",
                    "need to sell quickly"
                ],
                "intent_phrases": [
                    "need to sell fast",
                    "sell my house quickly",
                    "urgent sale",
                    "motivated seller",
                    "sell fast"
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
