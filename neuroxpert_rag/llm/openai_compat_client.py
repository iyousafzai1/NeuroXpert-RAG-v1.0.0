"""Minimal OpenAI-compatible chat client (stdlib only).

vLLM exposes an OpenAI-compatible HTTP API at /v1/chat/completions.  This
client intentionally mirrors the small ``generate`` interface used by the
Ollama client so pilot scripts can switch backends without changing prompts.
"""

from __future__ import annotations

import http.client
import json
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class OpenAICompatClient:
    base_url: str = "http://127.0.0.1:8000/v1"
    timeout_s: int = 240
    max_retries: int = 3
    retry_backoff_s: float = 2.0
    api_key: Optional[str] = None

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call /chat/completions and return an Ollama-like response dict."""

        options = options or {}
        base = self.base_url.rstrip("/")
        url = base if base.endswith("/chat/completions") else base + "/chat/completions"

        messages = []
        if system is not None:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": options.get("temperature", 0.1),
            "top_p": options.get("top_p", 0.9),
        }
        max_tokens = options.get("max_tokens", options.get("num_predict"))
        if max_tokens is not None:
            payload["max_tokens"] = int(max_tokens)

        data = json.dumps(payload).encode("utf-8")
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Unsupported OpenAI-compatible base_url scheme: {parsed.scheme}")

        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "NeuroXpert-RAG/0.1",
            "Connection": "close",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        raw = b""
        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                if parsed.scheme == "https":
                    conn: http.client.HTTPConnection = http.client.HTTPSConnection(host, port, timeout=self.timeout_s)
                else:
                    conn = http.client.HTTPConnection(host, port, timeout=self.timeout_s)
                conn.request("POST", path, body=data, headers=headers)
                resp = conn.getresponse()
                raw = resp.read()
                status = resp.status
                conn.close()

                if status >= 400:
                    detail = raw.decode("utf-8", errors="replace")
                    raise RuntimeError(f"OpenAI-compatible HTTP {status}: {detail}")
                last_err = None
                break
            except Exception as e:
                last_err = e

            if attempt < self.max_retries:
                time.sleep(self.retry_backoff_s * (2**attempt))

        if last_err is not None:
            raise RuntimeError(
                "OpenAI-compatible request failed after retries. Ensure the vLLM server is running and reachable. "
                f"Last error: {last_err}"
            ) from last_err

        try:
            obj = json.loads(raw.decode("utf-8"))
            content = obj["choices"][0]["message"].get("content") or ""
        except Exception as e:
            raise RuntimeError(f"Failed to parse OpenAI-compatible JSON response: {raw[:500]!r}") from e

        return {"response": content, "raw": obj}
