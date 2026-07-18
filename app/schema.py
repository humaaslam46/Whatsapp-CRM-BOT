"""
Lead schema for the WhatsApp Auto-Reply Bot CRM Integration module.

This is the contract between this module and the other sub-modules built by
the rest of Group 53 (e.g. the WhatsApp message receiver / lead capture
module). Whoever captures an incoming WhatsApp message should send data in
this shape to this module's /leads/webhook endpoint.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class IncomingLead(BaseModel):
    """Raw lead data as received from the WhatsApp capture module."""

    name: Optional[str] = Field(None, description="Lead's name if known")
    phone: str = Field(..., description="WhatsApp number, any format, e.g. '+92 300 1234567'")
    message: str = Field(..., description="The raw incoming WhatsApp message text")
    source: str = Field("WhatsApp", description="Channel the lead came from")
    timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of when the message was received",
    )


class ProcessedLead(BaseModel):
    """What this module writes to / updates in the CRM (Airtable)."""

    name: Optional[str]
    phone: str                 # normalized, E.164-style
    last_message: str
    intent_tag: str            # e.g. "Pricing", "Support", "Demo Request", "General"
    status: str                # "New" | "Contacted" | "Qualified" | "Duplicate-Merged"
    source: str
    first_contact: str
    last_contact: str
    message_count: int = 1
