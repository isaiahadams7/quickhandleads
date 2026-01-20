"""
Streamlit Dashboard V2 for Real Estate Lead Finder
Enhanced with database, duplicate detection, and better viewing
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
from datetime import datetime, timezone
from io import BytesIO

# Import our existing modules
from google_search import (
    GoogleSearchClient,
    create_search_from_template,
    rank_results_by_locations,
    result_matches_locations,
    build_reddit_subreddits,
    reddit_exclude_terms
)
from google_places import GooglePlacesClient, normalize_places_result, places_query_for_template
from contact_extractor import ContactExtractor
from search_templates import SearchTemplates
from database import get_database as get_db_instance

# Page configuration
st.set_page_config(
    page_title="Real Estate Lead Finder Pro",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .new-badge {
        background-color: #28a745;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .duplicate-badge {
        background-color: #ffc107;
        color: black;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def get_database():
    db_instance = get_db_instance()
    # Display database type in sidebar for debugging
    db_type = "Supabase ☁️" if "Supabase" in type(db_instance).__name__ else "SQLite 📁"
    return db_instance, db_type

db, db_type = get_database()

# Show database status at the top
st.sidebar.markdown(f"**Database:** {db_type}")

# Initialize session state
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'search'  # 'search' or 'database'


def check_api_credentials():
    """Check if API credentials are configured."""
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    return api_key and cse_id


def get_download_data(df, file_format="excel"):
    """Generate download data for dataframe."""
    if file_format == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Leads')
        output.seek(0)
        return output.getvalue()
    else:  # CSV
        return df.to_csv(index=False).encode('utf-8')


def apply_location_badge(df: pd.DataFrame) -> pd.DataFrame:
    """Add a small badge to the name/company fields when location matches."""
    if "location_match" not in df.columns:
        df["location_match"] = False

    def add_badge(row: pd.Series) -> pd.Series:
        if not row.get("location_match"):
            return row
        if row.get("company_name"):
            row["company_name"] = f"📍 {row['company_name']}"
        elif row.get("first_name"):
            row["first_name"] = f"📍 {row['first_name']}"
        elif row.get("last_name"):
            row["last_name"] = f"📍 {row['last_name']}"
        return row

    return df.apply(add_badge, axis=1)


def apply_quality_badges(df: pd.DataFrame) -> pd.DataFrame:
    """Add compact badges to highlight lead quality signals."""
    def add_badges(row: pd.Series) -> pd.Series:
        badges = []
        if row.get("good_lead"):
            badges.append("✅")
        if row.get("keyword_match") is False:
            badges.append("⚠️")
        if row.get("intent_match"):
            badges.append("🎯")
        if row.get("location_match"):
            badges.append("📍")
        if row.get("lead_recency_days", 9999) <= 7:
            badges.append("🕒")
        if row.get("contact_score", 0) >= 10:
            badges.append("☎")
        if row.get("lead_source") == "places":
            badges.append("🏢")

        if not badges:
            return row

        badge_str = " ".join(badges)
        if row.get("company_name"):
            row["company_name"] = f"{badge_str} {row['company_name']}"
        elif row.get("first_name"):
            row["first_name"] = f"{badge_str} {row['first_name']}"
        elif row.get("last_name"):
            row["last_name"] = f"{badge_str} {row['last_name']}"
        return row

    return df.apply(add_badges, axis=1)


def lead_location_match(lead: pd.Series) -> bool:
    """Best-effort location match using stored locations and lead fields."""
    existing = lead.get("location_match")
    if isinstance(existing, bool):
        return existing
    locations_str = lead.get("locations", "") or ""
    locations = [loc.strip() for loc in locations_str.split(",") if loc.strip()]
    result_stub = {
        "title": lead.get("company_name", "") or "",
        "snippet": "",
        "link": lead.get("website_url", "") or ""
    }
    return result_matches_locations(result_stub, locations)


def lead_keyword_match(lead: pd.Series) -> bool:
    """Best-effort keyword match using template keywords and stored fields."""
    template_name = lead.get("template") or ""
    try:
        tmpl = SearchTemplates.get_template(template_name)
    except Exception:
        return False
    combined = f"{lead.get('company_name') or ''} {lead.get('website_url') or ''}"
    return any(kw.lower() in combined.lower() for kw in tmpl.get("keywords", []))


def detect_intent_match(text: str, phrases: list) -> bool:
    text_lower = (text or "").lower()
    return any(phrase in text_lower for phrase in (phrases or []))


def lead_source_from_link(link: str) -> str:
    if not link:
        return "cse"
    link_lower = link.lower()
    if "reddit.com" in link_lower:
        return "reddit"
    if "facebook.com" in link_lower:
        return "facebook"
    if "instagram.com" in link_lower:
        return "instagram"
    if "linkedin.com" in link_lower:
        return "linkedin"
    if "nextdoor.com" in link_lower:
        return "nextdoor"
    if "tiktok.com" in link_lower:
        return "tiktok"
    if "youtube.com" in link_lower:
        return "youtube"
    if "pinterest.com" in link_lower:
        return "pinterest"
    if "craigslist.org" in link_lower:
        return "craigslist"
    return "cse"


def compute_lead_score(row: pd.Series) -> pd.Series:
    """Compute a 0-100 lead score and helper fields for display."""
    score = 0
    intent_match = bool(row.get("intent_match"))
    location_match = bool(row.get("location_match"))
    if location_match:
        score += 35
    if intent_match:
        score += 30

    recency_days = row.get("lead_recency_days", 9999)
    if recency_days <= 7:
        score += 20
    elif recency_days <= 30:
        score += 15
    elif recency_days <= 60:
        score += 10
    elif recency_days <= 90:
        score += 5

    contact_score = 0
    if row.get("email"):
        contact_score += 7
    if row.get("phone"):
        contact_score += 7
    if row.get("website_url"):
        contact_score += 6
    score += contact_score

    keyword_match = row.get("keyword_match")
    intent_match = bool(row.get("intent_match"))
    if keyword_match is True:
        score += 8
    elif keyword_match is False:
        score -= 5

    # Penalize non-Reddit leads that lack intent/keyword match instead of deleting.
    if row.get("lead_source") not in {"reddit", "places"}:
        if not intent_match and not keyword_match:
            score -= 12

    source = row.get("lead_source")
    if source == "places":
        score += 8
    elif source == "linkedin":
        score += 5
    elif source == "facebook":
        score += 4
    elif source == "instagram":
        score += 3
    elif source == "reddit":
        score += 2
    else:
        score += 3

    good_lead = intent_match and location_match and recency_days <= 60
    if good_lead:
        score += 10

    # Enforce stricter scoring: no "good" score without intent match.
    if not intent_match:
        score = min(score, 60)

    score = max(0, min(100, score))

    row["lead_score"] = int(score)
    row["contact_score"] = contact_score
    row["good_lead"] = good_lead
    return row


def run_cse_search(
    client: GoogleSearchClient,
    query: str,
    total_results: int,
    delay: float,
    date_restrict: str = None
) -> list:
    """Compat wrapper for older GoogleSearchClient versions without pagination."""
    if hasattr(client, "search_multiple_pages"):
        return client.search_multiple_pages(query, total_results=total_results, delay=delay, date_restrict=date_restrict)

    results = []
    results_per_page = 10
    pages_needed = (total_results + results_per_page - 1) // results_per_page
    for page in range(pages_needed):
        start_index = page * results_per_page + 1
        results.extend(
            client.search(
                query,
                num_results=results_per_page,
                start_index=start_index,
                date_restrict=date_restrict
            )
        )
        if page < pages_needed - 1:
            time.sleep(delay)
    return results


def filter_recent_reddit_results(results: list, max_age_days: int = 60) -> tuple:
    """Drop Reddit results older than max_age_days using Reddit JSON endpoints."""
    import json
    import requests

    cutoff = datetime.now(timezone.utc).timestamp() - (max_age_days * 86400)
    filtered = []
    meta = {}

    for result in results:
        link = result.get("link", "")
        if "reddit.com" not in link:
            filtered.append(result)
            continue
        json_url = link.rstrip("/") + ".json"
        try:
            resp = requests.get(json_url, headers={"User-Agent": "LeadFinderBot/1.0"}, timeout=15)
            if resp.status_code >= 400:
                filtered.append(result)
                continue
            data = resp.json()
            post = None
            if isinstance(data, list) and data:
                children = data[0].get("data", {}).get("children", [])
                if children:
                    post = children[0].get("data", {})
            created = post.get("created_utc") if post else None
            if created:
                meta[link] = created
            if created and created >= cutoff:
                filtered.append(result)
            # If we cannot verify recency, drop it for strictness.
        except (requests.RequestException, json.JSONDecodeError):
            pass

        time.sleep(0.2)

    return filtered, meta


def result_matches_keywords(result: dict, keywords: list) -> bool:
    """Return True if result text includes at least one keyword."""
    if not keywords:
        return True
    combined = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
    return any(kw.lower() in combined for kw in keywords)


def filter_results_by_intent_and_keywords(results: list, keywords: list, intent_phrases: list) -> list:
    """Keep results that match either template keywords or intent phrases."""
    filtered = []
    for result in results:
        combined_text = f"{result.get('title', '')} {result.get('snippet', '')}"
        keyword_match = result_matches_keywords(result, keywords)
        intent_match = detect_intent_match(combined_text, intent_phrases)
        if not (keyword_match or intent_match):
            continue
        filtered.append(result)
    return filtered


def render_search_page():
    """Render the search interface."""
    st.markdown('<h1 class="main-header">🔍 Search for New Leads</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar - Search Configuration
    st.sidebar.title("🔍 Search Configuration")

    # Template selection
    categories = SearchTemplates.list_by_category()
    template_options = []
    for category, templates in categories.items():
        for template_name in templates:
            template = SearchTemplates.get_template(template_name)
            template_options.append(f"{template_name} - {template['description']}")

    selected_option = st.sidebar.selectbox(
        "Search Template",
        template_options,
        help="Choose what type of leads you want to find"
    )

    template_name = selected_option.split(" - ")[0]
    template = SearchTemplates.get_template(template_name)

    with st.sidebar.expander("ℹ️ Template Info", expanded=False):
        st.write(f"**Description:** {template['description']}")
        st.write(f"**Keywords:** {', '.join(template['keywords'][:3])}...")
        st.write(f"**Default Sites:** {', '.join(template['sites'])}")

    st.sidebar.markdown("---")

    # Location input
    st.sidebar.subheader("📍 Locations")

    # Location presets
    location_preset = st.sidebar.selectbox(
        "Quick Presets",
        ["Custom", "Bloomingdale IL Area", "Boston/NH Area", "Both Areas"]
    )

    # Set default based on preset
    if location_preset == "Bloomingdale IL Area":
        default_locations = "Bloomingdale IL\nAddison IL\nGlendale Heights IL\nCarol Stream IL\nRoselle IL\nItasca IL\nMedinah IL\nWheaton IL\nElmhurst IL\nLombard IL"
    elif location_preset == "Boston/NH Area":
        default_locations = "Boston MA\nCambridge MA\nSomerville MA\nBrookline MA\nNewton MA\nQuincy MA\nMalden MA\nMedford MA\nNashua NH\nManchester NH\nSalem NH\nDerry NH"
    elif location_preset == "Both Areas":
        default_locations = "Bloomingdale IL\nAddison IL\nGlendale Heights IL\nBoston MA\nCambridge MA\nSomerville MA\nNashua NH\nManchester NH"
    else:
        default_locations = "Boston MA\nCambridge MA\nSomerville MA"

    location_input = st.sidebar.text_area(
        "Locations (one per line)",
        value=default_locations,
        height=150
    )
    locations = [loc.strip() for loc in location_input.split("\n") if loc.strip()]

    st.sidebar.markdown("---")

    # Sites configuration
    st.sidebar.subheader("🌐 Social Media Sites")
    available_sites = [
        "instagram.com", "facebook.com", "twitter.com", "linkedin.com",
        "reddit.com", "tiktok.com", "nextdoor.com", "youtube.com",
        "pinterest.com", "craigslist.org"
    ]

    # Initialize site selection state
    if 'site_selection' not in st.session_state:
        st.session_state.site_selection = {
            "instagram.com": True,
            "facebook.com": True,
            "twitter.com": True,
            "linkedin.com": True,
            "reddit.com": True,
            "tiktok.com": False,
            "nextdoor.com": False,
            "youtube.com": False,
            "pinterest.com": False,
            "craigslist.org": False
        }

    # Select all / deselect all buttons
    col1, col2 = st.sidebar.columns(2)
    if col1.button("✓ All", key="select_all", use_container_width=True):
        for site in available_sites:
            st.session_state.site_selection[site] = True
        st.rerun()

    if col2.button("✗ None", key="deselect_all", use_container_width=True):
        for site in available_sites:
            st.session_state.site_selection[site] = False
        st.rerun()

    # Site checkboxes
    selected_sites = []
    cols = st.sidebar.columns(2)
    for idx, site in enumerate(available_sites):
        col = cols[idx % 2]
        site_name = site.replace(".com", "").replace(".org", "").title()

        is_checked = col.checkbox(
            site_name,
            value=st.session_state.site_selection.get(site, False),
            key=f"site_{site}_{location_preset}"
        )

        # Update state
        st.session_state.site_selection[site] = is_checked

        if is_checked:
            selected_sites.append(site)

    st.sidebar.markdown("---")

    # Advanced options
    with st.sidebar.expander("⚙️ Advanced Options", expanded=True):
        max_results = st.slider(
            "Max Results",
            min_value=10,
            max_value=100,
            value=30,
            step=10
        )

        include_emails = st.checkbox("Include email domains in search", value=True)
        strict_filter = st.checkbox(
            "Strict intent/keyword filter (fewer, higher-quality)",
            value=False,
            help="When on, results must match intent or template keywords."
        )
        preview_only = st.checkbox(
            "Preview only (do not save to DB)",
            value=False,
            help="Shows results without running duplicate checks or saving."
        )
        show_debug = st.checkbox(
            "Show debug counts",
            value=False,
            help="Displays counts at each filtering step."
        )

        show_new_only = st.checkbox(
            "Show only NEW leads (hide duplicates)",
            value=True,
            help="Only show leads not already in your database"
        )

        api_queries_used = max_results // 10
        st.info(f"📊 ~{api_queries_used} API queries")

    st.sidebar.markdown("---")
    search_button = st.sidebar.button("🚀 Run Search", type="primary", use_container_width=True)

    # Main content - Database stats
    stats = db.get_stats()

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Total Leads in DB", stats['total_leads'])
    with col2:
        st.metric("With Email", stats['leads_with_email'])
    with col3:
        st.metric("With Phone", stats['leads_with_phone'])
    with col4:
        st.metric("New Today", stats['new_today'])
    with col5:
        st.metric("API Queries Today", stats.get('api_queries_today', 0))
    with col6:
        st.metric("Total API Queries", stats.get('total_api_queries', 0))

    st.markdown("---")

    # Search execution
    if search_button:
        if not locations or not selected_sites:
            st.error("Please enter at least one location and select at least one site!")
            st.stop()

        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Initialize client(s)
            status_text.text("🔧 Initializing...")
            progress_bar.progress(10)

            use_places = template_name in {"realtors", "contractors", "investors"}
            places_client = None
            if use_places:
                try:
                    places_client = GooglePlacesClient()
                except Exception:
                    use_places = False

            search_client = GoogleSearchClient()

            # Build query
            status_text.text("🔍 Building query...")
            progress_bar.progress(20)

            intent_phrases = template.get("intent_phrases", [])
            exclude_terms = list(template["exclude_terms"])
            reddit_subs = None
            if "reddit.com" in selected_sites:
                exclude_terms.extend(reddit_exclude_terms())
                reddit_subs = build_reddit_subreddits(locations)

            if set(selected_sites) != set(template['sites']):
                query = search_client.build_query(
                    keywords=template["keywords"],
                    locations=locations,
                    sites=selected_sites,
                    email_domains=SearchTemplates.EMAIL_DOMAINS if include_emails else None,
                    exclude_terms=exclude_terms,
                    intent_phrases=intent_phrases,
                    reddit_subreddits=reddit_subs
                )
            else:
                query = search_client.build_query(
                    keywords=template["keywords"],
                    locations=locations,
                    sites=template["sites"],
                    email_domains=SearchTemplates.EMAIL_DOMAINS if include_emails else None,
                    exclude_terms=exclude_terms,
                    intent_phrases=intent_phrases,
                    reddit_subreddits=reddit_subs
                )

            service_templates = {"realtors", "contractors", "investors"}

            # Perform search
            status_text.text(f"🌐 Searching Google...")
            progress_bar.progress(30)

            results = []
            reddit_meta = {}
            results_source = "cse"
            if use_places and places_client:
                status_text.text("📍 Searching Places (geo)...")
                progress_bar.progress(30)
                places_query = places_query_for_template(template_name)
                places_raw, places_stats = places_client.search_locations(
                    base_query=places_query,
                    locations=locations,
                    max_results=max_results
                )
                results = [normalize_places_result(p) for p in places_raw]
                results_source = "places"

                if not results:
                    geo_note = ""
                    if places_stats:
                        geo_note = (
                            f"Geocoded {places_stats.get('locations_geocoded', 0)}/"
                            f"{places_stats.get('locations_total', 0)} locations"
                        )
                        status_detail = places_stats.get("last_status")
                        if status_detail:
                            geo_note = f"{geo_note}. Places status: {status_detail}"
                    status_text.text("🌐 Places returned 0, falling back to Google CSE...")
                    st.warning(
                        "Places returned 0 results. Check that Places API and Geocoding API "
                        "are enabled and your key allows server-side use. "
                        f"{geo_note}".strip()
                    )
                    date_restrict = "d60"
                    results = run_cse_search(
                        search_client,
                        query,
                        total_results=max_results,
                        delay=0.5,
                        date_restrict=date_restrict
                    )
                    if "reddit.com" in selected_sites:
                        status_text.text("🧹 Filtering Reddit posts by recency (60 days)...")
                        results, reddit_meta = filter_recent_reddit_results(results, max_age_days=60)
                    results_source = "cse"
            else:
                date_restrict = "d60"
                results = run_cse_search(
                    search_client,
                    query,
                    total_results=max_results,
                    delay=0.5,
                    date_restrict=date_restrict
                )
                if "reddit.com" in selected_sites:
                    status_text.text("🧹 Filtering Reddit posts by recency (60 days)...")
                    results, reddit_meta = filter_recent_reddit_results(results, max_age_days=60)
                results_source = "cse"

            # Strict relevance filter for all non-Places results (optional).
            raw_results_count = len(results)
            if strict_filter and results_source != "places":
                pre_filter_count = len(results)
                results = filter_results_by_intent_and_keywords(
                    results,
                    template["keywords"],
                    intent_phrases
                )
                removed = pre_filter_count - len(results)
                if removed > 0:
                    st.info(f"Filtered out {removed} results by intent/keyword rules.")
            ranked_results = rank_results_by_locations(results, locations)
            progress_bar.progress(60)

            if not results:
                st.error("❌ No results found. Try different parameters.")
                progress_bar.empty()
                status_text.empty()
                st.stop()

            # Calculate actual API queries used (each query returns 10 results)
            api_queries_used = (len(results) + 9) // 10  # Round up

            # Extract contact information
            status_text.text(f"📊 Extracting contacts...")
            progress_bar.progress(70)

            contacts = []
            extractor = ContactExtractor()

            if results_source == "places" and places_client:
                for place in places_raw:
                    place_id = place.get("id", "")
                    details = {}
                    if place_id:
                        try:
                            details = places_client.place_details(place_id)
                        except Exception:
                            details = {}
                    display_name = place.get("displayName", {}).get("text", "")
                    contact_info = {
                        "first_name": None,
                        "last_name": None,
                        "company_name": display_name,
                        "website_url": details.get("websiteUri") or normalize_places_result(place).get("link", ""),
                        "email": None,
                        "phone": details.get("internationalPhoneNumber", "")
                    }
                    contact_info["location_match"] = result_matches_locations(
                        {
                            "title": display_name,
                            "snippet": place.get("formattedAddress", ""),
                            "link": contact_info["website_url"]
                        },
                        locations
                    )
                    contact_info["intent_match"] = False
                    contact_info["lead_source"] = "places"
                    contact_info["keyword_match"] = result_matches_keywords(
                        {
                            "title": display_name,
                            "snippet": place.get("formattedAddress", "")
                        },
                        template["keywords"]
                    )
                    contact_info["post_created_at"] = None
                    contacts.append(contact_info)
            else:
                for result in ranked_results:
                    contact_info = extractor.extract_contact_info(
                        title=result.get("title", ""),
                        snippet=result.get("snippet", ""),
                        link=result.get("link", "")
                    )
                    combined_text = f"{result.get('title', '')} {result.get('snippet', '')}"
                    contact_info["location_match"] = result_matches_locations(result, locations)
                    contact_info["intent_match"] = detect_intent_match(combined_text, intent_phrases)
                    contact_info["lead_source"] = lead_source_from_link(result.get("link", ""))
                    contact_info["keyword_match"] = result_matches_keywords(result, template["keywords"])
                    created_utc = reddit_meta.get(result.get("link", ""))
                    if created_utc:
                        contact_info["post_created_at"] = datetime.fromtimestamp(
                            created_utc, tz=timezone.utc
                        ).isoformat()
                    else:
                        contact_info["post_created_at"] = None
                    contacts.append(contact_info)

            progress_bar.progress(80)

            # Filter useful contacts
            service_templates = {"realtors", "contractors", "investors"}
            people_templates = {
                "home_buyers", "first_time_buyers", "home_sellers",
                "downsizing", "renovation_needed", "home_repair",
                "relocating", "urgent_sellers"
            }

            if results_source == "places":
                useful_contacts = [
                    c for c in contacts
                    if c.get('website_url') or c.get('phone')
                ]
            elif template_name in people_templates:
                useful_contacts = [
                    c for c in contacts
                    if c.get('website_url') and (c.get('intent_match') or c.get('keyword_match'))
                ]
            else:
                useful_contacts = [
                    c for c in contacts
                    if c.get('website_url') and (c.get('email') or c.get('phone'))
                ]

            if show_debug:
                st.info(
                    f"Results: raw={raw_results_count} "
                    f"post-filter={len(results)} "
                    f"contacts={len(contacts)} "
                    f"useful={len(useful_contacts)}"
                )

            # Save to database and detect duplicates
            status_text.text("💾 Saving to database...")
            progress_bar.progress(90)

            if preview_only:
                new_leads, duplicate_leads = useful_contacts, []
            else:
                new_leads, duplicate_leads = db.add_leads(
                    useful_contacts,
                    template=template_name,
                    locations=locations,
                    api_queries_used=api_queries_used
                )

            progress_bar.progress(100)
            status_text.empty()
            progress_bar.empty()

            # Display results
            st.markdown("---")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🔍 Total Found", len(useful_contacts))
            with col2:
                st.metric("✨ New Leads", len(new_leads), delta=len(new_leads))
            with col3:
                st.metric("🔄 Duplicates", len(duplicate_leads))
            with col4:
                st.metric("📊 API Queries Used", api_queries_used)

            if len(new_leads) > 0:
                st.success(f"🎉 Found {len(new_leads)} NEW leads!")
            else:
                st.warning("⚠️ No new leads found. All results were duplicates.")

            # Show results based on preference
            if show_new_only:
                if new_leads:
                    st.subheader("✨ New Leads Only")
                    df = pd.DataFrame(new_leads).fillna('')
                    display_df = apply_location_badge(df.copy())
                    display_df = display_df[['first_name', 'last_name', 'company_name', 'website_url', 'email', 'phone']]
                    st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)

                    # Download button for new leads only
                    download_df = df[['first_name', 'last_name', 'company_name', 'website_url', 'email', 'phone']]
                    excel_data = get_download_data(download_df, "excel")
                    st.download_button(
                        "📥 Download New Leads (Excel)",
                        data=excel_data,
                        file_name=f"new_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("No new leads to display. All results were already in your database.")
            else:
                # Show all results with new/duplicate badges
                st.subheader("📊 All Results")

                all_results = []
                for lead in new_leads:
                    lead['status'] = '✨ NEW'
                    all_results.append(lead)
                for lead in duplicate_leads:
                    lead['status'] = '🔄 DUPLICATE'
                    all_results.append(lead)

                df = pd.DataFrame(all_results).fillna('')
                display_df = apply_location_badge(df.copy())
                for col in ['status', 'first_name', 'last_name', 'company_name', 'website_url', 'email', 'phone']:
                    if col not in display_df.columns:
                        display_df[col] = ''
                display_df = display_df[['status', 'first_name', 'last_name', 'company_name', 'website_url', 'email', 'phone']]
                st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)


def render_database_page():
    """Render the database view page."""
    st.markdown('<h1 class="main-header">💾 Lead Database</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar filters
    st.sidebar.title("🔍 Filters")

    # Get unique templates from database
    all_leads = db.get_all_leads()
    unique_templates = sorted(set([lead.get('template', 'Unknown') for lead in all_leads]))

    # Template filter with better names
    template_display_names = {
        'homebuyers_facebook': '🏠 Homebuyers (Facebook)',
        'homebuyers_reddit': '🏠 Homebuyers (Reddit)',
        'homebuyers_instagram': '🏠 Homebuyers (Instagram)',
        'real_estate_agents': '👔 Real Estate Agents',
        'real_estate_investors': '💰 Real Estate Investors',
        'first_time_homebuyers': '🎉 First Time Buyers',
        'downsizing_seniors': '👴 Downsizing Seniors',
        'imported': '📥 Imported'
    }

    # Create filter options
    filter_options = ["All Leads"] + [template_display_names.get(t, t.replace('_', ' ').title()) for t in unique_templates]
    selected_display = st.sidebar.selectbox("Filter by Type", filter_options)

    # Map back to actual template name
    if selected_display == "All Leads":
        selected_template = None
    else:
        # Reverse lookup
        selected_template = next((k for k, v in template_display_names.items() if v == selected_display),
                                 selected_display.replace(' ', '_').lower())

    # Sorting
    sort_by = st.sidebar.selectbox(
        "Sort by",
        ["Newest First", "Oldest First", "Most Seen", "Has Email", "Has Phone", "Location Match", "Lead Score"]
    )

    # Search box
    search_query = st.sidebar.text_input("🔍 Search in database", "")
    min_score = st.sidebar.slider("⭐ Min Lead Score", min_value=0, max_value=100, value=0, step=5)

    st.sidebar.markdown("---")

    # Action buttons
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    export_all = st.sidebar.button("📥 Export All Leads", use_container_width=True)

    if st.sidebar.button("🗑️ Clear Database", type="secondary", use_container_width=True):
        if st.sidebar.checkbox("⚠️ Confirm deletion"):
            db.clear_database()
            st.success("Database cleared!")
            st.rerun()

    st.sidebar.markdown("---")

    # Get database stats
    stats = db.get_stats()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Leads", stats['total_leads'])
    with col2:
        st.metric("With Email", stats['leads_with_email'])
    with col3:
        st.metric("With Phone", stats['leads_with_phone'])
    with col4:
        st.metric("New Today", stats['new_today'])
    with col5:
        st.metric("API Queries Total", stats.get('total_api_queries', 0))

    st.markdown("---")

    # Get leads from database
    leads = db.get_all_leads(template=selected_template)

    if not leads:
        st.info("📭 No leads in database yet. Run a search to get started!")
        return

    # Convert to DataFrame
    df = pd.DataFrame(leads)

    # Apply search filter
    if search_query:
        mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
        df = df[mask]

    if 'location_match' not in df.columns:
        df['location_match'] = df.apply(lead_location_match, axis=1)

    if 'intent_match' not in df.columns:
        df['intent_match'] = False
    else:
        df['intent_match'] = df['intent_match'].fillna(False)
    if 'keyword_match' not in df.columns:
        df['keyword_match'] = df.apply(lead_keyword_match, axis=1)
    else:
        df['keyword_match'] = df['keyword_match'].fillna(False)
    if 'lead_source' not in df.columns:
        df['lead_source'] = ""
    else:
        df['lead_source'] = df['lead_source'].fillna("")

    created_at = pd.to_datetime(df['created_at'], utc=True, errors='coerce')
    post_created_at = pd.to_datetime(df.get('post_created_at'), utc=True, errors='coerce')
    now = pd.Timestamp.utcnow()
    recency_days = (now - created_at).dt.days
    use_post = post_created_at.notna()
    recency_days = recency_days.where(~use_post, (now - post_created_at).dt.days)
    if 'lead_source' in df.columns:
        reddit_missing = (df['lead_source'] == "reddit") & post_created_at.isna()
        recency_days = recency_days.mask(reddit_missing, 9999)
    df['lead_recency_days'] = recency_days.fillna(9999)
    df = df.apply(compute_lead_score, axis=1)

    if min_score > 0:
        df = df[df['lead_score'] >= min_score]

    # Apply sorting
    if sort_by == "Newest First":
        df = df.sort_values('created_at', ascending=False)
    elif sort_by == "Oldest First":
        df = df.sort_values('created_at', ascending=True)
    elif sort_by == "Most Seen":
        df = df.sort_values('times_seen', ascending=False)
    elif sort_by == "Has Email":
        df = df.sort_values('email', ascending=False, na_position='last')
    elif sort_by == "Has Phone":
        df = df.sort_values('phone', ascending=False, na_position='last')
    elif sort_by == "Location Match":
        df = df.sort_values(['location_match', 'created_at'], ascending=[False, False])
    elif sort_by == "Lead Score":
        df = df.sort_values(['lead_score', 'created_at'], ascending=[False, False])

    display_df = apply_quality_badges(df.copy())

    # Display columns
    display_columns = [
        'lead_score',
        'first_name', 'last_name', 'company_name',
        'email', 'phone', 'website_url',
        'template', 'times_seen', 'created_at'
    ]

    # Show results
    st.subheader(f"📊 Showing {len(df)} leads")

    # Column configuration for better display
    column_config = {
        "lead_score": st.column_config.NumberColumn("Score", help="Lead quality score (0-100)"),
        "website_url": st.column_config.LinkColumn("Website"),
        "times_seen": st.column_config.NumberColumn("Seen", help="Times found in searches"),
        "created_at": st.column_config.DatetimeColumn("First Seen", format="MMM DD, YYYY")
    }

    st.dataframe(
        display_df[display_columns],
        use_container_width=True,
        height=500,
        hide_index=True,
        column_config=column_config
    )

    # Export functionality
    if export_all or st.button("📥 Export Current View"):
        export_df = df[['first_name', 'last_name', 'company_name', 'website_url', 'email', 'phone']]
        excel_data = get_download_data(export_df, "excel")

        st.download_button(
            "📥 Download as Excel",
            data=excel_data,
            file_name=f"all_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


def main():
    """Main application."""

    # Check API credentials
    if not check_api_credentials():
        st.error("⚠️ API Credentials Not Found!")
        st.markdown("""
        Please create a `.env` file with:
        ```
        GOOGLE_API_KEY=your_api_key_here
        GOOGLE_CSE_ID=your_cse_id_here
        ```
        """)
        st.stop()

    # Top navigation
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("🔍 Search", use_container_width=True, type="primary" if st.session_state.current_view == 'search' else "secondary"):
            st.session_state.current_view = 'search'
            st.rerun()

    with col2:
        if st.button("💾 Database", use_container_width=True, type="primary" if st.session_state.current_view == 'database' else "secondary"):
            st.session_state.current_view = 'database'
            st.rerun()

    # Render appropriate page
    if st.session_state.current_view == 'search':
        render_search_page()
    else:
        render_database_page()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>Real Estate Lead Finder Pro | Built with Streamlit | Powered by Google Custom Search API</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
