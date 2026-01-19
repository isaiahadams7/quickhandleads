"""
Simple database for storing and managing leads to prevent duplicates.
Auto-detects and uses Supabase (cloud) or SQLite (local).
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import hashlib


def get_database():
    """
    Factory function to get the appropriate database instance.
    Uses Supabase if credentials available, otherwise SQLite.
    """
    # Check if Supabase credentials exist
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if supabase_url and supabase_key:
        try:
            from database_supabase import SupabaseLeadDatabase
            print("✅ Using Supabase (cloud database)")
            return SupabaseLeadDatabase()
        except Exception as e:
            print(f"⚠️ Supabase connection failed: {e}")
            print("📁 Falling back to local SQLite database")
            return LeadDatabase()
    else:
        print("📁 Using local SQLite database (data/leads.db)")
        return LeadDatabase()


class LeadDatabase:
    """Manage leads database with duplicate detection (SQLite backend)."""

    def __init__(self, db_path: str = "data/leads.db"):
        """Initialize database connection."""
        self.db_path = db_path

        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Leads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                company_name TEXT,
                website_url TEXT UNIQUE,
                email TEXT,
                phone TEXT,
                template TEXT,
                locations TEXT,
                url_hash TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                times_seen INTEGER DEFAULT 1
            )
        """)

        # Search history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template TEXT,
                locations TEXT,
                num_results INTEGER,
                new_leads INTEGER,
                duplicate_leads INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_url_hash ON leads(url_hash)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email ON leads(email)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_website_url ON leads(website_url)
        """)

        conn.commit()
        conn.close()

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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        new_leads = []
        duplicate_leads = []
        location_str = ", ".join(locations)

        for lead in leads:
            url = lead.get('website_url', '')
            if not url:
                continue  # Skip if no URL

            url_hash = self._hash_url(url)

            # Check if lead already exists
            cursor.execute(
                "SELECT id, times_seen FROM leads WHERE url_hash = ?",
                (url_hash,)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing lead
                lead_id, times_seen = existing
                cursor.execute("""
                    UPDATE leads
                    SET last_seen = CURRENT_TIMESTAMP,
                        times_seen = ?,
                        email = COALESCE(NULLIF(?, ''), email),
                        phone = COALESCE(NULLIF(?, ''), phone),
                        first_name = COALESCE(NULLIF(?, ''), first_name),
                        last_name = COALESCE(NULLIF(?, ''), last_name),
                        company_name = COALESCE(NULLIF(?, ''), company_name)
                    WHERE id = ?
                """, (
                    times_seen + 1,
                    lead.get('email', ''),
                    lead.get('phone', ''),
                    lead.get('first_name', ''),
                    lead.get('last_name', ''),
                    lead.get('company_name', ''),
                    lead_id
                ))
                duplicate_leads.append(lead)
            else:
                # Insert new lead
                cursor.execute("""
                    INSERT INTO leads (
                        first_name, last_name, company_name,
                        website_url, email, phone,
                        template, locations, url_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lead.get('first_name', ''),
                    lead.get('last_name', ''),
                    lead.get('company_name', ''),
                    url,
                    lead.get('email', ''),
                    lead.get('phone', ''),
                    template,
                    location_str,
                    url_hash
                ))
                new_leads.append(lead)

        # Add to search history
        cursor.execute("""
            INSERT INTO search_history (
                template, locations, num_results, new_leads, duplicate_leads
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            template,
            location_str,
            len(leads),
            len(new_leads),
            len(duplicate_leads)
        ))

        conn.commit()
        conn.close()

        return new_leads, duplicate_leads

    def get_all_leads(
        self,
        limit: Optional[int] = None,
        template: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all leads from database.

        Args:
            limit: Maximum number of leads to return
            template: Filter by template name

        Returns:
            List of lead dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM leads"
        params = []

        if template:
            query += " WHERE template = ?"
            params.append(template)

        query += " ORDER BY created_at DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        leads = []
        for row in rows:
            leads.append({
                'id': row['id'],
                'first_name': row['first_name'],
                'last_name': row['last_name'],
                'company_name': row['company_name'],
                'website_url': row['website_url'],
                'email': row['email'],
                'phone': row['phone'],
                'template': row['template'],
                'locations': row['locations'],
                'created_at': row['created_at'],
                'last_seen': row['last_seen'],
                'times_seen': row['times_seen']
            })

        conn.close()
        return leads

    def get_search_history(self, limit: int = 50) -> List[Dict]:
        """Get recent search history."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM search_history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        history = [dict(row) for row in rows]

        conn.close()
        return history

    def get_stats(self) -> Dict:
        """Get database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total leads
        cursor.execute("SELECT COUNT(*) FROM leads")
        stats['total_leads'] = cursor.fetchone()[0]

        # Leads with email
        cursor.execute("SELECT COUNT(*) FROM leads WHERE email != ''")
        stats['leads_with_email'] = cursor.fetchone()[0]

        # Leads with phone
        cursor.execute("SELECT COUNT(*) FROM leads WHERE phone != ''")
        stats['leads_with_phone'] = cursor.fetchone()[0]

        # New leads today
        cursor.execute("""
            SELECT COUNT(*) FROM leads
            WHERE DATE(created_at) = DATE('now')
        """)
        stats['new_today'] = cursor.fetchone()[0]

        # Total searches
        cursor.execute("SELECT COUNT(*) FROM search_history")
        stats['total_searches'] = cursor.fetchone()[0]

        # Most used template
        cursor.execute("""
            SELECT template, COUNT(*) as count
            FROM search_history
            GROUP BY template
            ORDER BY count DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        stats['most_used_template'] = result[0] if result else "None"

        conn.close()
        return stats

    def delete_lead(self, lead_id: int) -> bool:
        """Delete a lead by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    def export_all_leads(self) -> List[Dict]:
        """Export all leads for backup."""
        return self.get_all_leads()

    def clear_database(self) -> bool:
        """Clear all data (use with caution!)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM leads")
        cursor.execute("DELETE FROM search_history")

        conn.commit()
        conn.close()

        return True
