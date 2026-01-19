"""
Module for extracting contact information from text using regex patterns.
"""
import re
from typing import Dict, Optional, List


class ContactExtractor:
    """Extract names, emails, and phone numbers from text."""

    # Email patterns for common providers
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@(?:gmail|outlook|hotmail|live|yahoo|icloud|me|aol|comcast|verizon|att)\.(?:com|net)\b',
        re.IGNORECASE
    )

    # Phone number patterns (US format)
    PHONE_PATTERN = re.compile(
        r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    )

    # Common business/personal name indicators
    NAME_STOPWORDS = {
        'inc', 'llc', 'ltd', 'corp', 'company', 'group', 'team',
        'realty', 'properties', 'homes', 'real estate', 'realtor'
    }

    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """Extract the first valid email address from text."""
        if not text:
            return None
        match = ContactExtractor.EMAIL_PATTERN.search(text)
        return match.group(0) if match else None

    @staticmethod
    def extract_all_emails(text: str) -> List[str]:
        """Extract all valid email addresses from text."""
        if not text:
            return []
        return ContactExtractor.EMAIL_PATTERN.findall(text)

    @staticmethod
    def extract_phone(text: str) -> Optional[str]:
        """Extract the first valid phone number from text."""
        if not text:
            return None
        match = ContactExtractor.PHONE_PATTERN.search(text)
        if match:
            # Normalize phone format
            phone = re.sub(r'[^\d]', '', match.group(0))
            if len(phone) == 10:
                return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
            elif len(phone) == 11 and phone[0] == '1':
                return f"+1 ({phone[1:4]}) {phone[4:7]}-{phone[7:]}"
        return None

    @staticmethod
    def extract_all_phones(text: str) -> List[str]:
        """Extract all valid phone numbers from text."""
        if not text:
            return []
        phones = []
        matches = ContactExtractor.PHONE_PATTERN.findall(text)
        for match in matches:
            phone = re.sub(r'[^\d]', '', match)
            if len(phone) == 10:
                phones.append(f"({phone[:3]}) {phone[3:6]}-{phone[6:]}")
            elif len(phone) == 11 and phone[0] == '1':
                phones.append(f"+1 ({phone[1:4]}) {phone[4:7]}-{phone[7:]}")
        return phones

    @staticmethod
    def extract_name_from_title(title: str) -> Dict[str, Optional[str]]:
        """
        Attempt to extract first and last name from a title or snippet.
        This is a best-effort approach and may not always be accurate.
        """
        if not title:
            return {"first_name": None, "last_name": None}

        # Remove common separators and extra info
        title = re.sub(r'[|—\-]+.*$', '', title)
        title = re.sub(r'\s*[@()]\s*.*$', '', title)

        # Extract potential names (capitalized words)
        words = re.findall(r'\b[A-Z][a-z]+\b', title)

        # Filter out common business words
        names = [w for w in words if w.lower() not in ContactExtractor.NAME_STOPWORDS]

        if len(names) >= 2:
            return {"first_name": names[0], "last_name": names[1]}
        elif len(names) == 1:
            return {"first_name": names[0], "last_name": None}

        return {"first_name": None, "last_name": None}

    @staticmethod
    def extract_company_name(text: str) -> Optional[str]:
        """
        Extract company name from text.
        Looks for patterns like "at CompanyName" or "CompanyName Realty"
        """
        if not text:
            return None

        # Look for "at [Company]" or "with [Company]" patterns
        patterns = [
            r'(?:at|with|@)\s+([A-Z][A-Za-z\s&]+(?:Realty|Properties|Homes|Group|Team|Real Estate))',
            r'([A-Z][A-Za-z\s&]+(?:Realty|Properties|Homes|Group|Team|Real Estate))',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                company = match.group(1).strip()
                # Clean up the company name
                company = re.sub(r'\s+', ' ', company)
                if len(company) > 3:  # Minimum length check
                    return company

        return None

    @staticmethod
    def extract_contact_info(title: str, snippet: str, link: str) -> Dict[str, Optional[str]]:
        """
        Extract all contact information from search result data.

        Args:
            title: The search result title
            snippet: The search result snippet/description
            link: The URL of the result

        Returns:
            Dictionary with extracted contact information
        """
        combined_text = f"{title} {snippet}"

        # Extract names
        names = ContactExtractor.extract_name_from_title(title)

        # Extract contact details
        email = ContactExtractor.extract_email(combined_text)
        phone = ContactExtractor.extract_phone(combined_text)
        company = ContactExtractor.extract_company_name(combined_text)

        return {
            "first_name": names["first_name"],
            "last_name": names["last_name"],
            "company_name": company,
            "website_url": link,
            "email": email,
            "phone": phone
        }
