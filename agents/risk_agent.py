"""
Agent 4 — Risk / Critic Agent
Challenges assumptions from all prior agents, surfaces unaddressed risks,
and produces a complete risk register.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger("war_room")

SYSTEM_PROMPT = """You are the Risk Officer and internal critic in this war room. Three agents have already submitted their analyses.

Your job is to be the most rigorous voice in the room:
1. Challenge weak assumptions in any of the three agent outputs — what did they take for granted without evidence?
2. Identify risks that NONE of the other agents mentioned explicitly.
3. Describe 2–3 realistic worst-case scenarios that could unfold in the next 24 hours if action is not taken.
4. List specific data or evidence that is currently missing before a high-confidence decision can be made.
5. Build a risk register: top 5 risks, each with likelihood (low/medium/high), impact (low/medium/high/critical), composite rating, and a specific mitigation action.

Rules:
- Do not be polite about weak analysis. If an assumption is unsupported, say so directly.
- Risk ratings must be justified — not just gut feel.
- Mitigations must be concrete (who does what, in what timeframe) — not "investigate further."

Output ONLY valid JSON. No preamble, no markdown fences.

Output schema:
{
  "challenged_assumptions": [
    {"agent": "<PM_Agent|Data_Analyst|Marketing_Comms>", "assumption": "<what they assumed>", "challenge": "<why it's weak>"}
  ],
  "unaddressed_risks": ["<risk 1>", "<risk 2>", "<risk 3>"],
  "worst_case_scenarios": [
    {"scenario": "<description>", "trigger": "<what causes it>", "estimated_impact": "<business impact>"}
  ],
  "evidence_gaps": ["<missing data 1>", "<missing data 2>"],
  "risk_register": [
    {
      "risk": "<description>",
      "likelihood": "low|medium|high",
      "impact": "low|medium|high|critical",
      "rating": "low|medium|high|critical",
      "mitigation": "<concrete action: who + what + when>"
    }
  ]
}"""


class RiskAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Risk_Critic")

    def run(
        self,
        pm_output: dict,
        analyst_output: dict,
        marketing_output: dict,
        anomaly_data: dict,
        aggregated_metrics: dict,
    ) -> dict[str, Any]:
        logger.info("[Risk_Critic] Starting — challenging assumptions and building risk register")

        user_message = f"""You are reviewing the analyses from three agents. Critically evaluate them and produce your JSON output.

## PM Agent Output
{json.dumps(pm_output, separators=(',', ':'))}

## Data Analyst Output
{json.dumps(analyst_output, separators=(',', ':'))}

## Marketing / Comms Agent Output
{json.dumps(marketing_output, separators=(',', ':'))}

## Anomaly Detection Data (raw tool output)
{json.dumps(anomaly_data, separators=(',', ':'))}

## Aggregated Metrics (threshold violations)
{json.dumps(aggregated_metrics, separators=(',', ':'))}

Produce your critical analysis and risk register as a single valid JSON object."""

        result = self._call_api(SYSTEM_PROMPT, user_message)
        risk_register  = result.get("risk_register", [])
        critical_count = sum(1 for r in risk_register if r.get("rating") == "critical")
        logger.info(f"[Risk_Critic] Risk register: {len(risk_register)} risks, {critical_count} critical")
        logger.info(f"[Risk_Critic] Challenged assumptions: {len(result.get('challenged_assumptions', []))}")
        return result
