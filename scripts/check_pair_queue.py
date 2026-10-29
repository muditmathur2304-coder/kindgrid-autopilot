"""Read-only job preflight: install seller CLI only when a full PAID+FREE pair is ready."""
import os
from src import autopilot as a
from src.paired_release import select_ready_pairs


def main():
    if not a.enabled("LIVE_MODE") or not a.enabled("PAIRED_RELEASE_ENABLED"):
        amount = 0
    else:
        rows = a.GoogleStore().get_rows("Gumroad Upload Queue")
        try:
            amount = len(select_ready_pairs(rows))
        except ValueError as error:
            # A forged/invalid QA link must never install a seller CLI or
            # abort the entire scheduled job before independent Pin checks.
            # Leave source rows unchanged for explicit QA reconciliation.
            print(f"PAIR_PREFLIGHT_BLOCKED: {error}; no seller action")
            amount = 0
    needed = "true" if amount else "false"
    print("PAIR_PREFLIGHT: %s complete validated pair(s); needs_cli=%s" % (amount, needed))
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            out.write("needs_cli="+needed+"\n")


if __name__=="__main__":
    main()
