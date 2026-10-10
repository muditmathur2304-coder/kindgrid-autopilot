"""Read-only check of publishing integrations. Never writes to services."""
import json
from src.autopilot import GoogleStore, BufferClient

def main():
    store = GoogleStore()
    pins = store.get_rows("Publishing Queue")
    products = store.get_rows("Gumroad Upload Queue")
    print("SHEETS_READ_OK", len(pins), len(products))
    client = BufferClient()
    boards = client.boards()
    print("PINTEREST_BOARD_OK", "Budgeting Printables & Cash Stuffing" in boards)
    print("BUFFER_QUEUED_COUNT", client.scheduled())
    for row in pins:
        if row.get("Status") != "SCHEDULED_BUFFER" or not row.get("Batch ID"):
            continue
        try:
            post = client.get_post(row["Batch ID"])
            details = {
                "pin": row.get("Queue ID"),
                "status": post.get("status"),
                "pinterest_url": post.get("externalLink") or "",
                "destination_valid": (post.get("metadata") or {}).get("url") == row.get("Destination URL"),
            }
            print("PIN_READBACK", json.dumps(details, ensure_ascii=True))
        except Exception as error:
            print("PIN_READBACK_ERROR", row.get("Queue ID"), type(error).__name__)
    print("READ_ONLY_FINISHED")

if __name__ == "__main__":
    main()
