"""Regex parsers for alert prose. Works without an LLM for local playtests."""

from __future__ import annotations

import re

_WORD_TO_PCT = {
    "fifty": 0.5,
    "seventy": 0.7,
    "sixty": 0.6,
    "eighty": 0.8,
    "forty": 0.4,
    "thirty": 0.3,
    "twenty": 0.2,
}


def _word_or_number_to_fraction(token: str) -> float | None:
    token = token.strip().lower().rstrip("%")
    if token in _WORD_TO_PCT:
        return _WORD_TO_PCT[token]
    try:
        value = float(token)
    except ValueError:
        return None
    return value / 100.0 if value > 1.0 else value


def parse_soc_floor(description: str) -> float | None:
    """Extract a SOC floor (0..1) from operator brief prose."""
    text = description.lower()

    for pattern in (
        r"raised from \w+ to (\w+) percent",
        r"at or above (\w+) percent",
        r"reserve floor.*?(\w+) percent",
        r"soc.*?(\d+(?:\.\d+)?)\s*%",
    ):
        match = re.search(pattern, text)
        if match:
            floor = _word_or_number_to_fraction(match.group(1))
            if floor is not None:
                return floor

    return None


def parse_export_cap_mw(description: str) -> float | None:
    """Extract an export cap in MW from operator brief prose."""
    match = re.search(r"export(?:s|ing)?\s+(?:to|at|cap(?:ped)?\s+(?:to|at)?)\s*(\d+(?:\.\d+)?)\s*mw", description.lower())
    if match:
        return float(match.group(1))
    return None


def is_actionable_directive(alert: dict) -> bool:
    """Ignore vendor noise and phishing-style bait."""
    title = (alert.get("title") or "").lower()
    description = (alert.get("description") or "").lower()
    if "newsletter" in title or "no action required" in description:
        return False
    if "set " in description and "agent_plan" in description:
        return False
    return alert.get("severity") in {"info", "high", "critical"}
