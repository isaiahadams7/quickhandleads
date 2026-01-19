"""
Module for exporting contact data to Excel spreadsheets.
"""
import os
from typing import List, Dict
from datetime import datetime
import pandas as pd


class SpreadsheetExporter:
    """Export contact information to Excel files."""

    COLUMNS = [
        "first_name",
        "last_name",
        "company_name",
        "website_url",
        "email",
        "phone"
    ]

    @staticmethod
    def export_to_excel(
        contacts: List[Dict],
        filename: str = None,
        output_dir: str = "output"
    ) -> str:
        """
        Export contacts to an Excel file.

        Args:
            contacts: List of contact dictionaries
            filename: Output filename (auto-generated if not provided)
            output_dir: Directory to save the file

        Returns:
            Path to the created Excel file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"realtor_contacts_{timestamp}.xlsx"

        # Ensure .xlsx extension
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'

        filepath = os.path.join(output_dir, filename)

        # Create DataFrame with specified column order
        df = pd.DataFrame(contacts, columns=SpreadsheetExporter.COLUMNS)

        # Fill NaN values with empty strings for better Excel display
        df = df.fillna('')

        # Export to Excel with formatting
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Contacts')

            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Contacts']

            # Auto-adjust column widths
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                # Set a reasonable max width
                max_length = min(max_length, 50)
                worksheet.column_dimensions[chr(64 + idx)].width = max_length

        print(f"✓ Exported {len(contacts)} contacts to: {filepath}")
        return filepath

    @staticmethod
    def export_to_csv(
        contacts: List[Dict],
        filename: str = None,
        output_dir: str = "output"
    ) -> str:
        """
        Export contacts to a CSV file.

        Args:
            contacts: List of contact dictionaries
            filename: Output filename (auto-generated if not provided)
            output_dir: Directory to save the file

        Returns:
            Path to the created CSV file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"realtor_contacts_{timestamp}.csv"

        # Ensure .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'

        filepath = os.path.join(output_dir, filename)

        # Create DataFrame with specified column order
        df = pd.DataFrame(contacts, columns=SpreadsheetExporter.COLUMNS)

        # Fill NaN values with empty strings
        df = df.fillna('')

        # Export to CSV
        df.to_csv(filepath, index=False, encoding='utf-8')

        print(f"✓ Exported {len(contacts)} contacts to: {filepath}")
        return filepath

    @staticmethod
    def print_summary(contacts: List[Dict]) -> None:
        """
        Print a summary of the extracted contacts.

        Args:
            contacts: List of contact dictionaries
        """
        total = len(contacts)
        with_email = sum(1 for c in contacts if c.get('email'))
        with_phone = sum(1 for c in contacts if c.get('phone'))
        with_name = sum(1 for c in contacts if c.get('first_name') or c.get('last_name'))
        with_company = sum(1 for c in contacts if c.get('company_name'))

        print("\n" + "=" * 50)
        print("CONTACT EXTRACTION SUMMARY")
        print("=" * 50)
        print(f"Total contacts found:     {total}")
        print(f"Contacts with email:      {with_email} ({with_email/total*100:.1f}%)")
        print(f"Contacts with phone:      {with_phone} ({with_phone/total*100:.1f}%)")
        print(f"Contacts with name:       {with_name} ({with_name/total*100:.1f}%)")
        print(f"Contacts with company:    {with_company} ({with_company/total*100:.1f}%)")
        print("=" * 50 + "\n")
