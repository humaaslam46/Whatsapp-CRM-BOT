"""
FastAPI service for the CRM Integration module.

This is the integration point for the rest of Group 53: whichever teammate
owns the WhatsApp message-receiving module should POST each incoming
message here as JSON matching the IncomingLead schema. This module takes it
from there (dedup, tagging, writing to Airtable).

Run locally:
    uvicorn app.main:app --reload --port 8001

Test it:
    curl -X POST http://localhost:8001/leads/webhook \\
      -H "Content-Type: application/json" \\
      -d '{"name": "Ali Raza", "phone": "0300-1234567", "message": "What is the price?"}'
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

from app.schema import IncomingLead
from app.crm import process_lead
from app.airtable_client import AirtableClient
from app.reply import generate_reply

app = FastAPI(title="SafeX WhatsApp Bot - CRM Integration Module")

# Single shared client. Falls back to "not connected" if env vars aren't set
# -- see README.md for how to configure Airtable credentials.
client = AirtableClient()


@app.get("/health")
def health():
    return {"status": "ok", "airtable_connected": client.is_connected}


@app.post("/leads/webhook")
def receive_lead(lead: IncomingLead):
    if not client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Airtable is not configured. Set AIRTABLE_API_KEY / AIRTABLE_BASE_ID env vars.",
        )
    result = process_lead(lead, client)
    return result


@app.get("/leads")
def list_leads():
    if not client.is_connected:
        raise HTTPException(status_code=503, detail="Airtable is not configured.")
    return client.get_all_leads()


@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """
    This is the URL you paste into Twilio's WhatsApp Sandbox settings
    ("When a message comes in"). Twilio POSTs incoming WhatsApp messages
    here as form-encoded data (not JSON) with fields like:
        From: "whatsapp:+923001234567"
        Body: "What is the price?"
        ProfileName: "Ali Raza"   (the sender's WhatsApp display name)

    We convert that into our IncomingLead shape, run it through the same
    process_lead() pipeline used by /leads/webhook (dedup + tagging +
    Airtable write), then reply with TwiML XML so Twilio sends the
    auto-reply back to the user on WhatsApp.
    """
    form = await request.form()
    raw_from = form.get("From", "")          # e.g. "whatsapp:+923001234567"
    phone = raw_from.replace("whatsapp:", "").strip()
    body = form.get("Body", "")
    profile_name = form.get("ProfileName")

    lead = IncomingLead(name=profile_name, phone=phone, message=body, source="WhatsApp (Twilio)")

    reply_text = generate_reply("General")
    if client.is_connected:
        result = process_lead(lead, client)
        intent = result["record"]["fields"].get("Intent Tag", "General")
        reply_text = generate_reply(intent)
    # If Airtable isn't configured, we still reply so the bot doesn't go silent,
    # just without CRM logging for that message.

    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response><Message>{}</Message></Response>"
    ).format(reply_text)

    return Response(content=twiml, media_type="application/xml")
