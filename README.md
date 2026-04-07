# War Room — Product Launch Decision System

> **PurpleMerit Technologies · AI/ML Engineer Assessment 1**
>
> A production-grade multi-agent CLI that simulates a cross-functional **war room**
> during a product launch. Five AI agents — powered by **Groq's free tier LLMs** —
> analyse a realistic mock dashboard (metrics + user feedback) and produce a structured
> **Proceed / Pause / Roll Back** decision with full rationale, risk register, action
> plan, and communication guidance.

---

## Architecture

```
data/
  metrics.json          ← 10-day time-series for 9 metrics
  user_feedback.json    ← 30 user feedback entries (mixed sentiment)
  release_notes.md      ← feature changelog + known risks
         │
         ▼
┌─────────────────────────────────────────────────┐
│        Phase 1 — Analytical Tools (pure Python) │
│  metric_aggregator → anomaly_detector           │
│  sentiment_analyzer → trend_comparator          │
└─────────────────────────────────────────────────┘
         │ grounded numerical context
         ▼
┌─────────────────────────────────────────────────┐
│        Phase 2 — LLM Agents (Groq / Llama 3.3) │
│  PM Agent → Data Analyst → Marketing/Comms      │
│         → Risk/Critic → Decision Agent          │
└─────────────────────────────────────────────────┘
         │
         ▼
  outputs/war_room_decision.json   ← final structured JSON
  logs/run_trace.log               ← full pipeline trace
```

Each agent receives the outputs of all prior agents as explicit context — creating
genuine deliberation, not just 5 isolated LLM calls.

---

## Agent Roles

| Agent | Responsibility |
|---|---|
| **PM Agent** | Evaluates success criteria pass/fail, estimates user impact, gives preliminary go/no-go |
| **Data Analyst** | Identifies statistically significant anomalies (z-scores), correlations, data confidence |
| **Marketing/Comms** | Assesses reputational risk, drafts internal Slack + external status page messages |
| **Risk/Critic** | Challenges assumptions from all agents, builds 5-item risk register, worst-case scenarios |
| **Decision Agent** | Synthesises all inputs, applies hard programmatic rules, produces final JSON decision |

---

## Tools (pure computation — no LLM)

| Tool | What it computes |
|---|---|
| `metric_aggregator` | Pre/post launch averages, % changes, threshold violations per metric |
| `anomaly_detector` | Z-score analysis per metric per day — flags statistically significant deviations |
| `sentiment_analyzer` | Sentiment distribution, keyword theme extraction, net sentiment score |
| `trend_comparator` | Linear regression on pre vs post launch slopes, momentum direction |

Tools are called programmatically by the orchestrator and their outputs are injected
as structured context into each agent's prompt — giving the LLM grounded numbers
rather than letting it hallucinate statistics.

---

## Setup

### Requirements

- Python 3.10 or higher
- A **free** Groq API key — no credit card required

### 1 · Clone and install

```bash
git clone <repo_url>
cd war-room
pip install -r requirements.txt
```

### 2 · Get your free Groq API key

1. Go to **https://console.groq.com**
2. Sign up (free, no credit card)
3. Navigate to **API Keys → Create API Key**
4. Copy the key

### 3 · Configure environment

```bash
cp .env.example .env
# Open .env in your editor and replace 'your_groq_api_key_here' with your real key
```

Your `.env` should look like:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Run

```bash
python main.py
```

The system will:
1. Print a live progress log to the terminal as each tool and agent completes
2. Display a rich formatted summary table in the terminal
3. Write the full structured JSON decision to `outputs/war_room_decision.json`
4. Write the complete pipeline trace to `logs/run_trace.log`

**Typical run time:** 30–90 seconds (5 LLM calls via Groq, sequential)

---

## Output Files

### `outputs/war_room_decision.json`

The complete structured decision containing:

```json
{
  "decision": "Roll Back",
  "hard_rule_triggered": "payment_success_rate=0.975 < 0.970 threshold",
  "rationale": {
    "key_drivers": [...],
    "metric_references": {...},
    "feedback_summary": "...",
    "agent_consensus": "..."
  },
  "risk_register": [
    {
      "risk": "...",
      "likelihood": "high",
      "impact": "critical",
      "rating": "critical",
      "mitigation": "..."
    }
  ],
  "action_plan": {
    "window": "24-48 hours",
    "actions": [
      {"action": "...", "owner": "...", "deadline": "2h", "priority": "P0"}
    ]
  },
  "communication_plan": {
    "internal": "...",
    "external": "...",
    "timing": "..."
  },
  "confidence_score": 0.82,
  "confidence_boosters": ["..."]
}
```

### `logs/run_trace.log`

A chronological trace of every tool call and agent step with:
- ISO timestamp
- Step type (TOOL / AGENT)
- Name
- Elapsed time in seconds
- One-line output summary

---

## Decision Hard Rules

The Decision Agent applies these rules programmatically in Python **before** sending to the LLM.
They cannot be reasoned away:

| Rule | Threshold | Consequence |
|---|---|---|
| `payment_success_rate` post-launch avg | < 0.970 | **Roll Back** |
| `crash_rate` post-launch avg | > 0.020 | **Roll Back** |
| Any `critical` risk in register | unmitigated | Minimum **Pause** |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | Free Groq API key — get one at [console.groq.com](https://console.groq.com) |

---

## Model

This project uses **`llama-3.3-70b-versatile`** via Groq's free tier.
To switch models, change `MODEL` in `agents/base_agent.py`.

Other free Groq models:
- `llama-3.1-8b-instant` — faster, lower quality
- `mixtral-8x7b-32768` — good balance
- `gemma2-9b-it` — lightweight

---

## Where to Find Traces

`logs/run_trace.log` is written after every run. Each entry has:

```
[2026-04-07T14:23:01Z] TOOL: metric_aggregator
  elapsed:  0.01s
  summary:  violations=6 | [CRITICAL] crash_rate post-launch avg ...

[2026-04-07T14:23:45Z] AGENT: Decision_Agent
  elapsed:  12.4s
  summary:  DECISION=Roll Back confidence=0.82
```

---

## Design Decisions

**Why sequential agents (not parallel)?**
Each agent builds explicitly on prior outputs. The Risk Agent reads the PM Agent's
assumptions and challenges them by name. Parallelism would lose that deliberation quality.

**Why pure-Python tools?**
Tools compute real statistics — z-scores, linear regression, keyword frequency.
They give the LLM agents grounded numerical context, preventing hallucinated statistics.

**Why Groq free tier?**
Groq's free tier provides genuinely fast inference (up to 500 tokens/sec) on
production-grade open-source models — making this system runnable by any engineer
with zero infrastructure cost.

**Why `tenacity` retry?**
Groq's free tier has rate limits. Three retries with exponential backoff ensure the
pipeline completes reliably without manual intervention.
