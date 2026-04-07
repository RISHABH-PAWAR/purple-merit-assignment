"""
Agent 5 — Decision Agent (War Room Coordinator)
Synthesises all four agent outputs and produces the final structured war room decision.

Hard rules enforced programmatically before LLM reasoning:
  - payment_success_rate post-launch avg < 0.970  → Roll Back
  - crash_rate post-launch avg > 0.020            → Roll Back
  - Any critical unmitigated risk in register      → minimum Pause
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger("war_room")

SYSTEM_PROMPT = """You are the War Room Coordinator. You have received analysis from four specialist agents:
- PM Agent: user impact, success criteria pass/fail, preliminary recommendation
- Data Analyst: quantitative anomalies, correlations, confidence level
- Marketing/Comms Agent: reputational risk, communication plan
- Risk/Critic Agent: risk register, challenged assumptions, worst-case scenarios

Your job is to synthesise everything and produce the final launch decision.

HARD RULES (non-negotiable — apply these before weighing anything else):
1. If payment_success_rate post-launch average < 0.970 → decision MUST be "Roll Back"
2. If crash_rate post-launch average > 0.020 → decision MUST be "Roll Back"
3. If any risk in the risk register has rating="critical" AND mitigation is not yet completed → decision MUST be at minimum "Pause"
4. If all critical metrics are within thresholds and sentiment is not strongly negative → "Proceed" is valid

DECISION LOGIC AFTER HARD RULES:
- Weigh: number of critical/high violations, agent consensus, reputational risk, data confidence
- If 3+ agents recommend Pause/Roll Back → align with them unless hard rules dictate otherwise
- Be specific: cite actual metric values and agent conclusions in your rationale

Produce a comprehensive, structured final output. Reference actual numbers.
Every action plan item must have a named owner role (not just "team").
Confidence score: 0.0–1.0. Explain what specific data would push it above 0.85.

Output ONLY valid JSON. No preamble, no markdown fences.

Output schema exactly:
{
  "decision": "Proceed|Pause|Roll Back",
  "hard_rule_triggered": "<rule description or null>",
  "rationale": {
    "key_drivers": ["<driver 1 with metric ref>", "<driver 2>", "..."],
    "metric_references": {
      "<metric_name>": {"pre": <float>, "post": <float>, "change_formatted": "<string>"}
    },
    "feedback_summary": "<string: sentiment + top issues>",
    "agent_consensus": "<string: where agents agreed / disagreed>"
  },
  "risk_register": [
    {
      "risk": "<description>",
      "likelihood": "low|medium|high",
      "impact": "low|medium|high|critical",
      "rating": "low|medium|high|critical",
      "mitigation": "<concrete action>"
    }
  ],
  "action_plan": {
    "window": "24-48 hours",
    "actions": [
      {
        "action": "<description>",
        "owner": "<role>",
        "deadline": "<e.g. 2h, 8h, 24h>",
        "priority": "P0|P1|P2"
      }
    ]
  },
  "communication_plan": {
    "internal": "<Slack/email message>",
    "external": "<status page / customer message>",
    "timing": "<when to send each>"
  },
  "confidence_score": <float 0.0-1.0>,
  "confidence_boosters": ["<what data would increase confidence>"]
}"""


class DecisionAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Decision_Agent")

    def run(
        self,
        pm_output: dict,
        analyst_output: dict,
        marketing_output: dict,
        risk_output: dict,
        aggregated_metrics: dict,
        sentiment_analysis: dict,
    ) -> dict[str, Any]:
        logger.info("[Decision_Agent] Starting final synthesis — war room coordinator")

        # ── Hard rules evaluated in Python before sending to LLM ────────────
        post_avgs = aggregated_metrics.get("post_launch_averages", {})
        payment   = post_avgs.get("payment_success_rate", 1.0)
        crash     = post_avgs.get("crash_rate", 0.0)

        hard_rule_notes: list[str] = []
        if payment < 0.970:
            note = f"HARD RULE TRIGGERED: payment_success_rate={payment:.3f} < 0.970 → Roll Back required"
            hard_rule_notes.append(note)
            logger.warning(f"[Decision_Agent] {note}")
        if crash > 0.020:
            note = f"HARD RULE TRIGGERED: crash_rate={crash:.4f} > 0.020 → Roll Back required"
            hard_rule_notes.append(note)
            logger.warning(f"[Decision_Agent] {note}")

        hard_rule_block = (
            "⚠ IMPORTANT — HARD RULES TRIGGERED (you MUST honour these in your decision):\n"
            + "\n".join(f"  • {n}" for n in hard_rule_notes)
            if hard_rule_notes else ""
        )

        user_message = f"""Synthesise all agent outputs below and produce the final war room decision as a single valid JSON object.

{hard_rule_block}

## PM Agent Output
{json.dumps(pm_output, separators=(',', ':'))}

## Data Analyst Output
{json.dumps(analyst_output, separators=(',', ':'))}

## Marketing / Comms Agent Output
{json.dumps(marketing_output, separators=(',', ':'))}

## Risk / Critic Agent Output
{json.dumps(risk_output, separators=(',', ':'))}

## Aggregated Metrics (for hard rule verification)
{json.dumps(aggregated_metrics, separators=(',', ':'))}

## Sentiment Analysis Summary
{json.dumps(sentiment_analysis, separators=(',', ':'))}

Produce the final war room decision as a single valid JSON object."""

        result     = self._call_api(SYSTEM_PROMPT, user_message)
        
        # ── Final programmatic verification of critical safety rules ────────
        if payment < 0.970 or crash > 0.020:
            original_decision = result.get("decision", "unknown")
            if original_decision != "Roll Back":
                logger.warning(f"[Decision_Agent] Overriding LLM decision '{original_decision}' with 'Roll Back' due to safety thresholds.")
                result["decision"] = "Roll Back"
                result["hard_rule_triggered"] = f"CRITICAL THRESHOLD BREACHED: payment={payment:.3f} or crash={crash:.3f}"

        decision   = result.get("decision", "unknown")
        confidence = result.get("confidence_score", 0.0)
        logger.info(f"[Decision_Agent] ★ FINAL DECISION: {decision} (confidence: {confidence:.0%})")
        return result
