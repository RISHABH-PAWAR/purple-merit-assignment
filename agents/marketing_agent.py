"""
Agent 3 — Marketing / Comms Agent
Assesses reputational risk, messaging urgency, and drafts internal + external comms.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger("war_room")

SYSTEM_PROMPT = """You are the Head of Marketing & Customer Communications.

A product launch is experiencing issues and the war room is deciding whether to Proceed, Pause, or Roll Back.

Your job is to:
1. Assess the reputational risk based on user feedback themes (quantify: how many mentions of what issues).
2. Determine the urgency of customer communication: immediate (< 1 hour) / within_4h / within_24h / monitor_only.
3. Draft a short internal message for the #product-war-room Slack channel (3–4 sentences, factual, no spin).
4. Draft a short external status page message for affected customers (honest, no corporate speak, under 80 words).
5. Identify any feedback that is a PR risk if left unaddressed (double charges, data issues, etc.).

Rules:
- Customers hate vague language. Be specific about what is known and what is being done.
- Do not minimise issues that have clear data support.
- The internal message should state facts plainly — this is not a press release.

Output ONLY valid JSON. No preamble, no markdown fences.

Output schema:
{
  "reputational_risk_level": "low|medium|high|critical",
  "reputational_risk_reasoning": "<string>",
  "communication_urgency": "immediate|within_4h|within_24h|monitor_only",
  "internal_message": "<string: Slack message>",
  "external_message": "<string: status page update>",
  "pr_risk_flags": [
    {"issue": "<description>", "risk_level": "medium|high|critical", "why": "<explanation>"}
  ]
}"""


class MarketingAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Marketing_Comms")

    def run(
        self,
        sentiment_analysis: dict,
        pm_output: dict,
        release_notes: str,
        sample_feedback: dict,
    ) -> dict[str, Any]:
        logger.info("[Marketing_Comms] Starting — assessing reputational risk and drafting comms")

        user_message = f"""Assess the reputational and communications situation and produce your JSON output.

## User Feedback Sentiment Analysis
{json.dumps(sentiment_analysis, separators=(',', ':'))}

## Sampled Representative Feedback (subset of total)
{json.dumps(sample_feedback, separators=(',', ':'))}

## PM Agent Preliminary Assessment
{json.dumps(pm_output, separators=(',', ':'))}

## Release Notes (for context on what changed)
{release_notes}

Produce your analysis as a single valid JSON object."""

        result = self._call_api(SYSTEM_PROMPT, user_message)
        logger.info(f"[Marketing_Comms] Reputational risk: {result.get('reputational_risk_level', 'unknown')}")
        logger.info(f"[Marketing_Comms] Communication urgency: {result.get('communication_urgency', 'unknown')}")
        return result
