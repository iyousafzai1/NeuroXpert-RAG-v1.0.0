"""Minimal Ollama HTTP client (stdlib only).

Ollama exposes a local HTTP API (default: http://127.0.0.1:11434).

We intentionally avoid external dependencies so the pilots remain easy to run.
"""

from __future__ import annotations

import time
import json
import http.client
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class OllamaClient:
    base_url: str = "http://127.0.0.1:11434"
    timeout_s: int = 240
    max_retries: int = 3
    retry_backoff_s: float = 2.0

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call /api/generate (non-streaming) and return decoded JSON."""

        url = self.base_url.rstrip("/") + "/api/generate"
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system is not None:
            payload["system"] = system
        if options:
            payload["options"] = options

        data = json.dumps(payload).encode("utf-8")
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Unsupported Ollama base_url scheme: {parsed.scheme}")

        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"

        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                if parsed.scheme == "https":
                    conn: http.client.HTTPConnection = http.client.HTTPSConnection(host, port, timeout=self.timeout_s)
                else:
                    conn = http.client.HTTPConnection(host, port, timeout=self.timeout_s)

                conn.request(
                    "POST",
                    path,
                    body=data,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "User-Agent": "NeuroXpert-RAG/0.1",
                        "Connection": "close",
                    },
                )
                resp = conn.getresponse()
                raw = resp.read()
                status = resp.status
                conn.close()

                if status >= 400:
                    detail = raw.decode("utf-8", errors="replace")
                    raise RuntimeError(f"Ollama HTTP {status}: {detail}")
                last_err = None
                break
            except Exception as e:
                # Some disconnects bubble up as generic Exceptions.
                last_err = e

            if attempt < self.max_retries:
                time.sleep(self.retry_backoff_s * (2**attempt))
            else:
                break

        if last_err is not None:
            raise RuntimeError(
                "Ollama request failed after retries. Ensure the Ollama app is running and the model is loaded. "
                f"Last error: {last_err}"
            ) from last_err

        try:
            return json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Failed to parse Ollama JSON response: {raw[:500]!r}") from e
