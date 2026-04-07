"""
Tool 4: Trend Comparator
Fits linear regression on pre-launch data and compares to post-launch trajectory.
Computes per-metric trend direction and momentum.
Pure computation — no LLM calls.
"""

from __future__ import annotations

import math


def _linear_regression(x: list[float], y: list[float]) -> tuple[float, float]:
    """Returns (slope, intercept) via ordinary least squares."""
    n = len(x)
    if n < 2:
        return 0.0, y[0] if y else 0.0
    sum_x  = sum(x)
    sum_y  = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)
    denom  = n * sum_x2 - sum_x ** 2
    if denom == 0:
        return 0.0, sum_y / n
    slope     = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return round(slope, 8), round(intercept, 6)


# Metrics where higher value is worse
_HIGHER_IS_WORSE = {"crash_rate", "api_latency_p95_ms", "support_ticket_volume", "churn_rate"}


def _is_bad_direction_positive_for(metric: str) -> bool:
    return metric in _HIGHER_IS_WORSE


def compare_trends(metrics_data: dict) -> dict:
    """
    For each metric:
    - Fits linear regression on pre-launch and post-launch data separately
    - Computes slope direction (improving / stable / degrading) pre vs post
    - Computes day-over-day momentum from the last 3 post-launch days
    - Computes jump magnitude at launch boundary

    Returns per-metric trend objects plus an overall health summary.
    """
    launch_day: int = metrics_data.get("launch_day", 7)
    raw: dict = metrics_data.get("metrics", {})

    results: dict[str, dict] = {}
    degrading_metrics: list[str] = []

    for metric, series in raw.items():
        pre_series  = [p for p in series if p["day"] < launch_day]
        post_series = [p for p in series if p["day"] >= launch_day]

        if not pre_series or not post_series:
            continue

        pre_x  = [float(p["day"])   for p in pre_series]
        pre_y  = [float(p["value"]) for p in pre_series]
        post_x = [float(p["day"])   for p in post_series]
        post_y = [float(p["value"]) for p in post_series]

        pre_slope,  pre_intercept  = _linear_regression(pre_x,  pre_y)
        post_slope, post_intercept = _linear_regression(post_x, post_y)

        higher_is_worse = _is_bad_direction_positive_for(metric)

        # Determine if post-launch slope is in a "bad" direction compared to pre-launch
        if higher_is_worse:
            trend_direction = (
                "degrading"  if post_slope > pre_slope + 0.0001 else
                "improving"  if post_slope < pre_slope - 0.0001 else
                "stable"
            )
        else:
            trend_direction = (
                "degrading"  if post_slope < pre_slope - 0.0001 else
                "improving"  if post_slope > pre_slope + 0.0001 else
                "stable"
            )

        # Momentum: day-over-day change direction in post-launch window
        recent_diffs = [post_y[i + 1] - post_y[i] for i in range(len(post_y) - 1)]
        avg_recent   = sum(recent_diffs) / len(recent_diffs) if recent_diffs else 0.0

        if higher_is_worse:
            momentum = (
                "worsening" if avg_recent > 0.001  else
                "recovering" if avg_recent < -0.001 else
                "flat"
            )
        else:
            momentum = (
                "recovering" if avg_recent > 0.001  else
                "worsening"  if avg_recent < -0.001 else
                "flat"
            )

        # Magnitude of post-launch deviation vs last pre-launch value
        last_pre   = pre_y[-1]
        first_post = post_y[0]
        jump_pct   = round((first_post - last_pre) / last_pre * 100, 2) if last_pre != 0 else 0.0

        results[metric] = {
            "pre_slope":       pre_slope,
            "post_slope":      post_slope,
            "trend_direction": trend_direction,
            "momentum":        momentum,
            "launch_jump_pct": jump_pct,
            "higher_is_worse": higher_is_worse,
        }

        if trend_direction == "degrading":
            degrading_metrics.append(metric)

    overall_health = (
        "critical" if len(degrading_metrics) >= 5 else
        "poor"     if len(degrading_metrics) >= 3 else
        "warning"  if len(degrading_metrics) >= 1 else
        "healthy"
    )

    return {
        "metric_trends":     results,
        "degrading_metrics": degrading_metrics,
        "degrading_count":   len(degrading_metrics),
        "overall_health":    overall_health,
        "summary": f"{len(degrading_metrics)} metrics degrading post-launch. Overall: {overall_health}.",
    }
