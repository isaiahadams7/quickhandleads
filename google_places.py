"""
Google Places API client for geo-targeted business searches.
"""
import os
import time
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()


GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_TEXTSEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


class GooglePlacesClient:
    """Client for Google Places API (Text Search + Details)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GOOGLE_PLACES_API_KEY is required for Places API searches."
            )

    def geocode(self, location: str) -> Optional[Tuple[float, float]]:
        if not location:
            return None
        params = {"address": location, "key": self.api_key}
        resp = requests.get(GEOCODE_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None
        loc = results[0]["geometry"]["location"]
        return loc["lat"], loc["lng"]

    def text_search(
        self,
        query: str,
        location: Optional[Tuple[float, float]] = None,
        radius_meters: Optional[int] = None,
        pagetoken: Optional[str] = None
    ) -> Dict:
        params = {"query": query, "key": self.api_key}
        if location:
            params["location"] = f"{location[0]},{location[1]}"
        if radius_meters:
            params["radius"] = radius_meters
        if pagetoken:
            params["pagetoken"] = pagetoken
        resp = requests.get(PLACES_TEXTSEARCH_URL, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def place_details(self, place_id: str) -> Dict:
        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,website",
            "key": self.api_key
        }
        resp = requests.get(PLACE_DETAILS_URL, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def search_locations(
        self,
        base_query: str,
        locations: List[str],
        max_results: int = 30,
        radius_miles: int = 25,
        delay_seconds: float = 2.0
    ) -> List[Dict]:
        results: List[Dict] = []
        seen_place_ids = set()
        radius_meters = int(radius_miles * 1609.34)

        for loc in locations:
            coords = self.geocode(loc)
            if not coords:
                continue

            query = f"{base_query} in {loc}".strip()
            next_token = None
            while len(results) < max_results:
                data = self.text_search(
                    query=query,
                    location=coords,
                    radius_meters=radius_meters,
                    pagetoken=next_token
                )
                for item in data.get("results", []):
                    place_id = item.get("place_id")
                    if not place_id or place_id in seen_place_ids:
                        continue
                    seen_place_ids.add(place_id)
                    results.append(item)
                    if len(results) >= max_results:
                        break

                next_token = data.get("next_page_token")
                if not next_token or len(results) >= max_results:
                    break
                time.sleep(delay_seconds)

            if len(results) >= max_results:
                break

        return results


def places_query_for_template(template_name: str) -> str:
    """Build a tight query string for Places based on template."""
    primary_terms = {
        "realtors": "realtor",
        "contractors": "contractor",
        "investors": "real estate investor"
    }
    base = primary_terms.get(template_name, template_name.replace("_", " "))
    return base


def normalize_places_result(place: Dict) -> Dict:
    place_id = place.get("place_id", "")
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else ""
    return {
        "title": place.get("name", ""),
        "link": maps_url,
        "snippet": place.get("formatted_address", ""),
        "displayLink": "google.com"
    }
