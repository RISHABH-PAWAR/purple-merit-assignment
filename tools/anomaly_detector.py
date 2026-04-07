"""
Tool 2: Anomaly Detector
Uses z-score against pre-launch baseline to flag statistically significant deviations.
Pure computation — no LLM calls.
"""

from __future__ import annotations

import math
from typing import Any


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def detect_anomalies(metrics_data: dict, z_threshold: float = 2.0) -> dict:
    """
    For each metric, computes baseline stats from pre-launch days (1 to launch_day-1).
    Then checks every post-launch day against baseline mean ± z_threshold * std.

    Returns:
        {
          "anomalies": [{"metric":..., "day":..., "value":..., "z_score":..., "severity":...}],
          "anomaly_count": int,
          "most_severe": {...},
          "z_threshold_used": float,
          "summary": "..."
        }
    """
    launch_day: int = metrics_data.get("launch_day", 7)
    raw: dict = metrics_data.get("metrics", {})

    def severity(z: float) -> str:
        az = abs(z)
        if az >= 4.0:
            return "critical"
        if az >= 3.0:
            return "high"
        if az >= 2.0:
            return "medium"
        return "low"

    anomalies: list[dict] = []

    for metric, series in raw.items():
        pre_vals  = [p["value"] for p in series if p["day"] < launch_day]
        post_days = [p for p in series if p["day"] >= launch_day]

        if not pre_vals or len(pre_vals) < 2:
            continue

        mu  = _mean(pre_vals)
        sig = _std(pre_vals, mu)

        if sig == 0:
            continue  # No variance in baseline — skip

        for point in post_days:
            val     = point["value"]
            z       = (val - mu) / sig
            if abs(z) >= z_threshold:
                z_capped = max(-10.0, min(10.0, z))
                anomalies.append({
                    "metric":        metric,
                    "day":           point["day"],
                    "value":         round(val, 6),
                    "baseline_mean": round(mu, 6),
                    "baseline_std":  round(sig, 6),
                    "z_score":       round(z_capped, 3),
                    "z_score_raw":   round(z, 3),
                    "z_capped":      z_capped != z,
                    "severity":      severity(z),
                    "direction":     "spike" if z > 0 else "drop",
                })

    # Sort by absolute z-score descending
    anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)

    most_severe = anomalies[0] if anomalies else None
    summary_lines = [
        f"{a['metric']} day {a['day']}: z={a['z_score']:.2f} ({a['severity']})"
        for a in anomalies[:5]
    ]
    summary = (
        f"{len(anomalies)} anomalies detected. Top: " + "; ".join(summary_lines)
        if anomalies else "No anomalies detected."
    )

    return {
        "anomalies":        anomalies,
        "anomaly_count":    len(anomalies),
        "most_severe":      most_severe,
        "z_threshold_used": z_threshold,
        "summary":          summary,
    }
