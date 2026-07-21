# WhatsApp Auto-Reply Bot — SafeX Solutions ML Internship
**Group 23 — Week 2 — Built individually by Huma Aslam**

> **Note on scope:** This project was originally assigned as a 9-person group
> task, with CRM Integration as my individual Week 2 module. Since my
> teammates' modules (WhatsApp message receiving, auto-reply generation)
> were not delivered, I built the full end-to-end bot myself so the project
> would be complete and demoable. The CRM Integration piece below remains
> the module I was formally assigned and graded on; the WhatsApp-receiving
> and auto-reply pieces were added to make the system fully functional.

## What this bot does

1. A user sends a WhatsApp message to the bot's number (via Twilio's
   WhatsApp Sandbox).
2. The bot receives it, logs it as a lead in Airtable — **de-duplicating**
   by phone number and **tagging** the message's intent.
3. The bot sends back an automatic reply, chosen based on that intent.

```
User's WhatsApp
      |
      v
Twilio WhatsApp Sandbox  (receives the message, forwards it as a webhook)
      |
      v
ngrok  (tunnels the public Twilio webhook to your local machine)
      |
      v
FastAPI app — POST /whatsapp/webhook
      |
      +--> app/dedup.py     (normalize phone, check for existing lead)
      +--> app/tagging.py   (classify message intent — spaCy + keywords)
      +--> app/crm.py       (orchestrates the above, writes to Airtable)
      +--> app/reply.py     (pick a canned reply based on intent)
      |
      v
Airtable "Leads" table  <---- CRM record created/updated
      |
Twilio  <---- TwiML reply sent back
      |
      v
User's WhatsApp (receives the auto-reply)
```

## Project structure

```
safex-crm-integration/
├── app/
│   ├── schema.py            # IncomingLead / ProcessedLead data contracts
│   ├── dedup.py              # phone normalization + duplicate lookup
│   ├── tagging.py            # intent classification (spaCy + keywords)
│   ├── reply.py               # canned auto-reply text per intent
│   ├── airtable_client.py    # Airtable API wrapper + MockAirtableClient
│   ├── crm.py                 # ties dedup + tagging + Airtable together
│   └── main.py                 # FastAPI app: /leads/webhook, /whatsapp/webhook
├── CRM_Integration_Demo.ipynb   # notebook demo using mock data (no credentials needed)
├── sample_leads.json
├── requirements.txt
└── README.md
```

## Module breakdown

### 1. WhatsApp receiving (Twilio Sandbox)
Real WhatsApp messages arrive via Twilio's free Sandbox. Twilio POSTs each
incoming message as form data to whatever public URL is configured in the
Sandbox settings — in this project, an ngrok tunnel pointing at the local
FastAPI server's `/whatsapp/webhook` endpoint.

### 2. CRM Integration (the originally assigned module)
- **De-duplication** (`dedup.py`): normalizes phone numbers to a consistent
  digit format regardless of spacing, dashes, or missing country codes, so
  the same person is recognized across multiple messages.
- **Intent tagging** (`tagging.py`): classifies each message as `Pricing`,
  `Demo Request`, `Support`, `Purchase Intent`, or `General`, using spaCy
  lemmatization plus keyword matching.
- **CRM writes** (`crm.py`, `airtable_client.py`): creates a new Airtable
  record for a first-time lead, or updates the existing record (bumping
  `Status` from `New` to `Contacted`, incrementing `Message Count`) for a
  repeat contact.

### 3. Auto-reply generation
- **`reply.py`**: simple rule-based responses, one canned reply per intent
  tag. No external API/LLM key required. Swappable for an LLM-based
  generator later without touching any other file.
- The FastAPI endpoint returns the reply as **TwiML** XML, which Twilio
  reads and sends back to the user on WhatsApp — no outbound Twilio API
  call or credentials needed for this direction.

## Airtable setup

Base: `Safex Whatsapp BOT CRM`, table: `Leads`, with these fields:

| Field name      | Type            |
|-----------------|-----------------|
| Name            | Single line text |
| Phone           | Single line text (normalized, e.g. `923001234567`) |
| Last Message    | Long text       |
| Intent Tag      | Single select — options: `Pricing`, `Demo Request`, `Support`, `Purchase Intent`, `General` |
| Status          | Single select — options: `New`, `Contacted`, `Qualified`, `Lost` |
| Source          | Single line text |
| First Contact   | Date, with "Include time" enabled |
| Last Contact    | Date, with "Include time" enabled |
| Message Count   | Number          |

Credentials needed: a Personal Access Token (Airtable Developer Hub, with
`data.records:read` + `data.records:write` scopes on this base) and the
Base ID (from the base's API documentation page).

## How to run this end-to-end

**1. Install dependencies:**
```powershell
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # optional, improves tagging
```

**2. Set environment variables** (each new terminal session):
```powershell
$env:AIRTABLE_API_KEY="your_token_here"
$env:AIRTABLE_BASE_ID="your_base_id_here"
$env:AIRTABLE_TABLE_NAME="Leads"
```

**3. Start the server:**
```powershell
uvicorn app.main:app --reload --port 8001
```

**4. In a second terminal, expose it publicly with ngrok:**
```powershell
ngrok http 8001
```
Copy the `https://....ngrok-free.app` (or `.dev`) forwarding URL it prints.

**5. Connect Twilio's WhatsApp Sandbox:**
- Twilio Console → Messaging → Try it out → WhatsApp Sandbox Settings
- Join the sandbox from your phone by WhatsApp-messaging the join code to
  the sandbox number
- Set "When a message comes in" to `<your-ngrok-url>/whatsapp/webhook`,
  method POST, and save

**6. Test it for real:** message the Twilio sandbox number from your phone.
You should get an automatic reply back, and a new/updated row should
appear in Airtable within a few seconds.

## Testing without WhatsApp/Twilio (offline demo)

- **`CRM_Integration_Demo.ipynb`** — runs the dedup + tagging + CRM logic
  against `sample_leads.json` using an in-memory `MockAirtableClient`, so
  it works with zero setup or credentials.
- **`/leads/webhook`** — a plain JSON endpoint (separate from the WhatsApp
  one) for testing the CRM logic directly with `curl`/PowerShell without
  needing Twilio or ngrok running:
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:8001/leads/webhook" -Method Post -Body '{"name": "Ali Raza", "phone": "0300-1234567", "message": "What is the price?"}' -ContentType "application/json"
  ```
- **`http://localhost:8001/docs`** — FastAPI's interactive Swagger UI, useful
  for a visual demo in the explanation video.

## Known limitations / notes for evaluators

- Auto-replies are rule-based (5 canned responses by intent), not LLM-generated,
  per project scope decisions made for this iteration.
- Twilio's Sandbox is a free testing environment — not a production WhatsApp
  Business number. Production would require WhatsApp Business API approval.
- The CRM Integration module (`dedup.py`, `tagging.py`, `crm.py`,
  `airtable_client.py`) was designed to be reusable regardless of which
  module sends it leads — it exposes a plain JSON webhook (`/leads/webhook`)
  independent of the WhatsApp-specific one (`/whatsapp/webhook`), so it
  would integrate cleanly with teammates' modules if those are added later.

## Submission checklist

- [x] Jupyter notebook with sample input/output
- [x] Source code
- [x] This documentation
- [x] Screenshots / recording of the module working (Airtable rows + WhatsApp conversation)
- [x] Push to GitHub repository
- [x] Record 5–15 min explanation video (face visible): architecture, challenges, tools, live demo
- [x] Submit anonymous feedback on Group Leader via the weekly form by Friday

---
## 👤 Author

**Huma Aslam**
GitHub: [@humaaslam46](https://github.com/humaaslam46)
LinkedIn: [@huma-aslam01](https://linkedin.com/in/huma-aslam01)
