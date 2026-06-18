"""Utilities for robustly parsing structured JSON from LLM outputs."""

from __future__ import annotations

import json
import re
from typing import Any, Dict


_JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def extract_single_json_object(text: str) -> Dict[str, Any]:
    """Extract the first JSON object from a text blob.

    This is defensive: even with strict prompting, models sometimes wrap JSON
    with extra tokens.
    """

    text = (text or "").strip()
    if not text:
        raise ValueError("Empty model output")

    # Fast path: valid JSON already.
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    m = _JSON_OBJ_RE.search(text)
    if not m:
        raise ValueError(f"No JSON object found in output: {text[:200]!r}")

    candidate = m.group(0)
    obj = json.loads(candidate)
    if not isinstance(obj, dict):
        raise ValueError("Extracted JSON is not an object")
    return obj
