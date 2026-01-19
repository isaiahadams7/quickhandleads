#!/usr/bin/env python3
"""
Real Estate Lead Finder
Searches Google for real estate contacts (agents, buyers, sellers, etc.) and exports to Excel.
"""
import sys
import argparse
from typing import List
from google_search import GoogleSearchClient, create_realtor_search_query, create_search_from_template
from contact_extractor import ContactExtractor
from spreadsheet_exporter import SpreadsheetExporter
from search_templates import SearchTemplates


def print_available_templates():
    """Print all available search templates organized by category."""
    categories = SearchTemplates.list_by_category()
    print("\n" + "=" * 60)
    print("AVAILABLE SEARCH TEMPLATES")
    print("=" * 60)
    for category, templates in categories.items():
        print(f"\n📁 {category}:")
        for template_name in templates:
            template = SearchTemplates.get_template(template_name)
            print(f"  • {template_name:20s} - {template['description']}")
    print("\n" + "=" * 60 + "\n")


def main():
    """Main entry point for the lead finder."""
    parser = argparse.ArgumentParser(
        description="Find real estate leads (agents, buyers, sellers, etc.) using Google Custom Search API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find realtors in Boston area (default)
  python main.py

  # Find people who recently bought homes
  python main.py --template home_buyers --locations "Miami FL" "Fort Lauderdale FL"

  # Find people looking to sell their homes
  python main.py --template home_sellers --locations "Austin TX"

  # Find people needing home renovations
  python main.py --template renovation_needed --locations "Denver CO"

  # List all available templates
  python main.py --list-templates
        """
    )
    parser.add_argument(
        "--template",
        type=str,
        default="realtors",
        help="Search template to use (default: realtors). Use --list-templates to see all options."
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List all available search templates and exit"
    )
    parser.add_argument(
        "--locations",
        nargs="+",
        default=["Boston MA", "Cambridge MA", "Somerville MA", "Brookline MA", "Newton MA"],
        help="Locations to search (e.g., 'Boston MA' 'Cambridge MA')"
    )
    parser.add_argument(
        "--sites",
        nargs="+",
        help="Override sites to search (e.g., instagram.com facebook.com)"
    )
    parser.add_argument(
        "--results",
        type=int,
        default=100,
        help="Maximum number of search results to fetch (default: 100)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output filename (default: auto-generated with timestamp)"
    )
    parser.add_argument(
        "--format",
        choices=["excel", "csv", "both"],
        default="excel",
        help="Output format (default: excel)"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Use a custom search query instead of template"
    )
    parser.add_argument(
        "--no-emails",
        action="store_true",
        help="Don't include email domains in search query"
    )

    args = parser.parse_args()

    # Handle --list-templates
    if args.list_templates:
        print_available_templates()
        sys.exit(0)

    print("=" * 60)
    print("REAL ESTATE LEAD FINDER")
    print("=" * 60)

    # Initialize the Google Search client
    try:
        client = GoogleSearchClient()
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease set up your .env file with:")
        print("  GOOGLE_API_KEY=your_api_key")
        print("  GOOGLE_CSE_ID=your_cse_id")
        print("\nSee README.md for setup instructions.")
        sys.exit(1)

    # Build or use custom query
    if args.query:
        query = args.query
        print(f"\n🔍 Using custom query: {query}\n")
    else:
        # Use template-based search
        try:
            template = SearchTemplates.get_template(args.template)
            print(f"\n🎯 Using template: {args.template}")
            print(f"📝 Description: {template['description']}")
            print(f"📍 Locations: {', '.join(args.locations)}")

            # Use custom sites if provided, otherwise use template defaults
            sites = args.sites if args.sites else template["sites"]
            print(f"🌐 Sites: {', '.join(sites)}")

            query = create_search_from_template(
                template_name=args.template,
                locations=args.locations,
                include_emails=not args.no_emails
            )

            # Override sites if specified
            if args.sites:
                query = client.build_query(
                    keywords=template["keywords"],
                    locations=args.locations,
                    sites=args.sites,
                    email_domains=None if args.no_emails else SearchTemplates.EMAIL_DOMAINS,
                    exclude_terms=template["exclude_terms"]
                )

            print(f"\n🔍 Search query:\n{query}\n")
        except ValueError as e:
            print(f"\n❌ Error: {e}")
            print("\nUse --list-templates to see available templates.")
            sys.exit(1)

    # Perform search
    print(f"🔎 Fetching up to {args.results} results...\n")
    results = client.search_multiple_pages(query, total_results=args.results)

    if not results:
        print("\n❌ No results found. Try adjusting your search parameters.")
        sys.exit(1)

    print(f"\n✓ Found {len(results)} search results")

    # Extract contact information
    print("\n📊 Extracting contact information...")
    contacts = []
    extractor = ContactExtractor()

    for result in results:
        contact_info = extractor.extract_contact_info(
            title=result.get("title", ""),
            snippet=result.get("snippet", ""),
            link=result.get("link", "")
        )
        contacts.append(contact_info)

    print(f"✓ Extracted contact data from {len(contacts)} results")

    # Filter out contacts with no useful information
    useful_contacts = [
        c for c in contacts
        if c.get('email') or c.get('phone') or c.get('first_name')
    ]

    if not useful_contacts:
        print("\n⚠️  Warning: No contacts with email, phone, or name information found.")
        print("This might happen if:")
        print("  - The search results don't contain contact info in titles/snippets")
        print("  - You need to adjust the search query")
        print("  - The API returned limited data")
        print("\nExporting all results anyway for manual review...")
        useful_contacts = contacts

    # Print summary
    SpreadsheetExporter.print_summary(useful_contacts)

    # Export to file(s)
    print("💾 Exporting to file...")

    if args.format in ["excel", "both"]:
        SpreadsheetExporter.export_to_excel(
            useful_contacts,
            filename=args.output
        )

    if args.format in ["csv", "both"]:
        csv_filename = args.output.replace('.xlsx', '.csv') if args.output else None
        SpreadsheetExporter.export_to_csv(
            useful_contacts,
            filename=csv_filename
        )

    print("\n✅ Done! Check the 'output' folder for your files.\n")


if __name__ == "__main__":
    main()
