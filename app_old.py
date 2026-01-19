"""
Streamlit Dashboard for Real Estate Lead Finder
A beautiful web interface for finding real estate leads using Google Custom Search API
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from io import BytesIO

# Import our existing modules
from google_search import GoogleSearchClient, create_search_from_template
from contact_extractor import ContactExtractor
from spreadsheet_exporter import SpreadsheetExporter
from search_templates import SearchTemplates

# Page configuration
st.set_page_config(
    page_title="Real Estate Lead Finder",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #0066cc;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'contacts' not in st.session_state:
    st.session_state.contacts = None
if 'search_history' not in st.session_state:
    st.session_state.search_history = []


def check_api_credentials():
    """Check if API credentials are configured."""
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    return api_key and cse_id


def get_download_link(df, filename, file_format="excel"):
    """Generate download link for dataframe."""
    if file_format == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Contacts')
        output.seek(0)
        return output.getvalue()
    else:  # CSV
        return df.to_csv(index=False).encode('utf-8')


def main():
    """Main dashboard application."""

    # Header
    st.markdown('<h1 class="main-header">🏠 Real Estate Lead Finder</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Check API credentials
    if not check_api_credentials():
        st.error("⚠️ API Credentials Not Found!")
        st.markdown("""
        <div class="info-box">
        <strong>Setup Required:</strong><br>
        Please create a <code>.env</code> file in the project root with:<br><br>
        <code>GOOGLE_API_KEY=your_api_key_here</code><br>
        <code>GOOGLE_CSE_ID=your_cse_id_here</code><br><br>
        See README.md for detailed setup instructions.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Sidebar - Search Configuration
    st.sidebar.title("🔍 Search Configuration")

    # Template selection
    categories = SearchTemplates.list_by_category()

    # Create template options organized by category
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

    # Extract template name from selection
    template_name = selected_option.split(" - ")[0]
    template = SearchTemplates.get_template(template_name)

    # Show template info
    with st.sidebar.expander("ℹ️ Template Info", expanded=False):
        st.write(f"**Description:** {template['description']}")
        st.write(f"**Keywords:** {', '.join(template['keywords'][:3])}...")
        st.write(f"**Default Sites:** {', '.join(template['sites'])}")

    st.sidebar.markdown("---")

    # Location input
    st.sidebar.subheader("📍 Locations")
    location_input = st.sidebar.text_area(
        "Enter locations (one per line)",
        value="Boston MA\nCambridge MA\nSomerville MA",
        height=100,
        help="Enter each location on a new line"
    )
    locations = [loc.strip() for loc in location_input.split("\n") if loc.strip()]

    st.sidebar.markdown("---")

    # Sites configuration
    st.sidebar.subheader("🌐 Social Media Sites")
    available_sites = ["instagram.com", "facebook.com", "twitter.com", "linkedin.com", "reddit.com"]
    selected_sites = []

    cols = st.sidebar.columns(2)
    for idx, site in enumerate(available_sites):
        col = cols[idx % 2]
        if col.checkbox(site.replace(".com", "").title(), value=True, key=f"site_{site}"):
            selected_sites.append(site)

    st.sidebar.markdown("---")

    # Advanced options
    with st.sidebar.expander("⚙️ Advanced Options", expanded=False):
        max_results = st.slider(
            "Max Results",
            min_value=10,
            max_value=100,
            value=50,
            step=10,
            help="More results = more API queries used"
        )

        include_emails = st.checkbox(
            "Include email domains in search",
            value=True,
            help="Search for common email providers"
        )

        api_queries_used = max_results // 10
        st.info(f"📊 This search will use ~{api_queries_used} API queries")

    st.sidebar.markdown("---")

    # Search button
    search_button = st.sidebar.button("🚀 Run Search", type="primary", use_container_width=True)

    # Main content area
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Template", template_name)
    with col2:
        st.metric("Locations", len(locations))
    with col3:
        st.metric("Max Results", max_results)
    with col4:
        api_quota = 100  # You could track this with a database
        st.metric("API Quota Today", f"{api_quota}/100")

    st.markdown("---")

    # Search execution
    if search_button:
        if not locations:
            st.error("Please enter at least one location!")
            st.stop()

        if not selected_sites:
            st.error("Please select at least one social media site!")
            st.stop()

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Initialize client
            status_text.text("🔧 Initializing Google Search client...")
            progress_bar.progress(10)
            client = GoogleSearchClient()

            # Build query
            status_text.text("🔍 Building search query...")
            progress_bar.progress(20)

            # Override sites if custom selection
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

            # Show query in expander
            with st.expander("🔎 View Search Query", expanded=False):
                st.code(query, language="text")

            # Perform search
            status_text.text(f"🌐 Searching Google (fetching up to {max_results} results)...")
            progress_bar.progress(30)

            results = client.search_multiple_pages(query, total_results=max_results, delay=0.5)
            progress_bar.progress(60)

            if not results:
                st.error("❌ No results found. Try adjusting your search parameters.")
                progress_bar.empty()
                status_text.empty()
                st.stop()

            # Extract contact information
            status_text.text(f"📊 Extracting contact information from {len(results)} results...")
            progress_bar.progress(70)

            contacts = []
            extractor = ContactExtractor()

            for idx, result in enumerate(results):
                contact_info = extractor.extract_contact_info(
                    title=result.get("title", ""),
                    snippet=result.get("snippet", ""),
                    link=result.get("link", "")
                )
                contacts.append(contact_info)

                # Update progress
                progress = 70 + int((idx / len(results)) * 20)
                progress_bar.progress(progress)

            progress_bar.progress(90)

            # Filter useful contacts
            useful_contacts = [
                c for c in contacts
                if c.get('email') or c.get('phone') or c.get('first_name')
            ]

            if not useful_contacts:
                useful_contacts = contacts  # Keep all if no useful info found

            # Save to session state
            st.session_state.search_results = results
            st.session_state.contacts = useful_contacts

            # Add to search history
            st.session_state.search_history.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'template': template_name,
                'locations': ', '.join(locations),
                'results': len(useful_contacts)
            })

            progress_bar.progress(100)
            status_text.text("✅ Search complete!")

            # Clear progress indicators after a moment
            import time
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()

            st.success(f"🎉 Successfully found {len(useful_contacts)} leads!")

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Error occurred: {str(e)}")
            st.exception(e)

    # Display results
    if st.session_state.contacts:
        st.markdown("---")
        st.subheader("📊 Search Results")

        contacts = st.session_state.contacts

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Leads", len(contacts))
        with col2:
            with_email = sum(1 for c in contacts if c.get('email'))
            st.metric("With Email", with_email)
        with col3:
            with_phone = sum(1 for c in contacts if c.get('phone'))
            st.metric("With Phone", with_phone)
        with col4:
            with_name = sum(1 for c in contacts if c.get('first_name'))
            st.metric("With Name", with_name)

        st.markdown("---")

        # Convert to DataFrame
        df = pd.DataFrame(contacts)

        # Reorder columns
        column_order = ['first_name', 'last_name', 'company_name', 'website_url', 'email', 'phone']
        df = df[column_order]

        # Fill NaN with empty strings
        df = df.fillna('')

        # Display dataframe with filters
        st.dataframe(
            df,
            use_container_width=True,
            height=400,
            hide_index=True
        )

        # Download buttons
        st.subheader("💾 Export Results")

        col1, col2 = st.columns(2)

        with col1:
            excel_data = get_download_link(df, "leads.xlsx", "excel")
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col2:
            csv_data = get_download_link(df, "leads.csv", "csv")
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # Search history
    if st.session_state.search_history:
        st.markdown("---")
        st.subheader("📜 Search History")

        history_df = pd.DataFrame(st.session_state.search_history)
        st.dataframe(history_df, use_container_width=True, hide_index=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>Built with ❤️ using Streamlit | Powered by Google Custom Search API</p>
        <p>Need help? Check the <a href="https://github.com/yourusername/quickhandleads">documentation</a></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
