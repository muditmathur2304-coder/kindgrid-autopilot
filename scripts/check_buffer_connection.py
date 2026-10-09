"""Read-only verification of the Buffer account, organization, and Pinterest channel.

No mutation queries, no posting, no token/ID logging.
"""
import os
import sys

import requests

ENDPOINT = "https://api.buffer.com"
REQUIRED = ("BUFFER_API_KEY", "BUFFER_ORGANIZATION_ID", "BUFFER_PINTEREST_CHANNEL_ID")


def read_only_query(query: str, token: str) -> dict:
    try:
        response = requests.post(
            ENDPOINT,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"query": query},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        # Avoid printing sensitive request headers or full server payloads.
        raise RuntimeError("Buffer HTTP or JSON response error") from None
    if payload.get("errors"):
        raise RuntimeError("Buffer GraphQL query failed; check API key and permissions")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Buffer response missing data")
    return data


def main() -> int:
    if any(not os.environ.get(name, "").strip() for name in REQUIRED):
        print("BUFFER_SETUP_REQUIRED: One or more Buffer secrets are missing.")
        return 1

    token = os.environ["BUFFER_API_KEY"].strip()
    organization_id = os.environ["BUFFER_ORGANIZATION_ID"].strip()
    channel_id = os.environ["BUFFER_PINTEREST_CHANNEL_ID"].strip()

    try:
        account = read_only_query(
            "query KindGridOrganizations { account { organizations { id name } } }",
            token,
        )
        orgs = (account.get("account") or {}).get("organizations") or []
        if not any(str(org.get("id")) == organization_id for org in orgs):
            raise RuntimeError("Configured Buffer organization was not found in this account")

        channels = read_only_query(
            """query KindGridChannels {
                channels(input: { organizationId: %s }) {
                    id
                    name
                    service
                }
            }""" % __import__("json").dumps(organization_id),
            token,
        ).get("channels") or []

        matched = [
            ch for ch in channels
            if str(ch.get("id")) == channel_id
            and str(ch.get("service", "")).lower() == "pinterest"
        ]
        if not matched:
            raise RuntimeError("Configured channel was not found as a Pinterest channel")

        print("BUFFER_CONNECTED: Organization and Pinterest channel verified (read-only).")
        print("BUFFER_SAFE: No posts created, scheduled, modified, or published.")
        return 0
    except RuntimeError as exc:
        print(f"BUFFER_VERIFY_FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
