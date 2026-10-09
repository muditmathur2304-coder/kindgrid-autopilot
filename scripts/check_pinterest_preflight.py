"""Preflight Buffer Pinterest API capabilities without posting or hosting images."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.autopilot import BufferClient

EXPECTED = {
    "Savings Challenges & Money Trackers",
    "Budgeting Printables & Cash Stuffing",
    "Debt Free Journey & Payoff Trackers",
    "Calm Living & Minimalist Planners",
}


def main():
    try:
        buffer = BufferClient()
        boards = buffer.boards()
        scheduled = buffer.scheduled()
    except Exception as exc:
        print("PINTEREST_PREFLIGHT_FAILED: Buffer boards or queue API did not respond as expected.")
        print(f"Failure category: {type(exc).__name__}; no posts or images created.")
        return 1

    print(f"PINTEREST_QUEUE_READ_OK: {scheduled} queued posts.")
    print("PINTEREST_BOARDS_READ_OK: Buffer returned board information.")
    print("PINTEREST_BOARDS_VISIBLE: " + " | ".join(sorted(boards.keys())))
    missing = sorted(EXPECTED.difference(boards))
    if missing:
        print("PINTEREST_BOARD_MISSING: " + ", ".join(missing))
        print("No posts created; create/refresh the missing boards before proceeding.")
        return 1

    if scheduled >= 10:
        print("PINTEREST_QUEUE_FULL: Buffer Free scheduling queue is at capacity.")
        return 1

    print("PINTEREST_PREFLIGHT_PASSED: Required boards and Free queue capacity verified.")
    print("PINTEREST_SAFE: No posts, images, or destinations created or modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
