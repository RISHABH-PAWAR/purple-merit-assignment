"""
Tool 1: Metric Aggregator
Computes pre/post launch averages, percent changes, and threshold violations.
Pure computation — no LLM calls.
"""

from __future__ import annotations

from typing import Any


THRESHOLDS: dict[str, dict[str, Any]] = {
    "crash_rate":            {"direction": "above",        "limit": 0.010, "severity": "critical"},
    "api_latency_p95_ms":   {"direction": "above",        "limit": 500,   "severity": "critical"},
    "payment_success_rate": {"direction": "below",        "limit": 0.985,  "severity": "critical"},
    "support_ticket_volume":{"direction": "increase_pct", "limit": 0.50,  "severity": "high"},
    "activation_rate":      {"direction": "decrease_pct", "limit": 0.10,  "severity": "high"},
    "feature_funnel_completion": {"direction": "decrease_pct", "limit": 0.10, "severity": "high"},
    "churn_rate":           {"direction": "above",        "limit": 0.015,  "severity": "high"},
    "d1_retention":         {"direction": "decrease_pct", "limit": 0.10,  "severity": "medium"},
    "d7_retention":         {"direction": "decrease_pct", "limit": 0.10,  "severity": "medium"},
}


def aggregate_metrics(metrics_data: dict) -> dict:
    """
    Splits metrics into pre-launch (days 1–6) and post-launch (days 7–10).
    Computes mean for each window and percent change.
    Flags any metric that breaches its threshold.

    Returns:
        {
          "pre_launch_averages": {metric: avg},
          "post_launch_averages": {metric: avg},
          "changes": {metric: {"pre": x, "post": y, "change_pct": z, "change_abs": w}},
          "violations": [{"metric": ..., "severity": ..., "detail": ...}],
          "violation_count": int,
          "summary": "human-readable string"
        }
    """
    launch_day: int = metrics_data.get("launch_day", 7)
    raw: dict = metrics_data.get("metrics", {})

    pre: dict[str, float] = {}
    post: dict[str, float] = {}

    for metric, series in raw.items():
        pre_vals  = [p["value"] for p in series if p["day"] < launch_day]
        post_vals = [p["value"] for p in series if p["day"] >= launch_day]
        pre[metric]  = round(sum(pre_vals)  / len(pre_vals),  6) if pre_vals  else 0.0
        post[metric] = round(sum(post_vals) / len(post_vals), 6) if post_vals else 0.0

    changes: dict[str, dict] = {}
    for metric in raw:
        p, q = pre[metric], post[metric]
        change_pct = round((q - p) / p, 6) if p != 0 else 0.0
        changes[metric] = {
            "pre":        p,
            "post":       q,
            "change_pct": change_pct,
            "change_abs": round(q - p, 6),
        }

    violations: list[dict] = []
    for metric, rule in THRESHOLDS.items():
        if metric not in changes:
            continue
        c = changes[metric]
        breached = False
        detail = ""
        if rule["direction"] == "above":
            if c["post"] > rule["limit"]:
                breached = True
                detail = f"{metric} post-launch avg {c['post']:.4f} exceeds limit {rule['limit']:.4f}"
        elif rule["direction"] == "below":
            if c["post"] < rule["limit"]:
                breached = True
                detail = f"{metric} post-launch avg {c['post']:.4f} is below floor {rule['limit']:.4f}"
        elif rule["direction"] == "increase_pct":
            if c["change_pct"] > rule["limit"]:
                breached = True
                detail = f"{metric} increased {c['change_pct']*100:.1f}% (limit: {rule['limit']*100:.0f}%)"
        elif rule["direction"] == "decrease_pct":
            if c["change_pct"] < -rule["limit"]:
                breached = True
                detail = f"{metric} dropped {abs(c['change_pct'])*100:.1f}% (limit: {rule['limit']*100:.0f}%)"
        if breached:
            violations.append({
                "metric":   metric,
                "severity": rule["severity"],
                "detail":   detail,
                "pre":      c["pre"],
                "post":     c["post"],
                "change_pct_formatted": f"{c['change_pct']*100:+.1f}%",
            })

    # Sort by severity: critical first
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    violations.sort(key=lambda x: order.get(x["severity"], 4))

    summary_parts = []
    for v in violations:
        summary_parts.append(f"[{v['severity'].upper()}] {v['detail']}")
    summary = "; ".join(summary_parts) if summary_parts else "No threshold violations detected."

    return {
        "pre_launch_averages":  pre,
        "post_launch_averages": post,
        "changes":     changes,
        "violations":  violations,
        "violation_count": len(violations),
        "summary":     summary,
    }
