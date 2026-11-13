"""
Deterministic, rule-based intent router for classifying questions into Live Data, Policy RAG, or Out of Scope.
"""

import re
from typing import Tuple, Dict, Any, Optional

# Keywords that indicate a question is related to parking facility context
PARKING_DOMAIN_KEYWORDS = {
    "park", "parking", "slot", "slots", "floor", "floors", "vehicle", "vehicles",
    "car", "bike", "suv", "ev", "charging", "revenue", "occupancy", "charge",
    "charges", "fee", "fees", "tariff", "rate", "rates", "overstay", "penalty",
    "rule", "rules", "policy", "fine", "ticket", "booking", "reserved", "disabled",
    "exit", "entry", "bay", "bays", "towing", "clamp", "clamped", "grace",
    "khali", "khaali", "batao", "bataiye", "kitna", "kitne", "paise", "paisa",
    "rupee", "rupees", "niyam", "price", "cost", "bhara", "aaj"
}

LIVE_DATA_PATTERNS = [
    (r"\b(available|empty|vacant|free|khali|khaali)\s+(parking\s+)?slots?\b", "AVAILABLE_SLOTS"),
    (r"\b(parking\s+)?slots?\s+(are\s+)?(available|empty|vacant|free|khali|khaali)\b", "AVAILABLE_SLOTS"),
    (r"\b(which|show|list|get|batao|bataiye|kitne)\s+.*(slots?|khali|khaali)\b", "AVAILABLE_SLOTS"),
    (r"\b(khali|khaali)\s+slot\b", "AVAILABLE_SLOTS"),
    (r"\bslots?\s+on\s+floor\s+[1-4]\b", "SLOTS_ON_FLOOR"),
    (r"\bfloor\s+[1-4]\s+(slots?|available|occupancy|khali|khaali)\b", "SLOTS_ON_FLOOR"),
    (r"\b(ev|electric)\s+(charging\s+)?slots?\b", "EV_SLOTS"),
    (r"\b(disabled|handicapped|accessible)\s+(parking\s+)?slots?\b", "DISABLED_SLOTS"),
    (r"\breserved\s+slots?\b", "RESERVED_SLOTS"),
    (r"\b(today'?s?|daily|aaj\s+ki)\s+(parking\s+)?(revenue|kamai|earning)\b", "TODAY_REVENUE"),
    (r"\boccupancy\s+(statistics|stats|percentage|by\s+floor)\b", "OCCUPANCY_STATS"),
    (r"\bhighest\s+occupancy\b", "HIGHEST_OCCUPANCY"),
    (r"\bvehicle\s+movement\b", "VEHICLE_MOVEMENT"),
    (r"\b(active|currently\s+parked)\s+(vehicles?|cars?)\b", "ACTIVE_VEHICLES"),
]

# Policy RAG Intent Sub-rules
POLICY_PATTERNS = [
    (r"\b(parking\s+)?(charges?|price|pricing|rates?|tariff|cost|how\s+much|paise|paisa|kiraya)\b", "POLICY_PRICING"),
    (r"\b(overstay|penalty|penalties|grace\s+period|towing|clamping|fine|fines|nuksan)\b", "POLICY_OVERSTAY"),
    (r"\b(rules?|regulations?|guidelines?|speed\s+limit|liability|prohibited|niyam)\b", "POLICY_RULES"),
    (r"\b(ev\s+charging|idle\s+fee|charging\s+rates?)\b", "POLICY_EV"),
    (r"\b(cancel|cancellation|refund|lost\s+ticket|faq|how\s+to\s+release)\b", "POLICY_FAQ"),
]


def classify_intent(question: str) -> Tuple[str, str]:
    """
    Classify user question into (intent_type, action_key).
    intent_type: 'LIVE_DATA' | 'POLICY' | 'OUT_OF_SCOPE'
    """
    q_clean = question.lower().strip()

    # Step 1: Check domain relevance
    words = set(re.findall(r"\b\w+\b", q_clean))
    has_domain_keyword = bool(words.intersection(PARKING_DOMAIN_KEYWORDS))

    # Step 2: Check Live Data patterns
    for pattern, action_key in LIVE_DATA_PATTERNS:
        if re.search(pattern, q_clean):
            return "LIVE_DATA", action_key

    # Step 3: Check Policy RAG patterns
    for pattern, action_key in POLICY_PATTERNS:
        if re.search(pattern, q_clean):
            return "POLICY", action_key

    # If question mentions parking domain keywords but didn't match explicit patterns, default to POLICY RAG
    if has_domain_keyword:
        return "POLICY", "POLICY_GENERAL"

    # Step 4: Refuse unrelated out-of-scope questions
    return "OUT_OF_SCOPE", "REFUSAL"
