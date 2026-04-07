"""
Tool 3: Sentiment Analyzer
Counts sentiment buckets, extracts top issues by keyword frequency,
computes a net sentiment score.
Pure computation — no LLM calls.
"""

from __future__ import annotations

from collections import Counter


ISSUE_KEYWORDS: dict[str, list[str]] = {
    "crash":            ["crash", "crashes", "crashed", "crashing", "startup"],
    "payment_failure":  ["payment", "charged", "charge", "transaction", "checkout", "failed", "failure", "amex", "international"],
    "slow_performance": ["slow", "loading", "takes forever", "latency", "504", "spins"],
    "login_issues":     ["login", "log in", "can't login", "cannot login", "sign in"],
    "ux_confusion":     ["confusing", "where did", "can't find", "settings", "step 3", "unusable"],
    "rollback_demand":  ["rollback", "roll back", "old version", "revert"],
    "double_charge":    ["charged twice", "double", "duplicate"],
    "android_issue":    ["android"],
}


def analyze_sentiment(feedback_entries: list[dict]) -> dict:
    """
    Counts sentiment distribution, extracts top recurring issue themes,
    and computes a sentiment score = (positive - negative) / total.

    Returns structured sentiment analysis dict.
    """
    counts: Counter = Counter()
    issue_hits: Counter = Counter()
    critical_mentions: list[str] = []

    for entry in feedback_entries:
        sentiment = entry.get("sentiment", "neutral")
        counts[sentiment] += 1

        text = entry.get("text", "").lower()

        for issue, keywords in ISSUE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                issue_hits[issue] += 1

        # Flag messages that are explicitly dangerous to brand
        if any(w in text for w in ["charged twice", "double charge", "refund", "rollback", "unusable", "unacceptable"]):
            critical_mentions.append(entry.get("text", ""))

    total    = len(feedback_entries)
    positive = counts.get("positive", 0)
    negative = counts.get("negative", 0)
    neutral  = counts.get("neutral", 0)
    outliers = counts.get("outlier", 0)

    sentiment_score = round((positive - negative) / total, 4) if total > 0 else 0.0

    top_issues = [
        {"issue": issue, "mention_count": count}
        for issue, count in issue_hits.most_common(6)
    ]

    return {
        "total":           total,
        "positive":        positive,
        "negative":        negative,
        "neutral":         neutral,
        "outliers":        outliers,
        "sentiment_score": sentiment_score,
        "sentiment_label": (
            "strongly_negative" if sentiment_score <= -0.30 else
            "negative"          if sentiment_score < -0.10 else
            "neutral"           if sentiment_score < 0.10  else
            "positive"
        ),
        "negative_pct":           round(negative / total * 100, 1) if total > 0 else 0,
        "top_issues":             top_issues,
        "critical_mentions":      critical_mentions,
        "critical_mention_count": len(critical_mentions),
    }
