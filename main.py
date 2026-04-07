"""
War Room — Product Launch Decision System
Entry point. Sets up logging, runs the orchestrator, prints rich terminal output.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich import box
from rich.text import Text

load_dotenv()

# ── Validate API key early ─────────────────────────────────────────────────────
if not os.environ.get("GROQ_API_KEY"):
    print("ERROR: GROQ_API_KEY not set.")
    print("  1. Get a free key at https://console.groq.com")
    print("  2. Copy .env.example → .env and paste your key")
    sys.exit(1)

# ── Logging setup ──────────────────────────────────────────────────────────────
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/run_verbose.log", mode="w", encoding="utf-8"),
    ],
)
logger  = logging.getLogger("war_room")
console = Console()

from orchestrator import WarRoomOrchestrator  # noqa: E402 — import after logging setup


DECISION_COLORS = {
    "Proceed":   "green",
    "Pause":     "yellow",
    "Roll Back": "red",
}


# ── Terminal output helpers ────────────────────────────────────────────────────

def print_header() -> None:
    console.print()
    console.print(Panel.fit(
        "[bold purple]PurpleMerit Technologies[/bold purple]\n"
        "[bold white]War Room — Product Launch Decision System[/bold white]\n"
        f"[dim]Smart Checkout v2.1.0  ·  {datetime.now().strftime('%d %b %Y  %H:%M')}[/dim]",
        border_style="purple",
        padding=(1, 4),
    ))
    console.print()


def print_final_result(result: dict) -> None:
    decision   = result.get("decision", "Unknown")
    confidence = float(result.get("confidence_score", 0.0))
    color      = DECISION_COLORS.get(decision, "white")

    console.print(Rule(style="purple"))
    console.print()

    # ── Decision banner ────────────────────────────────────────────────────────
    hard_rule = result.get("hard_rule_triggered")
    banner_lines = [
        f"[bold {color}]★  FINAL DECISION: {decision.upper()}  ★[/bold {color}]",
        f"[dim]Confidence: {confidence:.0%}[/dim]",
    ]
    if hard_rule:
        banner_lines.append(f"\n[bold red]⚠ Hard rule triggered:[/bold red] [dim]{hard_rule}[/dim]")

    console.print(Panel.fit(
        "\n".join(banner_lines),
        border_style=color,
        padding=(1, 6),
    ))
    console.print()

    # ── Key drivers table ──────────────────────────────────────────────────────
    drivers = result.get("rationale", {}).get("key_drivers", [])
    if drivers:
        table = Table(title="Key Decision Drivers", box=box.ROUNDED, border_style="purple")
        table.add_column("#", style="dim", width=3)
        table.add_column("Driver", style="white")
        for i, d in enumerate(drivers, 1):
            table.add_row(str(i), d)
        console.print(table)
        console.print()

    # ── Risk register table ────────────────────────────────────────────────────
    risks = result.get("risk_register", [])
    if risks:
        risk_table = Table(title="Risk Register", box=box.ROUNDED, border_style="red")
        risk_table.add_column("Risk", style="white", max_width=46)
        risk_table.add_column("Likelihood", justify="center", width=12)
        risk_table.add_column("Impact",     justify="center", width=12)
        risk_table.add_column("Rating",     justify="center", width=10)
        severity_color = {"critical": "red", "high": "orange1", "medium": "yellow", "low": "green"}
        for r in risks:
            rating = r.get("rating", "low")
            rc     = severity_color.get(rating, "white")
            risk_table.add_row(
                r.get("risk", ""),
                r.get("likelihood", ""),
                r.get("impact", ""),
                f"[bold {rc}]{rating.upper()}[/bold {rc}]",
            )
        console.print(risk_table)
        console.print()

    # ── Action plan table ──────────────────────────────────────────────────────
    actions = result.get("action_plan", {}).get("actions", [])
    if actions:
        action_table = Table(title="Action Plan (24–48 h)", box=box.ROUNDED, border_style="green")
        action_table.add_column("Priority", justify="center", width=8)
        action_table.add_column("Action",   style="white", max_width=40)
        action_table.add_column("Owner",    width=20)
        action_table.add_column("Deadline", justify="center", width=10)
        prio_color = {"P0": "red", "P1": "orange1", "P2": "yellow"}
        for a in actions:
            p  = a.get("priority", "P2")
            pc = prio_color.get(p, "white")
            action_table.add_row(
                f"[bold {pc}]{p}[/bold {pc}]",
                a.get("action", ""),
                a.get("owner", ""),
                a.get("deadline", ""),
            )
        console.print(action_table)
        console.print()

    # ── Communication plan ─────────────────────────────────────────────────────
    comms = result.get("communication_plan", {})
    if comms:
        console.print("[bold yellow]Communication Plan[/bold yellow]")
        if comms.get("timing"):
            console.print(f"  [dim]Timing:[/dim]  {comms['timing']}")
        if comms.get("internal"):
            internal = comms.get('internal', '')
            console.print(f"  [dim]Internal:[/dim] {internal[:120]}{'...' if len(internal) > 120 else ''}")
        if comms.get("external"):
            external = comms.get('external', '')
            console.print(f"  [dim]External:[/dim] {external[:120]}{'...' if len(external) > 120 else ''}")
        console.print()

    # ── Confidence boosters ────────────────────────────────────────────────────
    boosters = result.get("confidence_boosters", [])
    if boosters:
        console.print("[bold yellow]What would increase confidence:[/bold yellow]")
        for b in boosters:
            console.print(f"  [dim]→[/dim] {b}")
        console.print()

    console.print(f"[dim]📄  Full output → [underline]outputs/war_room_decision.json[/underline][/dim]")
    console.print(f"[dim]📋  Trace log   → [underline]logs/run_trace.log[/underline][/dim]")
    console.print(f"[dim]📝  Verbose log  → [underline]logs/run_verbose.log[/underline][/dim]")
    console.print()


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    print_header()

    orchestrator = WarRoomOrchestrator(
        metrics_path       = "data/metrics.json",
        feedback_path      = "data/user_feedback.json",
        release_notes_path = "data/release_notes.md",
        output_path        = "outputs/war_room_decision.json",
        log_path           = "logs/run_trace.log",
    )

    try:
        result = orchestrator.run()
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user.[/red]")
        sys.exit(1)
    except Exception as exc:
        logger.exception(f"Fatal error: {exc}")
        console.print(f"\n[bold red]Fatal error:[/bold red] {exc}")
        sys.exit(1)

    print_final_result(result)


if __name__ == "__main__":
    main()
