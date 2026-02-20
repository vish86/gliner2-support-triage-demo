"""
Triage tests: correctness (routing accuracy), stability (determinism), latency.
Results are stored in METRICS_RESULTS for the metrics report script.
Run: pytest python/tests/test_triage.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.payloads import build_analyze_payload

# Shared results for metrics report (filled by tests, written in conftest pytest_sessionfinish)
METRICS_RESULTS = {
    "correctness": {},  # threshold -> { total, correct_next_queue, correct_priority, correct_both }
    "stability": {},    # { passed: bool, runs_per_ticket: int, tickets_checked: int }
    "latency": [],      # list of timings_ms dicts per run
    "thresholds": [],
}

# Thresholds to test (multiple entity thresholds)
THRESHOLDS = [0.5, 0.6, 0.7, 0.75]
STABILITY_RUNS = 10
STABILITY_TICKET_INDEXES = [0, 5, 10, 20, 30]  # subset of golden tickets for stability


# client and golden_tickets fixtures come from conftest.py (conftest loads model before client)

def test_correctness_per_threshold(client, golden_tickets):
    """Routing accuracy: for each threshold, run all golden tickets and compare next_queue + priority."""
    METRICS_RESULTS["thresholds"] = THRESHOLDS
    for threshold in THRESHOLDS:
        correct_next = 0
        correct_priority = 0
        correct_both = 0
        total = len(golden_tickets)
        for item in golden_tickets:
            payload = build_analyze_payload(
                item["preset"], item["text"], threshold
            )
            resp = client.post("/analyze", json=payload)
            assert resp.status_code == 200, resp.text
            data = resp.json()
            expected = item["expected_routing"]
            got = data.get("routing") or {}
            if got.get("next_queue") == expected.get("next_queue"):
                correct_next += 1
            if got.get("priority") == expected.get("priority"):
                correct_priority += 1
            if (
                got.get("next_queue") == expected.get("next_queue")
                and got.get("priority") == expected.get("priority")
            ):
                correct_both += 1
        METRICS_RESULTS["correctness"][str(threshold)] = {
            "total": total,
            "correct_next_queue": correct_next,
            "correct_priority": correct_priority,
            "correct_both": correct_both,
            "accuracy_next_queue_pct": round(100 * correct_next / total, 1),
            "accuracy_priority_pct": round(100 * correct_priority / total, 1),
            "accuracy_both_pct": round(100 * correct_both / total, 1),
        }


def test_stability(client, golden_tickets):
    """Same ticket run N times yields identical routing (determinism)."""
    threshold = 0.6
    all_identical = True
    for idx in STABILITY_TICKET_INDEXES:
        if idx >= len(golden_tickets):
            continue
        item = golden_tickets[idx]
        payload = build_analyze_payload(item["preset"], item["text"], threshold)
        routings = []
        for _ in range(STABILITY_RUNS):
            resp = client.post("/analyze", json=payload)
            assert resp.status_code == 200
            routings.append(resp.json().get("routing"))
        if len(set(json.dumps(r, sort_keys=True) for r in routings)) != 1:
            all_identical = False
    METRICS_RESULTS["stability"] = {
        "passed": all_identical,
        "runs_per_ticket": STABILITY_RUNS,
        "tickets_checked": len(STABILITY_TICKET_INDEXES),
        "output_stability_pct": 100.0 if all_identical else 0.0,
    }


def test_latency(client, golden_tickets):
    """Collect triage latencies (timings_ms) for all tickets at threshold 0.6."""
    METRICS_RESULTS["latency"] = []
    threshold = 0.6
    for item in golden_tickets:
        payload = build_analyze_payload(item["preset"], item["text"], threshold)
        resp = client.post("/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        METRICS_RESULTS["latency"].append(data.get("timings_ms") or {})
    assert len(METRICS_RESULTS["latency"]) == len(golden_tickets)
