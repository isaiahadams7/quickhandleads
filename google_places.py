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
PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACE_DETAILS_URL = "https://places.googleapis.com/v1/places/"


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
        pagetoken: Optional[str] = None,
        max_results: int = 20
    ) -> Dict:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,nextPageToken"
        }
        payload: Dict = {
            "textQuery": query,
            "maxResultCount": max_results
        }
        if location and radius_meters:
            payload["locationBias"] = {
                "circle": {
                    "center": {"latitude": location[0], "longitude": location[1]},
                    "radius": radius_meters
                }
            }
        if pagetoken:
            payload["pageToken"] = pagetoken
        resp = requests.post(PLACES_SEARCH_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def place_details(self, place_id: str) -> Dict:
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "id,displayName,formattedAddress,websiteUri,internationalPhoneNumber"
        }
        params = {
            "fields": "displayName,formattedAddress,websiteUri,internationalPhoneNumber"
        }
        resp = requests.get(f"{PLACE_DETAILS_URL}{place_id}", headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def search_locations(
        self,
        base_query: str,
        locations: List[str],
        max_results: int = 30,
        radius_miles: int = 25,
        delay_seconds: float = 2.0
    ) -> Tuple[List[Dict], Dict]:
        results: List[Dict] = []
        seen_place_ids = set()
        radius_meters = int(radius_miles * 1609.34)

        stats = {
            "locations_total": len(locations),
            "locations_geocoded": 0,
            "last_status": None
        }

        for loc in locations:
            coords = self.geocode(loc)
            if not coords:
                continue
            stats["locations_geocoded"] += 1

            query = f"{base_query} in {loc}".strip()
            next_token = None
            while len(results) < max_results:
                data = self.text_search(
                    query=query,
                    location=coords,
                    radius_meters=radius_meters,
                    pagetoken=next_token,
                    max_results=min(20, max_results - len(results))
                )
                stats["last_status"] = data.get("status") or data.get("error", {}).get("message")
                for item in data.get("places", []):
                    place_id = item.get("id")
                    if not place_id or place_id in seen_place_ids:
                        continue
                    seen_place_ids.add(place_id)
                    results.append(item)
                    if len(results) >= max_results:
                        break

                next_token = data.get("nextPageToken")
                if not next_token or len(results) >= max_results:
                    break
                time.sleep(delay_seconds)

            if len(results) >= max_results:
                break

        return results, stats


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
    place_id = place.get("id", "")
    display_name = place.get("displayName", {}).get("text", "")
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else ""
    return {
        "title": display_name,
        "link": maps_url,
        "snippet": place.get("formattedAddress", ""),
        "displayLink": "google.com"
    }
