"""
Core CRM integration pipeline.

process_lead() is the single function the rest of the team's bot should
call. It handles:
    1. Normalizing the phone number
    2. Checking for an existing lead (de-duplication)
    3. Tagging the message with an intent
    4. Creating a new CRM record OR updating the existing one, bumping the
       lead's status and message count.
"""

from datetime import datetime, timezone

from app.dedup import normalize_phone, find_existing_lead
from app.tagging import tag_intent
from app.schema import IncomingLead


def process_lead(lead: IncomingLead, client) -> dict:
    """
    client: an AirtableClient or MockAirtableClient instance (see
    airtable_client.py). Returns a dict describing what happened, e.g.:
        {"action": "created", "record": {...}}
        {"action": "updated_duplicate", "record": {...}}
    """
    phone = normalize_phone(lead.phone)
    intent = tag_intent(lead.message)
    now = datetime.now(timezone.utc).isoformat()

    existing_records = client.get_all_leads()
    existing = find_existing_lead(phone, existing_records)

    if existing is None:
        fields = {
            "Name": lead.name or "Unknown",
            "Phone": phone,
            "Last Message": lead.message,
            "Intent Tag": intent,
            "Status": "New",
            "Source": lead.source,
            "First Contact": now,
            "Last Contact": now,
            "Message Count": 1,
        }
        record = client.create_lead(fields)
        return {"action": "created", "record": record}

    # Duplicate: merge into existing record instead of creating a new one
    new_count = existing["fields"].get("Message Count", 1) + 1
    prev_status = existing["fields"].get("Status", "New")
    updated_status = "Contacted" if prev_status == "New" else prev_status

    updated_fields = {
        "Last Message": lead.message,
        "Intent Tag": intent,
        "Status": updated_status,
        "Last Contact": now,
        "Message Count": new_count,
    }
    record = client.update_lead(existing["id"], updated_fields)
    return {"action": "updated_duplicate", "record": record}
