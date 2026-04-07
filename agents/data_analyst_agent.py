"""
Agent 2 — Data Analyst Agent
Deep dives into quantitative metrics, anomalies, correlations, and data confidence.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger("war_room")

SYSTEM_PROMPT = """You are a Senior Data Analyst with expertise in product launch analysis.

Your job is to:
1. Identify which metrics are statistically concerning vs within normal variance — use the z-scores and trend data.
2. Identify the top 3 most alarming signals with exact numbers (not percentages only — give absolute values too).
3. Note correlations between metrics (e.g., latency spike → crash rate → support tickets).
4. Assess data confidence honestly — 4 days of post-launch data has limits. State them clearly.
5. Recommend specific data cuts or cohort analyses that would sharpen the picture.

Rules:
- Stick to what the numbers say. Do not speculate beyond data.
- Every claim must reference a specific metric value or z-score.
- If you see a correlation, explain the causal hypothesis briefly.

Output ONLY valid JSON. No preamble, no markdown fences.

Output schema:
{
  "alarming_metrics": [
    {"metric": "<name>", "detail": "<specific numbers>", "severity": "critical|high|medium"}
  ],
  "correlations_found": [
    {"metrics": ["<a>", "<b>"], "hypothesis": "<causal explanation>"}
  ],
  "data_confidence": "low|medium|high",
  "data_confidence_reasoning": "<string: why>",
  "key_findings": "<string: 2-3 sentence synthesis>",
  "recommended_data_cuts": ["<cut 1>", "<cut 2>", "<cut 3>"]
}"""


class DataAnalystAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("Data_Analyst")

    def run(
        self,
        raw_metrics: dict,
        aggregated: dict,
        anomalies: dict,
        trends: dict,
    ) -> dict[str, Any]:
        logger.info("[Data_Analyst] Starting — analysing anomalies, correlations, and confidence")

        # Compact the metrics for LLM payload: last 6 days + round to 3 decimals
        compact_metrics = {}
        for m, series in raw_metrics.get("metrics", {}).items():
            compact_metrics[m] = [{"d": p["day"], "v": round(p["value"], 3)} for p in series[-6:]]

        user_message = f"""Analyse the following product launch metrics data and produce your JSON output.

## Raw Metrics Time Series (Last 6 Days)
{json.dumps(compact_metrics, separators=(',', ':'))}

## Aggregated Summary (pre vs post launch averages + violations)
{json.dumps(aggregated, separators=(',', ':'))}

## Anomaly Detection Results (z-score analysis)
{json.dumps(anomalies, separators=(',', ':'))}

## Trend Comparison (pre vs post launch slopes + momentum)
{json.dumps(trends, separators=(',', ':'))}

Produce your analysis as a single valid JSON object."""

        result = self._call_api(SYSTEM_PROMPT, user_message)
        logger.info(f"[Data_Analyst] Data confidence: {result.get('data_confidence', 'unknown')}")
        logger.info(f"[Data_Analyst] Alarming metrics: {len(result.get('alarming_metrics', []))}")
        return result
