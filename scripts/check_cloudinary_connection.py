"""Read-only Cloudinary credential diagnostic, safe for GitHub Actions logs.

Prints only error categories, never API credentials, URLs, response bodies, or
exception messages that might contain them. Never uploads or modifies assets.
"""
import os
import sys
from urllib.parse import urlsplit


def main() -> int:
    raw = os.getenv("CLOUDINARY_URL", "").strip()
    if not raw:
        print("CLOUDINARY_SETUP_REQUIRED: GitHub secret CLOUDINARY_URL is missing.")
        return 1
    if raw.startswith("CLOUDINARY_URL="):
        print("CLOUDINARY_FORMAT_ERROR: Secret includes CLOUDINARY_URL= prefix. Store only the cloudinary:// value.")
        return 1
    if raw[:13] != "cloudinary://":
        print("CLOUDINARY_FORMAT_ERROR: Secret must start with cloudinary://")
        return 1
    try:
        parsed = urlsplit(raw)
        if not parsed.username or parsed.password is None or not parsed.hostname:
            print("CLOUDINARY_FORMAT_ERROR: API key, secret, or cloud name missing in URL.")
            return 1
        if any("<" in x or ">" in x for x in [parsed.username, parsed.password, parsed.hostname]):
            print("CLOUDINARY_FORMAT_ERROR: URL still contains placeholder values.")
            return 1
    except ValueError:
        print("CLOUDINARY_FORMAT_ERROR: Could not parse the API environment variable.")
        return 1

    try:
        import cloudinary
        import cloudinary.api
        import cloudinary.exceptions

        # Cloudinary's Python SDK automatically reads CLOUDINARY_URL.
        cloudinary.config(secure=True)
        cfg = cloudinary.config()
        if not all((cfg.cloud_name, cfg.api_key, cfg.api_secret)):
            print("CLOUDINARY_SDK_ERROR: SDK did not load all credentials from CLOUDINARY_URL.")
            return 1
        print("CLOUDINARY_FORMAT_OK: Credentials parsed and loaded without exposing values.")
        reply = cloudinary.api.ping()
        if reply.get("status") != "ok":
            print("CLOUDINARY_PING_ERROR: Authenticated ping returned a non-OK status.")
            return 1
    except cloudinary.exceptions.AuthorizationRequired:
        print("CLOUDINARY_AUTH_ERROR: Cloudinary rejected the API key or secret (401).")
        return 1
    except cloudinary.exceptions.NotAllowed:
        print("CLOUDINARY_PERMISSION_ERROR: API access forbidden (403).")
        return 1
    except cloudinary.exceptions.RateLimited:
        print("CLOUDINARY_RATE_LIMIT: Cloudinary API rate limit reached.")
        return 1
    except Exception as error:
        # Type only; messages can contain credential-bearing URLs.
        print(f"CLOUDINARY_SDK_OR_NETWORK_ERROR: {type(error).__name__}.")
        return 1

    print("CLOUDINARY_CONNECTED: Authenticated Cloudinary ping succeeded (read-only).")
    print("CLOUDINARY_SAFE: No files uploaded, changed, or deleted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
