"""
Base agent class.
Handles Groq API calls (OpenAI-compatible free tier), JSON parsing, retry logic, and logging.
All agents inherit from this class.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from groq import Groq, APIConnectionError, RateLimitError, InternalServerError, APIStatusError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger("war_room")

# Groq free-tier — fastest & most capable free model as of 2026
MODEL      = "llama-3.1-8b-instant"
MAX_TOKENS = 1024


class BaseAgent:
    """
    Base class for all war-room agents.

    Uses the official Groq Python SDK.
    API key is read from GROQ_API_KEY environment variable — never hard-coded.
    Free tier: https://console.groq.com  (no credit card required)
    """

    def __init__(self, name: str) -> None:
        self.name   = name
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type((APIConnectionError, RateLimitError, InternalServerError, APIStatusError)),
    )
    def _call_api(self, system: str, user_message: str) -> dict[str, Any]:
        """
        Call the Groq API and parse the JSON response.
        Retries on transient connection / rate-limit errors.
        """
        t0 = time.time()
        logger.info(f"[{self.name}] Sending request to {MODEL}")

        # Guarantee 1-minute reset for Groq Free Tier TPM limit

        response = self.client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_message},
            ],
        )

        elapsed = round(time.time() - t0, 2)
        raw     = response.choices[0].message.content.strip()
        logger.debug(f"[{self.name}] Raw response ({elapsed}s): {raw[:200]}...")

        # Strip markdown code fences if the model wrapped the JSON
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            raw   = "\n".join(lines).strip()

        # NEW: Try to extract JSON object if LLM added preamble/postamble
        if not raw.startswith("{"):
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start != -1 and end > start:
                raw = raw[start:end]
                logger.warning(f"[{self.name}] Stripped preamble/postamble from LLM response")

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"[{self.name}] JSON parse failed: {e}\nRaw output: {raw[:500]}")
            raise RuntimeError(f"[{self.name}] LLM returned non-JSON output after 3 attempts.") from e

        logger.info(f"[{self.name}] Completed in {elapsed}s")
        return parsed

    def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError("Each agent must implement run()")
