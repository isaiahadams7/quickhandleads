"""
Google Custom Search API client for finding real estate contacts and leads.
"""
import os
import time
import re
from typing import List, Dict, Optional, Set, Tuple
import requests
from dotenv import load_dotenv
from search_templates import SearchTemplates

# Load environment variables
load_dotenv()


class GoogleSearchClient:
    """Client for Google Custom Search API."""

    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    DEFAULT_PARAMS = {
        "gl": "us",
        "hl": "en",
        "cr": "countryUS"
    }

    def __init__(self, api_key: Optional[str] = None, cse_id: Optional[str] = None):
        """
        Initialize the Google Search client.

        Args:
            api_key: Google API key (or reads from GOOGLE_API_KEY env var)
            cse_id: Custom Search Engine ID (or reads from GOOGLE_CSE_ID env var)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.cse_id = cse_id or os.getenv("GOOGLE_CSE_ID")

        if not self.api_key or not self.cse_id:
            raise ValueError(
                "API key and CSE ID are required. "
                "Set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables "
                "or pass them as arguments."
            )

    def build_query(
        self,
        keywords: List[str],
        locations: List[str],
        sites: Optional[List[str]] = None,
        email_domains: Optional[List[str]] = None,
        exclude_terms: Optional[List[str]] = None
    ) -> str:
        """
        Build a search query from components.

        Args:
            keywords: List of keywords (e.g., ["realtor", "real estate agent"])
            locations: List of locations (e.g., ["Boston MA", "Cambridge MA"])
            sites: List of sites to search (e.g., ["instagram.com", "facebook.com"])
            email_domains: List of email domains to include
            exclude_terms: Terms to exclude from results

        Returns:
            Formatted search query string
        """
        query_parts = []

        # Add site restrictions
        if sites:
            site_query = " OR ".join([f"site:{site}" for site in sites])
            query_parts.append(f"({site_query})")

        # Add keywords
        if keywords:
            keywords_query = " OR ".join([f'"{kw}"' for kw in keywords])
            query_parts.append(f"({keywords_query})")

        # Add email domains
        if email_domains:
            email_query = " OR ".join([f'"{domain}"' for domain in email_domains])
            query_parts.append(f"({email_query})")

        # Add locations
        if locations:
            location_query = " OR ".join([f'"{loc}"' for loc in locations])
            query_parts.append(f"({location_query})")

        # Join main query parts
        query = " ".join(query_parts)

        # Add exclusions
        if exclude_terms:
            exclusions = " ".join([f"-{term}" for term in exclude_terms])
            query = f"{query} {exclusions}"

        return query.strip()

    def search(
        self,
        query: str,
        num_results: int = 10,
        start_index: int = 1
    ) -> List[Dict]:
        """
        Execute a search query using Google Custom Search API.

        Args:
            query: The search query string
            num_results: Number of results to return (max 10 per request)
            start_index: Starting index for pagination (1-based)

        Returns:
            List of search result dictionaries
        """
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": min(num_results, 10),  # API max is 10 per request
            "start": start_index
        }
        params.update(self.DEFAULT_PARAMS)

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "displayLink": item.get("displayLink", "")
                })

            return results

        except requests.exceptions.RequestException as e:
            print(f"Error making search request: {e}")
            return []
        except ValueError as e:
            print(f"Error parsing response JSON: {e}")
            return []


US_STATES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming"
}


def _normalize(text: str) -> str:
    return text.lower().strip() if text else ""


def _parse_locations(locations: List[str]) -> Tuple[Set[str], Set[str], Set[str]]:
    allowed_cities: Set[str] = set()
    allowed_state_abbrevs: Set[str] = set()
    allowed_state_names: Set[str] = set()

    for loc in locations:
        cleaned = loc.replace(",", " ").strip()
        parts = [p for p in cleaned.split() if p]
        if not parts:
            continue

        state_token = parts[-1].upper()
        city_tokens = parts[:-1]
        if state_token in US_STATES:
            allowed_state_abbrevs.add(state_token)
            allowed_state_names.add(US_STATES[state_token].lower())
        else:
            state_name = " ".join(parts[-2:]).lower()
            if state_name in [name.lower() for name in US_STATES.values()]:
                allowed_state_names.add(state_name)
                if len(parts) >= 2:
                    city_tokens = parts[:-2]
            else:
                city_tokens = parts

        if city_tokens:
            allowed_cities.add(" ".join(city_tokens).lower())

    return allowed_cities, allowed_state_abbrevs, allowed_state_names


def _text_mentions_any(text: str, phrases: Set[str]) -> bool:
    if not text or not phrases:
        return False
    for phrase in phrases:
        if phrase and re.search(rf"\b{re.escape(phrase)}\b", text):
            return True
    return False


def _abbrev_mentions(text: str, abbrevs: Set[str]) -> bool:
    if not text or not abbrevs:
        return False
    pattern = r"(?<![A-Za-z])(" + "|".join(sorted(abbrevs)) + r")(?![A-Za-z])"
    return re.search(pattern, text) is not None


def rank_results_by_locations(
    results: List[Dict],
    locations: List[str]
) -> List[Dict]:
    """
    Rank results by location relevance.
    Priority: allowed locations > no location mention > other US state mention.
    """
    if not results or not locations:
        return results

    allowed_cities, allowed_state_abbrevs, allowed_state_names = _parse_locations(locations)

    disallowed_state_abbrevs = set(US_STATES.keys()) - allowed_state_abbrevs
    disallowed_state_names = {name.lower() for name in US_STATES.values()} - allowed_state_names

    ranked = []
    for result in results:
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        link = result.get("link", "")
        combined = f"{title} {snippet} {link}"
        combined_lower = _normalize(combined)

        has_allowed_city = _text_mentions_any(combined_lower, allowed_cities)
        has_allowed_state_name = _text_mentions_any(combined_lower, allowed_state_names)
        has_allowed_state_abbrev = _abbrev_mentions(combined, allowed_state_abbrevs)

        has_other_state_name = _text_mentions_any(combined_lower, disallowed_state_names)
        has_other_state_abbrev = _abbrev_mentions(combined, disallowed_state_abbrevs)

        if has_allowed_city or has_allowed_state_name or has_allowed_state_abbrev:
            score = 2
        elif has_other_state_name or has_other_state_abbrev:
            score = 0
        else:
            score = 1

        ranked.append((score, result))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in ranked]


def result_matches_locations(result: Dict, locations: List[str]) -> bool:
    """Return True if the result mentions any allowed location."""
    if not locations:
        return False

    allowed_cities, allowed_state_abbrevs, allowed_state_names = _parse_locations(locations)

    title = result.get("title", "")
    snippet = result.get("snippet", "")
    link = result.get("link", "")
    combined = f"{title} {snippet} {link}"
    combined_lower = _normalize(combined)

    return (
        _text_mentions_any(combined_lower, allowed_cities)
        or _text_mentions_any(combined_lower, allowed_state_names)
        or _abbrev_mentions(combined, allowed_state_abbrevs)
    )

    def search_multiple_pages(
        self,
        query: str,
        total_results: int = 100,
        delay: float = 1.0
    ) -> List[Dict]:
        """
        Search multiple pages of results (handles pagination).

        Args:
            query: The search query string
            total_results: Total number of results to retrieve
            delay: Delay in seconds between requests to avoid rate limiting

        Returns:
            List of all search result dictionaries
        """
        all_results = []
        results_per_page = 10  # API maximum
        pages_needed = (total_results + results_per_page - 1) // results_per_page

        print(f"Fetching up to {total_results} results ({pages_needed} pages)...")

        for page in range(pages_needed):
            start_index = page * results_per_page + 1
            print(f"Fetching page {page + 1}/{pages_needed} (results {start_index}-{start_index + results_per_page - 1})...")

            results = self.search(query, num_results=results_per_page, start_index=start_index)

            if not results:
                print(f"No more results found at page {page + 1}")
                break

            all_results.extend(results)

            # Add delay between requests to be respectful to the API
            if page < pages_needed - 1 and results:
                time.sleep(delay)

        print(f"Retrieved {len(all_results)} total results")
        return all_results


def create_search_from_template(
    template_name: str,
    locations: List[str],
    include_emails: bool = True
) -> str:
    """
    Create a search query using a pre-built template.

    Args:
        template_name: Name of the template to use (e.g., "home_buyers", "realtors")
        locations: List of locations to search
        include_emails: Whether to include email domain search terms

    Returns:
        Formatted search query
    """
    template = SearchTemplates.get_template(template_name)

    client = GoogleSearchClient()

    email_domains = None
    if include_emails:
        email_domains = SearchTemplates.EMAIL_DOMAINS

    return client.build_query(
        keywords=template["keywords"],
        locations=locations,
        sites=template["sites"],
        email_domains=email_domains,
        exclude_terms=template["exclude_terms"]
    )


def create_realtor_search_query(
    locations: List[str],
    sites: Optional[List[str]] = None,
    email_domains: Optional[List[str]] = None
) -> str:
    """
    Helper function to create a query for finding real estate agents.
    (Kept for backward compatibility)

    Args:
        locations: List of locations to search
        sites: Sites to search (defaults to Instagram and Facebook)
        email_domains: Email domains to search for (defaults to common providers)

    Returns:
        Formatted search query
    """
    if sites is None:
        sites = ["instagram.com", "facebook.com"]

    if email_domains is None:
        email_domains = [
            "@gmail.com", "@outlook.com", "@hotmail.com", "@live.com",
            "@yahoo.com", "@icloud.com", "@me.com", "@aol.com",
            "@comcast.net", "@verizon.net", "@att.net"
        ]

    keywords = ["realtor", "real estate agent", "real estate"]
    exclude_terms = ["job", "hiring"]

    client = GoogleSearchClient()
    return client.build_query(
        keywords=keywords,
        locations=locations,
        sites=sites,
        email_domains=email_domains,
        exclude_terms=exclude_terms
    )
