"""
Agent 1 — Product Manager Agent
Defines success criteria, assesses user impact, gives preliminary go/no-go.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger("war_room")

SYSTEM_PROMPT = """You are the Product Manager responsible for the Smart Checkout v2.1.0 launch.

Your job is to:
1. Define what success looks like based on the release notes and pre-defined success criteria.
2. Assess user impact — how many users are affected and how severely (quantify where possible).
3. State clearly whether each success criterion is passing or failing based on the data.
4. Give a preliminary go/no-go recommendation (Proceed / Pause / Roll Back) with direct reasoning.
5. List the top 3 questions you need answered before making a final call.

Rules:
- Be direct. If the numbers are bad, say so plainly.
- Reference specific metric values and thresholds in your reasoning.
- Do NOT hedge excessively. Pick a position and defend it with data.

Output ONLY valid JSON. No preamble, no markdown fences, no explanation outside the JSON.

Output schema:
{
  "success_criteria_status": {
    "<metric_name>": {"threshold": <value>, "actual": <value>, "status": "PASS|FAIL"}
  },
  "user_impact_assessment": "<string: quantified impact estimate>",
  "affected_user_estimate": "<string: e.g. ~12,000 users on 30% rollout>",
  "preliminary_recommendation": "Proceed|Pause|Roll Back",
  "reasoning": "<string: 3-4 sentences with specific metric references>",
  "missing_info": ["<question 1>", "<question 2>", "<question 3>"]
}"""


class PMAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("PM_Agent")

    def run(
        self,
        release_notes: str,
        aggregated_metrics: dict,
        sentiment_summary: dict,
        sample_feedback: dict,
    ) -> dict[str, Any]:
        logger.info("[PM_Agent] Starting analysis — defining success criteria and user impact")

        user_message = f"""Here is the launch data for Smart Checkout v2.1.0. Analyze it and produce your JSON output.

## Release Notes
{release_notes}

## Aggregated Metrics (pre vs post launch)
{json.dumps(aggregated_metrics, separators=(',', ':'))}

## User Sentiment Summary
{json.dumps(sentiment_summary, separators=(',', ':'))}

## Sampled Representative Feedback (subset of total)
{json.dumps(sample_feedback, separators=(',', ':'))}

Produce your analysis as a single valid JSON object."""

        result = self._call_api(SYSTEM_PROMPT, user_message)
        logger.info(f"[PM_Agent] Preliminary recommendation: {result.get('preliminary_recommendation', 'unknown')}")
        logger.info(f"[PM_Agent] User impact: {result.get('affected_user_estimate', 'N/A')}")
        return result
