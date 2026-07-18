"""
Thin wrapper around Airtable so the rest of the module doesn't need to know
about the pyairtable API directly. This is the ONLY file you'd need to
change if the team later switches to Google Sheets or another CRM backend -
every other module just calls get_all_leads / upsert_lead.

Setup (see README.md for full Airtable base instructions):
    export AIRTABLE_API_KEY="your_pat_here"
    export AIRTABLE_BASE_ID="appXXXXXXXXXXXXXX"
    export AIRTABLE_TABLE_NAME="Leads"
"""

import os
from datetime import datetime, timezone

try:
    from pyairtable import Table
except ImportError:
    Table = None  # allows offline/demo mode without the package installed


class AirtableClient:
    def __init__(self, api_key: str = None, base_id: str = None, table_name: str = None):
        self.api_key = api_key or os.getenv("AIRTABLE_API_KEY")
        self.base_id = base_id or os.getenv("AIRTABLE_BASE_ID")
        self.table_name = table_name or os.getenv("AIRTABLE_TABLE_NAME", "Leads")
        self._table = None

        if self.api_key and self.base_id and Table is not None:
            self._table = Table(self.api_key, self.base_id, self.table_name)

    @property
    def is_connected(self) -> bool:
        return self._table is not None

    def get_all_leads(self) -> list[dict]:
        """Return all lead records currently in the CRM."""
        if not self.is_connected:
            raise RuntimeError(
                "Airtable not configured. Set AIRTABLE_API_KEY / AIRTABLE_BASE_ID, "
                "or use MockAirtableClient for offline testing."
            )
        return self._table.all()

    def create_lead(self, fields: dict) -> dict:
        if not self.is_connected:
            raise RuntimeError("Airtable not configured.")
        return self._table.create(fields)

    def update_lead(self, record_id: str, fields: dict) -> dict:
        if not self.is_connected:
            raise RuntimeError("Airtable not configured.")
        return self._table.update(record_id, fields)


class MockAirtableClient:
    """
    In-memory stand-in for AirtableClient, used in the demo notebook and for
    local testing without real Airtable credentials. Same method signatures
    as AirtableClient, so process_lead() works unchanged against either.
    """

    def __init__(self):
        self._records = []
        self._next_id = 1

    @property
    def is_connected(self) -> bool:
        return True

    def get_all_leads(self) -> list[dict]:
        return self._records

    def create_lead(self, fields: dict) -> dict:
        record = {
            "id": f"rec_mock_{self._next_id}",
            "createdTime": datetime.now(timezone.utc).isoformat(),
            "fields": fields,
        }
        self._next_id += 1
        self._records.append(record)
        return record

    def update_lead(self, record_id: str, fields: dict) -> dict:
        for record in self._records:
            if record["id"] == record_id:
                record["fields"].update(fields)
                return record
        raise KeyError(f"No mock record with id {record_id}")
