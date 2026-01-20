#!/usr/bin/env python3
"""
Backfill Reddit post_created_at in Supabase leads.
Reads SUPABASE_URL and SUPABASE_KEY from environment.
"""
import os
import time
import requests
from supabase import create_client

DEFAULT_TIMEOUT = 20


def load_all_leads(supabase):
    all_rows = []
    offset = 0
    batch_size = 500
    while True:
        res = (
            supabase.table("leads")
            .select("id,website_url")
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        rows = res.data or []
        all_rows.extend(rows)
        if len(rows) < batch_size:
            break
        offset += batch_size
    return all_rows


def fetch_reddit_created_utc(url: str) -> float:
    if not url or "reddit.com" not in url:
        return 0
    json_url = url.rstrip("/") + ".json"
    try:
        resp = requests.get(
            json_url,
            headers={"User-Agent": "LeadFinderBot/1.0"},
            timeout=DEFAULT_TIMEOUT
        )
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


def main() -> int:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("Missing SUPABASE_URL or SUPABASE_KEY in environment.")
        return 1

    supabase = create_client(supabase_url, supabase_key)
    leads = load_all_leads(supabase)

    updated = 0
    for lead in leads:
        url = lead.get("website_url") or ""
        if "reddit.com" not in url:
            continue
        created_utc = fetch_reddit_created_utc(url)
        if not created_utc:
            continue
        iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(created_utc))
        supabase.table("leads").update({"post_created_at": iso}).eq("id", lead.get("id")).execute()
        updated += 1
        time.sleep(0.2)

    print(f"Backfill complete. Updated {updated} reddit leads with post_created_at.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
