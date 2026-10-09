"""Low-cost preflight: install Gumroad CLI only when a new READY draft exists.

Google Sheets is read using the existing scoped service account. This step
never creates, changes or publishes anything.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.autopilot import GoogleStore, validate_gumroad


def main():
    if not os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_B64"):
        print("PREFLIGHT_BLOCKED: Google credentials missing.")
        return 1
    try:
        store = GoogleStore()
        rows = store.get_rows("Gumroad Upload Queue")
        valid = []
        for row in rows:
            if row.get("Upload Status") == "READY" and row.get("QA Verified (YES/NO)") == "YES":
                try:
                    valid.append(validate_gumroad(row))
                except ValueError:
                    # Main publisher will set NEEDS_FIX for invalid READY rows.
                    pass
        requires_cli = bool(valid)
        output_path = os.getenv("GITHUB_OUTPUT")
        if not output_path:
            print("PREFLIGHT_BLOCKED: GitHub output path unavailable.")
            return 1
        with open(output_path, "a", encoding="utf-8") as output:
            output.write(f"needs_cli={'true' if requires_cli else 'false'}\n")
        print(f"NEW_DRAFT_PREFLIGHT: {len(valid)} eligible new product(s).")
        print("GUMROAD_CLI_REQUIRED: " + ("YES" if requires_cli else "NO (skip Go installation)."))
        return 0
    except Exception as error:
        print(f"PREFLIGHT_BLOCKED: {type(error).__name__}; no external writes.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
