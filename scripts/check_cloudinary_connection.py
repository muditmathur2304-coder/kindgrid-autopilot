"""Verify KindGrid Cloudinary credentials with a read-only authenticated ping.

Never prints the Cloudinary URL, API key, API secret, cloud name or response body.
Does not upload, delete, or transform any media.
"""
import os
import sys


def main() -> int:
    if not os.getenv("CLOUDINARY_URL", "").strip():
        print("CLOUDINARY_SETUP_REQUIRED: CLOUDINARY_URL secret is missing.")
        return 1
    try:
        import cloudinary
        import cloudinary.api

        cloudinary.config(secure=True)
        cfg = cloudinary.config()
        if not all((cfg.cloud_name, cfg.api_key, cfg.api_secret)):
            print("CLOUDINARY_VERIFY_FAILED: Credential format is incomplete.")
            return 1

        reply = cloudinary.api.ping()
        if reply.get("status") != "ok":
            print("CLOUDINARY_VERIFY_FAILED: Ping status not OK.")
            return 1
    except Exception:
        # Do not expose full exceptions; they may contain credential-bearing URLs.
        print("CLOUDINARY_VERIFY_FAILED: Authenticated ping was rejected or unreachable.")
        return 1

    print("CLOUDINARY_CONNECTED: Authenticated Cloudinary ping succeeded (read-only).")
    print("CLOUDINARY_SAFE: No files uploaded, changed, or deleted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
