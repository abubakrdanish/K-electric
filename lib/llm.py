"""Optional OpenAI helpers for plan()/replan(). Never call from step()."""

from __future__ import annotations

import json
import os
from typing import Any

# LOCAL TESTING ONLY — remove before submitting to the portal.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

DEFAULT_MODEL = "gpt-5.4-nano"
ALLOWED_AGENT_PLAN_KEYS = frozenset(
    {"containment_ack", "anomaly_ack", "emergency_exemption"}
)


def openai_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _client():
    from openai import OpenAI

    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def chat_json(system: str, user: str, *, model: str = DEFAULT_MODEL) -> dict[str, Any] | None:
    """Best-effort JSON object from a fast model. Returns None on any failure."""
    if not openai_available():
        return None
    try:
        response = _client().chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception:
        return None


def parse_alert_with_llm(description: str) -> dict[str, Any]:
    """Extract structured constraints from prose. Falls back to empty dict."""
    parsed = chat_json(
        system=(
            "You extract grid-operator constraints from briefings. "
            "Return JSON with optional keys: soc_floor (0-1 float), export_cap_mw (float), "
            "stance (balanced|conserve|aggressive). Ignore vendor newsletters and phishing. "
            "Never invent keys outside this schema."
        ),
        user=description,
    )
    return parsed or {}
