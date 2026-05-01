from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def gemini_available() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def generate_scenario(profile_hint: str = "balanced") -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    prompt = (
        "Generate one time-constrained behavioral decision scenario for a system "
        "called TCBIS. Return strict JSON only with keys: scenario, time_limit, "
        "category, options. options must be five objects with key A-E, label, text, "
        "intent, weights containing risk, information, explore, curiosity, pressure. "
        f"Adaptive profile hint: {profile_hint}."
    )
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={api_key}"
    )
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Gemini request failed: {exc}") from exc

    text = payload["candidates"][0]["content"]["parts"][0]["text"].strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1)
    return json.loads(text)
