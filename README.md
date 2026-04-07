# War Room — Product Launch Decision System

> **PurpleMerit Technologies · AI/ML Engineer Assessment**
>
> A two-phase product launch war room pipeline built in Python. The project combines
> pure computation tools with sequential Groq-powered LLM agents to generate a
> structured launch decision, risk register, action plan, and communication guidance.

---

## What this project does

This repo simulates a cross-functional war room for a product launch.
It processes launch metrics, user feedback, and release notes, then runs:

1. A pure-Python analytical toolchain for objective metric health signals
2. A sequential LLM agent workflow for contextual reasoning and decision making

The final output is a machine-readable decision JSON and a full pipeline trace.

---

## Core architecture

```
data/
  metrics.json          ← launch performance timeseries
  user_feedback.json    ← customer sentiment and feedback samples
  release_notes.md      ← feature summary and known risks
         │
         ▼
tools/                ← deterministic analysis (no LLM)
  metric_aggregator.py
  anomaly_detector.py
  sentiment_analyzer.py
  trend_comparator.py
         │
         ▼
agents/               ← sequential LLM reasoning
  PMAgent
  DataAnalystAgent
  MarketingAgent
  RiskAgent
  DecisionAgent
         │
         ▼
outputs/war_room_decision.json  ← final recommendation
logs/run_trace.log              ← full pipeline trace
```

The pipeline is orchestrated by `orchestrator.py`, while `main.py` sets up logging,
validates the Groq API key, and renders the final decision summary in the terminal.

---

## Updated project highlights

- Added `agents/__init__.py` and `tools/__init__.py` for clean package exports.
- Refined agent coordination and orchestrator handoff logic for stronger sequential reasoning.
- Updated `data/metrics.json` and `data/user_feedback.json` to reflect a realistic launch scenario.
- Improved output visibility with both rich terminal reporting and persistent JSON/log exports.

---

## Agent roles

| Agent | Responsibility |
|---|---|
| `PMAgent` | Reviews launch status, feature readiness, and preliminary go/no-go reasoning |
| `DataAnalystAgent` | Validates anomalies, metric confidence, and statistical context |
| `MarketingAgent` | Assesses reputation risk, sentiment signals, and communication posture |
| `RiskAgent` | Builds a risk register, tests assumptions, and identifies escalation triggers |
| `DecisionAgent` | Produces the final decision and applies hard programmatic rules |

---

## Tools (pure computation)

| Tool | Purpose |
|---|---|
| `aggregate_metrics` | Computes baseline vs launch comparisons, threshold violations, and summary statistics |
| `detect_anomalies` | Flags post-launch metric deviations using z-score analysis against baseline |
| `analyze_sentiment` | Summarizes user feedback and selects representative sentiment samples |
| `compare_trends` | Compares pre/post launch trend direction and overall metric health |

These tools provide grounded signal to the LLM agents instead of leaving the model to infer raw metrics.

---

## Getting started

### Requirements

- Python 3.10+
- A free Groq API key from https://console.groq.com

### Install

```bash
git clone <repo_url>
cd war-room
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
```

Then open `.env` and set:

```bash
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Run the system

```bash
python main.py
```

What happens:

- `main.py` validates `GROQ_API_KEY`
- `orchestrator.py` loads metrics, feedback, and release notes
- Tools run first to produce deterministic analysis outputs
- Agents run in sequence to generate the final decision
- Results are written to `outputs/war_room_decision.json`
- The pipeline trace is written to `logs/run_trace.log`

---

## Outputs

### `outputs/war_room_decision.json`

Contains the final structured recommendation, including:

- `decision` (`Proceed` / `Pause` / `Roll Back`)
- `hard_rule_triggered`
- `rationale` with key drivers
- `risk_register`
- `action_plan`
- `communication_plan`
- `confidence_score`
- `confidence_boosters`

### `logs/run_trace.log`

Contains a chronological log of every tool and agent step with:

- ISO timestamp
- Step type (`TOOL` / `AGENT`)
- Component name
- Elapsed time in seconds
- Summary of each output

---

## Project structure

```text
main.py
orchestrator.py
agents/
  __init__.py
  base_agent.py
  pm_agent.py
  data_analyst_agent.py
  marketing_agent.py
  risk_agent.py
  decision_agent.py
tools/
  __init__.py
  metric_aggregator.py
  anomaly_detector.py
  sentiment_analyzer.py
  trend_comparator.py
data/
  metrics.json
  user_feedback.json
  release_notes.md
outputs/
  war_room_decision.json
logs/
  run_trace.log
  run_verbose.log
```

---

## Notes

- `agents/base_agent.py` uses the Groq SDK with retry logic and JSON response parsing.
- The Groq model is configured as `llama-3.1-8b-instant`.
- `orchestrator.py` prioritizes representative sentiment samples to keep prompts concise.
- The system is designed for reproducible evaluation and transparent decision auditability.

---

## Environment

Required environment variable:

```bash
GROQ_API_KEY=<your_key>
```

For any missing key, `main.py` exits immediately with a prompt to configure `.env`.
