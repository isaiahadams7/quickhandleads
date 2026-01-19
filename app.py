"""
Streamlit Dashboard V2 for Real Estate Lead Finder
Enhanced with database, duplicate detection, and better viewing
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from io import BytesIO

# Import our existing modules
from google_search import GoogleSearchClient, create_search_from_template
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
            # Initialize client
            status_text.text("🔧 Initializing...")
            progress_bar.progress(10)
            client = GoogleSearchClient()

            # Build query
            status_text.text("🔍 Building query...")
            progress_bar.progress(20)

            if set(selected_sites) != set(template['sites']):
                query = client.build_query(
                    keywords=template["keywords"],
                    locations=locations,
                    sites=selected_sites,
                    email_domains=SearchTemplates.EMAIL_DOMAINS if include_emails else None,
                    exclude_terms=template["exclude_terms"]
                )
            else:
                query = create_search_from_template(
                    template_name=template_name,
                    locations=locations,
                    include_emails=include_emails
                )

            # Perform search
            status_text.text(f"🌐 Searching Google...")
            progress_bar.progress(30)

            results = client.search_multiple_pages(query, total_results=max_results, delay=0.5)
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

            for result in results:
                contact_info = extractor.extract_contact_info(
                    title=result.get("title", ""),
                    snippet=result.get("snippet", ""),
                    link=result.get("link", "")
                )
                contacts.append(contact_info)

            progress_bar.progress(80)

            # Filter useful contacts - must have URL AND at least email or phone
            useful_contacts = [
                c for c in contacts
                if c.get('website_url') and (c.get('email') or c.get('phone'))  # Must have contact info
            ]

            # Save to database and detect duplicates
            status_text.text("💾 Saving to database...")
            progress_bar.progress(90)

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
                    df = pd.DataFrame(new_leads)
                    df = df[['first_name', 'last_name', 'company_name', 'website_url', 'email', 'phone']]
                    df = df.fillna('')
                    st.dataframe(df, use_container_width=True, height=400, hide_index=True)

                    # Download button for new leads only
                    excel_data = get_download_data(df, "excel")
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

                df = pd.DataFrame(all_results)
                df = df[['status', 'first_name', 'last_name', 'company_name', 'website_url', 'email', 'phone']]
                df = df.fillna('')
                st.dataframe(df, use_container_width=True, height=400, hide_index=True)

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

    # Template filter
    all_templates = ["All"] + list(set([t for category in SearchTemplates.list_by_category().values() for t in category]))
    selected_template = st.sidebar.selectbox("Filter by Template", all_templates)

    # Sorting
    sort_by = st.sidebar.selectbox(
        "Sort by",
        ["Newest First", "Oldest First", "Most Seen", "Has Email", "Has Phone"]
    )

    # Search box
    search_query = st.sidebar.text_input("🔍 Search in database", "")

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
    template_filter = None if selected_template == "All" else selected_template
    leads = db.get_all_leads(template=template_filter)

    if not leads:
        st.info("📭 No leads in database yet. Run a search to get started!")
        return

    # Convert to DataFrame
    df = pd.DataFrame(leads)

    # Apply search filter
    if search_query:
        mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
        df = df[mask]

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

    # Display columns
    display_columns = [
        'first_name', 'last_name', 'company_name',
        'email', 'phone', 'website_url',
        'template', 'times_seen', 'created_at'
    ]

    # Show results
    st.subheader(f"📊 Showing {len(df)} leads")

    # Column configuration for better display
    column_config = {
        "website_url": st.column_config.LinkColumn("Website"),
        "times_seen": st.column_config.NumberColumn("Seen", help="Times found in searches"),
        "created_at": st.column_config.DatetimeColumn("First Seen", format="MMM DD, YYYY")
    }

    st.dataframe(
        df[display_columns],
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
