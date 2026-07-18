"""
Rule-based auto-reply generation.

Reuses the intent tag from app/tagging.py to pick a canned response.
This is intentionally simple (no LLM/API key needed) per project scope -
swap in an LLM call here later without touching main.py or crm.py.
"""

INTENT_REPLIES = {
    "Pricing": (
        "Thanks for your interest! Our plans start at a range depending on your needs. "
        "A team member will follow up shortly with a detailed quote."
    ),
    "Demo Request": (
        "We'd love to show you around! A team member will reach out shortly to schedule your demo."
    ),
    "Support": (
        "Sorry to hear you're running into an issue. We've logged your message and "
        "a support agent will get back to you as soon as possible."
    ),
    "Purchase Intent": (
        "Great to hear you're ready to move forward! A team member will contact you "
        "shortly to complete your order."
    ),
    "General": (
        "Thanks for messaging SafeX Solutions! A team member will get back to you shortly."
    ),
}

DEFAULT_REPLY = INTENT_REPLIES["General"]


def generate_reply(intent_tag: str) -> str:
    return INTENT_REPLIES.get(intent_tag, DEFAULT_REPLY)
