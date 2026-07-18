"""
De-duplication logic.

Leads are considered duplicates if they share the same normalized phone
number, regardless of how the number was formatted in the incoming message
(spaces, dashes, missing country code, etc.).
"""

import re


def normalize_phone(raw_phone: str, default_country_code: str = "92") -> str:
    """
    Normalize a phone number to a consistent E.164-ish digit string.

    Examples (default_country_code='92' for Pakistan):
        '0300-1234567'      -> '923001234567'
        '+92 300 1234567'   -> '923001234567'
        '92 3001234567'     -> '923001234567'
        '3001234567'        -> '923001234567'
    """
    digits = re.sub(r"\D", "", raw_phone or "")

    if digits.startswith("00"):
        digits = digits[2:]

    if digits.startswith("0"):
        digits = default_country_code + digits[1:]
    elif not digits.startswith(default_country_code):
        digits = default_country_code + digits

    return digits


def find_existing_lead(normalized_phone: str, existing_records: list[dict]) -> dict | None:
    """
    Look for an existing CRM record matching this phone number.

    existing_records: list of Airtable record dicts, each expected to have
    fields['Phone'] already normalized (this module always writes normalized
    numbers, so lookups stay consistent).
    """
    for record in existing_records:
        if record.get("fields", {}).get("Phone") == normalized_phone:
            return record
    return None
