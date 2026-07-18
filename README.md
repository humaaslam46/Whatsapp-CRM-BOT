# CRM Integration Module — WhatsApp Auto-Reply Bot
**SafeX Solutions ML Internship — Group 53 — Week 2 individual task**
**Built by:** Huma Aslam

## What this is

This module is one piece of the group's WhatsApp Auto-Reply Bot. Its job:
whenever the bot's message-capture piece (built by another teammate)
receives a WhatsApp message from a lead, this module

1. **Normalizes** the phone number so the same person is recognized
   regardless of how their number was formatted.
2. **De-duplicates** — if the phone number already exists in the CRM, the
   existing record is updated instead of a new one being created.
3. **Tags intent** — classifies the message as `Pricing`, `Demo Request`,
   `Support`, `Purchase Intent`, or `General` (rule-based keyword matching,
   lemmatized with spaCy for robustness; swappable for an LLM classifier
   later without touching other files).
4. **Writes to Airtable** — creates or updates the lead record, including a
   `Status` field (`New` -> `Contacted` on repeat contact).

## Architecture

```
Teammate's WhatsApp        This module                     Airtable
capture module    ---->    POST /leads/webhook   ---->    Leads table
                            (FastAPI)
                              |
                              v
                    dedup.py + tagging.py + crm.py
```

- `app/schema.py` — the `IncomingLead` data contract other modules send data in.
- `app/dedup.py` — phone number normalization + duplicate lookup.
- `app/tagging.py` — intent classification.
- `app/crm.py` — orchestrates dedup + tagging + create/update.
- `app/airtable_client.py` — Airtable API wrapper, plus `MockAirtableClient`
  for offline demo/testing.
- `app/main.py` — FastAPI service exposing the module to the rest of the bot.

## Airtable setup

1. Create a new Airtable base (or a table inside the shared team base if one exists).
2. Create a table named `Leads` with these fields:

   | Field name      | Type            |
   |-----------------|-----------------|
   | Name            | Single line text |
   | Phone           | Single line text (normalized, e.g. `923001234567`) |
   | Last Message    | Long text       |
   | Intent Tag      | Single select (`Pricing`, `Demo Request`, `Support`, `Purchase Intent`, `General`) |
   | Status          | Single select (`New`, `Contacted`, `Qualified`, `Lost`) |
   | Source          | Single line text |
   | First Contact   | Date/time       |
   | Last Contact    | Date/time       |
   | Message Count   | Number          |

3. Get a Personal Access Token (Airtable account settings -> Developer hub)
   with read/write scope on this base, and the Base ID (from the API docs
   page for your base).

4. Set environment variables before running:
   ```bash
   export AIRTABLE_API_KEY="your_pat_here"
   export AIRTABLE_BASE_ID="appXXXXXXXXXXXXXX"
   export AIRTABLE_TABLE_NAME="Leads"
   ```

## How to run

Install dependencies:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # optional, improves tagging
```

**Option A — the demo notebook (no Airtable credentials needed):**
```bash
jupyter notebook CRM_Integration_Demo.ipynb
```
Runs the full pipeline against `sample_leads.json` using an in-memory mock
CRM, so you (or an evaluator) can see input/output without any setup.

**Option B — the real service (for integration with teammates' modules):**
```bash
uvicorn app.main:app --reload --port 8001
```
Then teammates POST captured leads to `http://localhost:8001/leads/webhook`
with a JSON body like:
```json
{"name": "Ali Raza", "phone": "0300-1234567", "message": "What is the price?"}
```
Check `GET /leads` to see everything currently in the CRM, and `GET
/health` to confirm Airtable is connected.

## How it integrates with the rest of Group 53

- This module **does not** read WhatsApp messages directly — it expects
  another teammate's capture module to forward each message as JSON to
  `/leads/webhook`. Confirmed this boundary with the group so nobody
  duplicates the WhatsApp API integration.
- This module **does not** send auto-replies — that's a separate
  response-generation module elsewhere in the project.
- The Airtable base is the single shared source of truth other modules
  (e.g. a reporting/dashboard module, if the group has one) can also read from.

## Testing notes

- `sample_leads.json` includes 5 sample messages, 3 of which are from the
  same person with differently-formatted phone numbers, to demonstrate
  de-duplication.
- The notebook shows this collapses to 3 CRM records, with the repeat
  lead's status moving from `New` to `Contacted` and `Message Count`
  incrementing.

## Submission checklist (for this Week 2 task)

- [x] Jupyter notebook with sample input/output (`CRM_Integration_Demo.ipynb`)
- [x] Source code (`app/`)
- [x] This documentation (`README.md`)
- [x] Screenshots or short recording of the module working — take these
      while running the notebook and/or the FastAPI service with `curl`/Postman
- [x] Push to GitHub repository
- [x] Record 5–15 min explanation video (face visible): cover architecture,
      challenges (e.g. phone number formatting inconsistencies), tools used,
      and a live demo
- [x] Submit anonymous feedback on Group Leader via the weekly form by Friday
