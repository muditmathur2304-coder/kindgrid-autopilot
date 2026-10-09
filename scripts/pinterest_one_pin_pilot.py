"""One-item Pinterest handoff pilot. Never processes Gumroad or other Pins.

Default mode only validates metadata; explicit live approval is required to
schedule the exact chosen Pin. Do not expose credentials in logs.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import autopilot


PILOT_ID = "Q-02"
EXPECTED_DESTINATION = "https://kindgridstudio.gumroad.com/l/ultimate-budget-planner"
EXPECTED_BOARD = "Budgeting Printables & Cash Stuffing"


def main() -> int:
    live = os.getenv("PIN_PILOT_CONFIRM_LIVE", "false").lower() == "true"
    os.environ["LIVE_MODE"] = "true" if live else "false"
    os.environ["PIN_AUTOSCHEDULE"] = "true" if live else "false"
    os.environ["GUMROAD_CREATE_DRAFTS"] = "false"
    os.environ["GUMROAD_AUTOPUBLISH"] = "false"
    os.environ["PIN_LOOKAHEAD_HOURS"] = "168"

    print(f"PINTEREST_PILOT: Selected {PILOT_ID}; live={live}; Gumroad DISABLED.")
    store = autopilot.GoogleStore()
    candidates = [r for r in store.get_rows("Publishing Queue") if r.get("Queue ID") == PILOT_ID]
    if len(candidates) != 1:
        print("PILOT_ABORT: Expected exactly one Q-02 row. No posts created.")
        return 1
    row = candidates[0]
    if row.get("Status") != "READY" or row.get("QA Verified (YES/NO)") != "YES":
        print("PILOT_ABORT: Q-02 is not READY with verified QA. No posts created.")
        return 1
    if row.get("Destination URL") != EXPECTED_DESTINATION or row.get("Target Board") != EXPECTED_BOARD:
        print("PILOT_ABORT: Q-02 sales link or board differs from approved source.")
        return 1
    if row.get("Batch ID") or row.get("Actual Pinterest Pin URL"):
        print("PILOT_ABORT: Existing publishing record detected; do not duplicate.")
        return 1

    try:
        pin = autopilot.validate_pin(row, datetime.now(timezone.utc), 168)
        print(f"PILOT_METADATA_OK: {pin['id']} scheduled for {pin['due'].isoformat()}, exact paid product link.")
    except ValueError as exc:
        print(f"PILOT_ABORT: {exc}")
        return 1
    if not live:
        print("PILOT_DRY_RUN_OK: One Pin validated. No uploads, edits or scheduling.")
        return 0

    result = autopilot.process_pins(store, [row], datetime.now(timezone.utc))
    for line in result:
        print(line)
    refreshed = [r for r in store.get_rows("Publishing Queue") if r.get("Queue ID") == PILOT_ID]
    status = refreshed[0].get("Status", "") if len(refreshed) == 1 else ""
    if status != "SCHEDULED_BUFFER":
        print(f"PILOT_NEEDS_REVIEW: Pin not confirmed scheduled; sheet status={status}. No automatic retry.")
        return 1
    print("PILOT_SCHEDULED: Exactly one Pin recorded in Buffer. Verify its destination URL in Buffer UI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
