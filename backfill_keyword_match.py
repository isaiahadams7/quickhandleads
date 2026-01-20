#!/usr/bin/env python3
"""
Backfill keyword_match in Supabase leads using page text + template keywords.
Reads SUPABASE_URL and SUPABASE_KEY from environment (supports .env via dotenv).
"""
import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

from search_templates import SearchTemplates

load_dotenv()

DEFAULT_TIMEOUT = 20
MAX_TEXT_CHARS = 20000


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
        return text[:MAX_TEXT_CHARS]
    except requests.RequestException:
        return ""


def matches_keywords(text: str, keywords: list) -> bool:
    if not keywords:
        return True
    text_lower = (text or "").lower()
    return any(kw.lower() in text_lower for kw in keywords)


def load_all_leads(supabase):
    all_rows = []
    offset = 0
    batch_size = 500
    while True:
        res = (
            supabase.table("leads")
            .select("id,template,company_name,website_url")
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        rows = res.data or []
        all_rows.extend(rows)
        if len(rows) < batch_size:
            break
        offset += batch_size
    return all_rows


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
        template = lead.get("template") or ""
        try:
            tmpl = SearchTemplates.get_template(template)
        except Exception:
            tmpl = {"keywords": []}

        url = lead.get("website_url") or ""
        page_text = fetch_page_text(url)
        combined = f"{lead.get('company_name') or ''} {page_text} {url}"
        keyword_match = matches_keywords(combined, tmpl.get("keywords", []))

        supabase.table("leads").update({"keyword_match": bool(keyword_match)}).eq("id", lead.get("id")).execute()
        updated += 1
        time.sleep(0.1)

    print(f"Backfill complete. Updated {updated} leads.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
