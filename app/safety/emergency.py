"""Emergency and self-harm response messages.

No invented phone numbers: users are directed to their local emergency
services generically, since valid numbers differ by country.
"""

from __future__ import annotations

EMERGENCY_MESSAGE = (
    "This sounds like it could be a medical emergency. I can't provide "
    "emergency medical help. Please contact your local emergency services "
    "immediately or go to the nearest emergency department. If someone is "
    "with you, ask them for help right away."
)

SELF_HARM_MESSAGE = (
    "I'm really sorry you're going through this. I can't provide the support "
    "you deserve, but you don't have to face this alone. Please reach out to "
    "your local emergency services or a crisis support line in your country, "
    "or speak with a mental health professional or someone you trust as soon "
    "as possible."
)
