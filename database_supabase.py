"""
Supabase database adapter for storing and managing leads.
Cloud-based, persistent storage that works with Streamlit Cloud.
"""
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import hashlib
from supabase import create_client, Client


class SupabaseLeadDatabase:
    """Manage leads database with Supabase (cloud PostgreSQL)."""

    def __init__(self):
        """Initialize Supabase connection."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError(
                "Supabase credentials not found. "
                "Set SUPABASE_URL and SUPABASE_KEY environment variables."
            )

        self.supabase: Client = create_client(supabase_url, supabase_key)

    @staticmethod
    def _hash_url(url: str) -> str:
        """Create hash of URL for duplicate detection."""
        return hashlib.md5(url.lower().strip().encode()).hexdigest()

    def add_leads(
        self,
        leads: List[Dict],
        template: str,
        locations: List[str]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Add leads to database, detecting duplicates.

        Returns:
            Tuple of (new_leads, duplicate_leads)
        """
        new_leads = []
        duplicate_leads = []
        location_str = ", ".join(locations)

        for lead in leads:
            url = lead.get('website_url', '')
            if not url:
                continue

            url_hash = self._hash_url(url)

            # Check if lead already exists
            existing = self.supabase.table('leads').select('*').eq('url_hash', url_hash).execute()

            if existing.data:
                # Update existing lead
                existing_lead = existing.data[0]
                times_seen = existing_lead.get('times_seen', 1) + 1

                update_data = {
                    'last_seen': datetime.now().isoformat(),
                    'times_seen': times_seen
                }

                # Update fields if new data provided
                if lead.get('email'):
                    update_data['email'] = lead['email']
                if lead.get('phone'):
                    update_data['phone'] = lead['phone']
                if lead.get('first_name'):
                    update_data['first_name'] = lead['first_name']
                if lead.get('last_name'):
                    update_data['last_name'] = lead['last_name']
                if lead.get('company_name'):
                    update_data['company_name'] = lead['company_name']

                self.supabase.table('leads').update(update_data).eq('id', existing_lead['id']).execute()
                duplicate_leads.append(lead)
            else:
                # Insert new lead
                insert_data = {
                    'first_name': lead.get('first_name', ''),
                    'last_name': lead.get('last_name', ''),
                    'company_name': lead.get('company_name', ''),
                    'website_url': url,
                    'email': lead.get('email', ''),
                    'phone': lead.get('phone', ''),
                    'template': template,
                    'locations': location_str,
                    'url_hash': url_hash,
                    'times_seen': 1
                }

                self.supabase.table('leads').insert(insert_data).execute()
                new_leads.append(lead)

        # Add to search history
        history_data = {
            'template': template,
            'locations': location_str,
            'num_results': len(leads),
            'new_leads': len(new_leads),
            'duplicate_leads': len(duplicate_leads)
        }
        self.supabase.table('search_history').insert(history_data).execute()

        return new_leads, duplicate_leads

    def get_all_leads(
        self,
        limit: Optional[int] = None,
        template: Optional[str] = None
    ) -> List[Dict]:
        """Get all leads from database."""
        query = self.supabase.table('leads').select('*').order('created_at', desc=True)

        if template:
            query = query.eq('template', template)

        if limit:
            query = query.limit(limit)

        result = query.execute()
        return result.data if result.data else []

    def get_search_history(self, limit: int = 50) -> List[Dict]:
        """Get recent search history."""
        result = self.supabase.table('search_history').select('*').order('timestamp', desc=True).limit(limit).execute()
        return result.data if result.data else []

    def get_stats(self) -> Dict:
        """Get database statistics."""
        stats = {}

        # Total leads
        total_result = self.supabase.table('leads').select('id', count='exact').execute()
        stats['total_leads'] = total_result.count if hasattr(total_result, 'count') else 0

        # Leads with email
        email_result = self.supabase.table('leads').select('id', count='exact').neq('email', '').execute()
        stats['leads_with_email'] = email_result.count if hasattr(email_result, 'count') else 0

        # Leads with phone
        phone_result = self.supabase.table('leads').select('id', count='exact').neq('phone', '').execute()
        stats['leads_with_phone'] = phone_result.count if hasattr(phone_result, 'count') else 0

        # New leads today
        today = datetime.now().date().isoformat()
        today_result = self.supabase.table('leads').select('id', count='exact').gte('created_at', today).execute()
        stats['new_today'] = today_result.count if hasattr(today_result, 'count') else 0

        # Total searches
        searches_result = self.supabase.table('search_history').select('id', count='exact').execute()
        stats['total_searches'] = searches_result.count if hasattr(searches_result, 'count') else 0

        # Most used template
        template_result = self.supabase.table('search_history').select('template').execute()
        if template_result.data:
            templates = [row['template'] for row in template_result.data]
            most_common = max(set(templates), key=templates.count) if templates else "None"
            stats['most_used_template'] = most_common
        else:
            stats['most_used_template'] = "None"

        return stats

    def delete_lead(self, lead_id: int) -> bool:
        """Delete a lead by ID."""
        result = self.supabase.table('leads').delete().eq('id', lead_id).execute()
        return len(result.data) > 0 if result.data else False

    def export_all_leads(self) -> List[Dict]:
        """Export all leads for backup."""
        return self.get_all_leads()

    def clear_database(self) -> bool:
        """Clear all data (use with caution!)."""
        try:
            self.supabase.table('leads').delete().neq('id', 0).execute()
            self.supabase.table('search_history').delete().neq('id', 0).execute()
            return True
        except Exception:
            return False
