#!/usr/bin/env python3
"""
ring_phone.py — tiny HTTP endpoint that rings an analog phone connected
to an ATA's FXS port, by sending it a SIP INVITE and then cancelling it
before it's ever answered. No PBX, no SIP trunk needed — this works as
a direct LAN peer-to-peer call.

Should work with any ATA that accepts a direct SIP call to a locally
configured extension (Grandstream HT80x, Cisco/Linksys SPA, Obihai,
Yealink, etc.) — tested against a Grandstream HT802V2.

Requires:
    uv sync
Run:
    uv run ring_phone.py
Then:
    curl -X POST http://<this-machine>:5005/ring
    curl -X POST "http://<this-machine>:5005/ring?seconds=10"
"""

import os

from flask import Flask, request
from nanosip import Invite, SIPAuthCreds, call_and_cancel

app = Flask(__name__)

# fmt:off
# --- Edit these for your setup, or override via env vars of the same name --
ATA_IP        = os.getenv("ATA_IP", "192.168.1.100")  # LAN IP of the ATA
ATA_PORT      = int(os.getenv("ATA_PORT", "5060"))    # SIP port - 5060 is the common default
ATA_EXTENSION = os.getenv("ATA_EXTENSION", "phone1")  # SIP user ID / extension configured on the FXS port
CALLER_NAME   = os.getenv("CALLER_NAME", "phone1")    # For debug use only, shows up in the ATA's call log
RING_SECONDS  = int(os.getenv("RING_SECONDS", "3"))   # default ring duration before auto-cancel

# Only needed if you've enabled auth for incoming calls on the ATA (uncommon
# for a plain LAN peer call). Leave blank otherwise.
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")
# -----------------------------------------------------------------------------
# fmt:on


@app.route("/ring", methods=["POST", "GET"])
def ring():
    seconds = int(request.args.get("seconds", RING_SECONDS))
    auth_creds = SIPAuthCreds(username=AUTH_USERNAME, password=AUTH_PASSWORD)
    inv = Invite(
        uri_from=f"sip:{CALLER_NAME}@{ATA_IP}",
        uri_to=f"sip:{ATA_EXTENSION}@{ATA_IP}",
        uri_via=ATA_IP,
        auth_creds=auth_creds,
    )
    try:
        call_and_cancel(inv, seconds, f"{ATA_IP}:{ATA_PORT}")
        return {"status": "ok", "rang_for_seconds": seconds}, 200
    except OSError as e:
        # e.g. "nanosip error: 407 Unauthorized" if the ATA challenges the call
        return {"status": "error", "detail": str(e)}, 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
