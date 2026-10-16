"""Owner-authorized one-time send-now of TWO already-scheduled Buffer Pins.

Provider preflight 2026-10-16T03:15Z confirmed exact provider IDs, published-now
allowed action, matching destination and future due times. No createPost calls.
Run only on owner-scoped one-time existing GitHub publisher push. No retries.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse
from src import autopilot as a

OWNER_MARKER = "KINDGRID_OWNER_SENDNOW_2026_10_16"
POSTS = {
    "Q-65": "6ad193acee2c696029b87cf7",
    "Q-66": "6ad193affb64fffcf1b0d38d",
}


def valid_public_pin(url: str) -> bool:
    parsed = urlparse(str(url or ""))
    return parsed.scheme == "https" and parsed.netloc.lower() in {
        "pinterest.com", "www.pinterest.com", "in.pinterest.com",
    } and parsed.path.startswith("/pin/")


def main() -> int:
    a.require(os.environ.get("KINDGRID_PIN_NOW_AUTHORIZATION") == OWNER_MARKER,
              "Not owner-authorized; cannot send scheduled Pins now")
    store = a.GoogleStore()
    rows = {r.get("Queue ID"): r for r in store.get_rows("Publishing Queue")}
    client = a.BufferClient()
    boards = client.boards()

    check_query = """query P($id:PostId!) {
        post(input:{id:$id}) {
            id status dueAt externalLink allowedActions
            metadata { ... on PinterestPostMetadata {
                url title board { serviceId }
            } }
        }
    }"""
    mutation = """mutation N($input:EditPostInput!) {
        editPost(input:$input) {
            ... on PostActionSuccess {
                post {id status externalLink dueAt
                    metadata { ... on PinterestPostMetadata {url} }
                }
            }
            ... on MutationError {message}
        }
    }"""

    for qid, batch in POSTS.items():
        row = rows.get(qid)
        a.require(row is not None and row.get("Batch ID") == batch and
                  row.get("Status") == "SCHEDULED_BUFFER",
                  qid + ": not the approved existing scheduled post")
        a.verify_qa_report(store, row, qid)
        a.require(row.get("Target Board") in boards,
                  qid + ": provider board not found")
        src = client.graphql(check_query, {"id": batch}).get("post") or {}
        meta = src.get("metadata") or {}
        a.require(src.get("id") == batch and src.get("status") == "scheduled" and
                  "publishPostNow" in (src.get("allowedActions") or []) and
                  meta.get("title") == row.get("Pin Title") and
                  meta.get("url") == row.get("Destination URL") and
                  (meta.get("board") or {}).get("serviceId") == boards[row["Target Board"]],
                  qid + ": provider metadata/action mismatch, refuse mutation")
        print(qid + ": EXACT_EXISTING_BUFFER_POST_VERIFIED")
        # One mutation to an existing scheduled post; NEVER create/duplicate.
        try:
            changed = client.graphql(mutation, {
                "input": {"id": batch, "mode": "shareNow"}
            }).get("editPost") or {}
            post = changed.get("post")
            if not post or post.get("id") != batch:
                raise RuntimeError("Buffer did not confirm post edit; no retry")
            if (post.get("metadata") or {}).get("url") != row["Destination URL"]:
                raise RuntimeError("Edited Pin destination mismatched, verify before any further posting")
            # Independently read back the SAME post after edit.
            current = client.graphql(check_query, {"id": batch}).get("post") or {}
            a.require(current.get("id") == batch, "Cannot verify existing post after send-now")
            url = current.get("externalLink") or post.get("externalLink") or ""
            if current.get("status") == "sent" and valid_public_pin(url):
                store.patch("Publishing Queue", row, {
                    "Status": "PUBLISHED", "Actual Pinterest Pin URL": url,
                    "Last Error": ""})
                print(qid + ": PINTEREST_PUBLIC_CONFIRMED " + url)
            elif current.get("status") == "error":
                store.patch("Publishing Queue", row, {
                    "Status": "NEEDS_FIX",
                    "Last Error": "Buffer reports a send-now Pinterest publishing error"})
                print(qid + ": BUFFER_SEND_NOW_ERROR; no retry")
            elif current.get("status") == "sent":
                store.patch("Publishing Queue", row, {
                    "Status": "LINK_REVIEW",
                    "Last Error": "Buffer says sent but public Pinterest Pin URL unavailable"})
                print(qid + ": SENT_BUT_PIN_LINK_MISSING; no retry")
            else:
                # When queued for immediate delivery, pending asynchronous provider
                # status is not a confirmed published Pin. Never invent a URL.
                print(qid + ": BUFFER_SEND_NOW_ACCEPTED status=" +
                      str(current.get("status")) +
                      "; wait for provider public Pinterest Pin URL")
        except Exception as exc:
            # Provider may have accepted mutation; do NOT send a second one.
            print(qid + ": BUFFER_SEND_NOW_UNCERTAIN " + type(exc).__name__ +
                  "; original Buffer post must be reconciled, no retry")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
