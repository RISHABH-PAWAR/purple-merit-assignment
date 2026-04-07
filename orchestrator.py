"""
War Room Orchestrator
Controls the sequential agent workflow. Loads data, runs tools, runs agents in order,
writes final JSON output and structured trace log.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools import aggregate_metrics, detect_anomalies, analyze_sentiment, compare_trends
from agents import PMAgent, DataAnalystAgent, MarketingAgent, RiskAgent, DecisionAgent

logger = logging.getLogger("war_room")


class WarRoomOrchestrator:
    """
    Runs the complete war-room pipeline in two phases:

    Phase 1 — Pure-Python tools (no LLM):
        metric_aggregator → anomaly_detector → sentiment_analyzer → trend_comparator

    Phase 2 — LLM agents (sequential, each builds on prior outputs):
        PM Agent → Data Analyst → Marketing/Comms → Risk/Critic → Decision Agent

    Writes:
        outputs/war_room_decision.json  — final structured decision
        logs/run_trace.log              — timestamped trace of every step
    """

    def __init__(
        self,
        metrics_path: str,
        feedback_path: str,
        release_notes_path: str,
        output_path: str,
        log_path: str,
    ) -> None:
        self.metrics_path       = metrics_path
        self.feedback_path      = feedback_path
        self.release_notes_path = release_notes_path
        self.output_path        = output_path
        self.log_path           = log_path
        self.trace: list[dict]  = []

        # Ensure output directories exist
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────── data loading ────────────────────────────

    def _load_data(self) -> tuple[dict, list[dict], str]:
        with open(self.metrics_path, encoding="utf-8") as f:
            metrics_data = json.load(f)
        with open(self.feedback_path, encoding="utf-8") as f:
            feedback_data = json.load(f)
        with open(self.release_notes_path, encoding="utf-8") as f:
            release_notes = f.read()
        return metrics_data, feedback_data["entries"], release_notes

    # ──────────────────────────── trace helpers ───────────────────────────

    def _log_step(self, step_type: str, name: str, output: Any, elapsed: float) -> None:
        entry = {
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "step_type":      step_type,
            "name":           name,
            "elapsed_s":      round(elapsed, 2),
            "output_summary": _summarize(output),
        }
        self.trace.append(entry)
        logger.info(f"  ✓ {step_type}: {name} completed in {elapsed:.2f}s")

    def _write_trace(self) -> None:
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"  WAR ROOM RUN TRACE — {datetime.now(timezone.utc).isoformat()}\n")
            f.write("=" * 70 + "\n\n")
            for step in self.trace:
                f.write(f"[{step['timestamp']}] {step['step_type']}: {step['name']}\n")
                f.write(f"  elapsed:  {step['elapsed_s']}s\n")
                f.write(f"  summary:  {step['output_summary']}\n\n")

    # ──────────────────────────── main pipeline ───────────────────────────

    def run(self) -> dict[str, Any]:
        logger.info("=" * 60)
        logger.info("  WAR ROOM — starting pipeline")
        logger.info("=" * 60)
        logger.info("Loading data files...")

        metrics_data, feedback_entries, release_notes = self._load_data()
        logger.info(
            f"  Loaded: {len(metrics_data['metrics'])} metric streams, "
            f"{len(feedback_entries)} feedback entries, release notes"
        )

        # ── Phase 1: Pure-Python analytical tools ────────────────────────
        logger.info("\n── Phase 1: Running analytical tools (no LLM) ──")

        t = time.time()
        aggregated = aggregate_metrics(metrics_data)
        self._log_step("TOOL", "metric_aggregator", aggregated, time.time() - t)

        t = time.time()
        anomalies = detect_anomalies(metrics_data)
        self._log_step("TOOL", "anomaly_detector", anomalies, time.time() - t)

        t = time.time()
        sentiment = analyze_sentiment(feedback_entries)
        self._log_step("TOOL", "sentiment_analyzer", sentiment, time.time() - t)

        t = time.time()
        trends = compare_trends(metrics_data)
        self._log_step("TOOL", "trend_comparator", trends, time.time() - t)

        logger.info(
            f"\n  Tool summary: {aggregated['violation_count']} threshold violations, "
            f"{anomalies['anomaly_count']} anomalies, "
            f"sentiment={sentiment['sentiment_label']} ({sentiment['sentiment_score']:+.2f}), "
            f"health={trends['overall_health']}"
        )

        # ── Phase 2: LLM agents (sequential deliberation) ────────────────
        logger.info("\n── Phase 2: Running agent analyses (LLM) ──")

        # Sample feedback to stay within token limits while providing context
        # We take top 5 negative, top 5 positive, and 2 neutral for balanced context
        neg_samples = [f["text"] for f in feedback_entries if f["sentiment"] == "negative"][:5]
        pos_samples = [f["text"] for f in feedback_entries if f["sentiment"] == "positive"][:5]
        neu_samples = [f["text"] for f in feedback_entries if f["sentiment"] == "neutral"][:2]
        sample_feedback = {
            "representative_negative": neg_samples,
            "representative_positive": pos_samples,
            "representative_neutral":  neu_samples,
            "note": f"Samples from a total of {len(feedback_entries)} entries."
        }

        t = time.time()
        pm_output = PMAgent().run(release_notes, aggregated, sentiment, sample_feedback)
        self._log_step("AGENT", "PM_Agent", pm_output, time.time() - t)

        t = time.time()
        analyst_output = DataAnalystAgent().run(metrics_data, aggregated, anomalies, trends)
        self._log_step("AGENT", "Data_Analyst", analyst_output, time.time() - t)

        t = time.time()
        marketing_output = MarketingAgent().run(sentiment, pm_output, release_notes, sample_feedback)
        self._log_step("AGENT", "Marketing_Comms", marketing_output, time.time() - t)

        t = time.time()
        risk_output = RiskAgent().run(pm_output, analyst_output, marketing_output, anomalies, aggregated)
        self._log_step("AGENT", "Risk_Critic", risk_output, time.time() - t)

        t = time.time()
        final = DecisionAgent().run(
            pm_output, analyst_output, marketing_output,
            risk_output, aggregated, sentiment,
        )
        self._log_step("AGENT", "Decision_Agent", final, time.time() - t)

        # ── Phase 3: Write outputs ────────────────────────────────────────
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        logger.info(f"\n📄  Decision written → {self.output_path}")

        self._write_trace()
        logger.info(f"📋  Trace log written → {self.log_path}")
        logger.info("=" * 60)

        return final


# ─────────────────────────── trace summarizer ────────────────────────────────

def _summarize(obj: Any) -> str:
    """Produce a short human-readable summary of a tool or agent output for trace logging."""
    if not isinstance(obj, dict):
        return str(obj)[:120]

    if "decision" in obj:
        conf = obj.get('confidence_score', '?')
        conf_str = f"{float(conf):.0%}" if conf != '?' else '?'
        return f"DECISION={obj['decision']} confidence={conf_str}"
    if "violation_count" in obj:
        return f"violations={obj['violation_count']} | {obj.get('summary', '')[:80]}"
    if "anomaly_count" in obj:
        return f"anomalies={obj['anomaly_count']} | {obj.get('summary', '')[:80]}"
    if "sentiment_score" in obj:
        return (
            f"sentiment={obj['sentiment_score']:+.2f} ({obj.get('sentiment_label','?')}) "
            f"neg={obj.get('negative','?')} pos={obj.get('positive','?')}"
        )
    if "degrading_count" in obj:
        return f"degrading={obj['degrading_count']} health={obj.get('overall_health','?')}"
    if "preliminary_recommendation" in obj:
        return f"rec={obj['preliminary_recommendation']} | {obj.get('reasoning','')[:80]}"
    if "reputational_risk_level" in obj:
        return f"rep_risk={obj['reputational_risk_level']} urgency={obj.get('communication_urgency','?')}"
    if "risk_register" in obj:
        critical = sum(1 for r in obj.get("risk_register", []) if r.get("rating") == "critical")
        return f"risks={len(obj.get('risk_register',[]))} critical={critical}"

    return str(obj)[:120]
