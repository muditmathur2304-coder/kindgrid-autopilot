"""One-time READ-ONLY Buffer Q-44 delivery verification; never repost."""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src import autopilot as a

EXPECTED_ID="6ac98f24b07d37ac975846a0"
DUE=datetime.fromisoformat("2026-10-10T01:11:33+00:00")
cutoff=DUE.timestamp()+18
if time.time()<cutoff: time.sleep(min(135,cutoff-time.time()))
store=a.GoogleStore()
rows=[r for r in store.get_rows("Publishing Queue") if r.get("Queue ID")=="Q-44"]
a.require(len(rows)==1,"Q-44 queue row not unique")
row=rows[0]
a.require(row.get("Batch ID")==EXPECTED_ID,"Buffer post ID changed; no mutation")
a.require(row.get("Status") in ("SCHEDULED_BUFFER","PUBLISHED"),"Q-44 has other state; no mutation")
if row.get("Status")=="PUBLISHED":
    print("Q44_ALREADY_PUBLISHED "+str(row.get("Actual Pinterest Pin URL") or ""))
    sys.exit(0)
client=a.BufferClient()
for n in range(4):
    post=client.get_post(EXPECTED_ID)
    status=str(post.get("status") or "")
    external=str(post.get("externalLink") or "")
    print(f"Q44_DELIVERY_CHECK {n+1}: status={status}, has_external_url={bool(external)}")
    if status=="sent":
        host=urlparse(external).netloc.lower()
        if host in {"www.pinterest.com","pinterest.com","in.pinterest.com"} and urlparse(external).path.startswith("/pin/"):
            store.patch("Publishing Queue",row,{"Status":"PUBLISHED",
                "Actual Pinterest Pin URL":external,"Last Error":""})
            print("Q44_PINTEREST_PUBLISHED_VERIFIED "+external)
        else:
            store.patch("Publishing Queue",row,{"Status":"LINK_REVIEW",
                "Last Error":"Buffer sent Q44 but external Pinterest URL missing or invalid"})
            print("Q44_SENT_BUT_LINK_UNVERIFIED")
        sys.exit(0)
    if status=="error":
        store.patch("Publishing Queue",row,{"Status":"NEEDS_FIX",
              "Last Error":"Buffer Q44 reports delivery error; no duplicate posting"})
        print("Q44_BUFFER_DELIVERY_ERROR")
        sys.exit(0)
    if n<3: time.sleep(12)
print("Q44_STILL_SCHEDULED: Cannot claim it is live until Buffer reports sent.")
