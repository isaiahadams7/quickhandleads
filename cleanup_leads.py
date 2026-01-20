#!/usr/bin/env python3
"""
Cleanup Supabase leads with strict rules:
1) Delete Reddit leads older than 60 days or missing post_created_at.
Default is dry-run; use --apply to delete.
"""
import argparse
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

DEFAULT_TIMEOUT = 20
REDDIT_MAX_AGE_DAYS = 60


def fetch_page_text(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    if not url or not url.startswith(("http://", "https://")):
        return ""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code >= 400:
            return ""
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(soup.stripped_strings)
        return text[:20000]
    except requests.RequestException:
        return ""


def fetch_reddit_created_utc(url: str) -> float:
    if not url or "reddit.com" not in url:
        return 0
    json_url = url.rstrip("/") + ".json"
    try:
        resp = requests.get(json_url, headers={"User-Agent": "LeadFinderBot/1.0"}, timeout=DEFAULT_TIMEOUT)
        if resp.status_code >= 400:
            return 0
        data = resp.json()
        if isinstance(data, list) and data:
            children = data[0].get("data", {}).get("children", [])
            if children:
                post = children[0].get("data", {})
                return float(post.get("created_utc") or 0)
    except Exception:
        return 0
    return 0


def load_all_leads(supabase) -> List[Dict]:
    all_rows: List[Dict] = []
    offset = 0
    batch_size = 500
    while True:
        res = (
            supabase.table("leads")
            .select("id,template,company_name,website_url,post_created_at,lead_source")
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        rows = res.data or []
        all_rows.extend(rows)
        if len(rows) < batch_size:
            break
        offset += batch_size
    return all_rows


def should_delete(lead: Dict) -> Tuple[bool, str]:
    url = lead.get("website_url") or ""
    source = (lead.get("lead_source") or "").lower()
    # Rule 1: Reddit recency
    if "reddit.com" in url or source == "reddit":
        created_utc = fetch_reddit_created_utc(url)
        if not created_utc:
            return True, "reddit_missing_date"
        cutoff = datetime.now(timezone.utc).timestamp() - (REDDIT_MAX_AGE_DAYS * 86400)
        if created_utc < cutoff:
            return True, "reddit_too_old"

    return False, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup leads with strict rules.")
    parser.add_argument("--apply", action="store_true", help="Delete matching leads")
    args = parser.parse_args()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("Missing SUPABASE_URL or SUPABASE_KEY in environment.")
        return 1

    supabase = create_client(supabase_url, supabase_key)
    leads = load_all_leads(supabase)

    to_delete = []
    reasons: Dict[str, int] = {}

    for lead in leads:
        delete, reason = should_delete(lead)
        if delete:
            to_delete.append((lead, reason))
            reasons[reason] = reasons.get(reason, 0) + 1
        time.sleep(0.15)

    print("CLEANUP REPORT")
    print(f"Total leads scanned: {len(leads)}")
    print(f"Candidates to delete: {len(to_delete)}")
    for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
        print(f"  {reason}: {count}")

    print("\nSample candidates (up to 20):")
    for lead, reason in to_delete[:20]:
        print(f"- id={lead.get('id')} reason={reason} url={lead.get('website_url')!r} template={lead.get('template')!r}")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to delete.")
        return 0

    ids = [lead.get("id") for lead, _ in to_delete if lead.get("id") is not None]
    if not ids:
        print("\nNo leads to delete.")
        return 0

    supabase.table("leads").delete().in_("id", ids).execute()
    print(f"\nDeleted {len(ids)} leads.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
