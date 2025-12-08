#!/usr/bin/env python3

"""
Unit test for queue membership guardrails in determine_pr_dashboards.

Run via: `python -m queueboard.test_compute_dashboard_prs`
"""

from __future__ import annotations

from datetime import datetime, timezone

from queueboard.ci_status import CIStatus
from queueboard.classify_pr_state import PRStatus
from queueboard.compute_dashboard_prs import AggregatePRInfo, BasicPRInformation, DataStatus, Label, determine_pr_dashboards
from queueboard.mathlib_dashboards import Dashboard


def _basic_pr(num: int, labels: list[Label] | None = None) -> BasicPRInformation:
    return BasicPRInformation(
        num, "alice", f"PR {num}", f"https://example.com/pr/{num}", labels or [], datetime.now(timezone.utc)
    )


def _aggregate_with_label(num: int, label_name: str) -> AggregatePRInfo:
    return AggregatePRInfo(
        False,
        CIStatus.Pass,
        "master",
        "branch",
        "repo",
        "open",
        datetime.now(timezone.utc),
        "alice",
        f"PR {num}",
        "desc",
        [],
        [Label(label_name, "000000", "https://example.com/label")],
        0,
        0,
        [],
        0,
        [],
        [],
        (DataStatus.Valid, []),
        0,
        None,
        None,
        None,
    )


def main() -> None:
    # Simulate a PR whose open-PR listing lacked a forbidden label, but aggregate data includes it.
    pr = _basic_pr(1)
    aggregate_info = {1: _aggregate_with_label(1, "merge-conflict")}
    nondraft_prs = [pr]
    base_branch = {1: "master"}
    ci_status = {1: CIStatus.Pass}

    dashboards = determine_pr_dashboards([pr], nondraft_prs, base_branch, ci_status, aggregate_info, True)

    assert pr not in dashboards[Dashboard.Queue], "PR with forbidden label must be excluded from Queue"
    # merge-conflict PRs should still be routed to NeedsMerge when excluded from the queue
    needs_merge_numbers = {p.number for p in dashboards[Dashboard.NeedsMerge]}
    assert pr.number in needs_merge_numbers

    # Sanity: pr_status matches awaiting review (ready) despite exclusion from queue due to label
    status = (
        PRStatus.tryFrom_str(aggregate_info[1].last_status_change.current_status.value)
        if aggregate_info[1].last_status_change
        else None
    )
    _ = status  # no strict assertion; guardrail concerns queue membership only


if __name__ == "__main__":
    main()
