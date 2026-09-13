# ring-phone

A tiny HTTP endpoint that rings an analog phone connected to an ATA's FXS port,
by sending it a SIP `INVITE` and cancelling it before it's ever answered.

No PBX, no SIP trunk, no registration — this talks directly to the ATA as a
LAN peer-to-peer call using [nanosip](https://github.com/WatskeBart/nanosip).
Handy for things like a Home Assistant automation that should ring a physical
phone (e.g. as a doorbell or notification chime) without playing any audio.

Should work with any ATA that accepts a direct SIP call to a locally
configured extension — Grandstream HT80x, Cisco/Linksys SPA, Obihai, Yealink,
etc. — though it's only been tested against a Grandstream HT802V2.

## How it works

1. `POST /ring` sends a SIP `INVITE` to the ATA's configured extension.
2. The phone starts ringing.
3. After `RING_SECONDS` (default 3), the call is cancelled with `CANCEL`
   before it can be answered — so it never actually connects and no audio
   path is ever established.

## Setup

Find your ATA's LAN IP, SIP port, and the extension/user ID configured on its
FXS port (check the ATA's web UI — don't assume the defaults below match your
device).

### Run locally

```bash
uv sync
uv run ring_phone.py
```

### Run with Docker

```bash
docker build -t ring-phone .
docker run -d -p 5005:5005 \
  -e ATA_IP=192.168.1.100 \
  -e ATA_EXTENSION=phone1 \
  -e CALLER_NAME=phone1 \
  ring-phone
```

## Configuration

Every setting can be edited directly at the top of `ring_phone.py`, or
overridden with an environment variable of the same name:

| Variable        | Default           | Description                                                        |
|------------------|-------------------|----------------------------------------------------------------------|
| `ATA_IP`         | `192.168.1.100`   | LAN IP of the ATA                                                   |
| `ATA_PORT`       | `5060`            | SIP port for the ATA (5060 is the common default)                  |
| `ATA_EXTENSION`  | `phone1`          | SIP user ID / extension configured on the FXS port                 |
| `CALLER_NAME`    | `phone1`          | Caller identity used in the SIP `From` header (debug/log use only) |
| `RING_SECONDS`   | `3`               | Default ring duration before auto-cancel                           |
| `AUTH_USERNAME`  | *(empty)*         | Only needed if the ATA requires auth for incoming calls (uncommon) |
| `AUTH_PASSWORD`  | *(empty)*         | Only needed if the ATA requires auth for incoming calls (uncommon) |

## Usage

```bash
# Ring using the default RING_SECONDS
curl -X POST http://<this-machine>:5005/ring

# Ring for a custom duration
curl -X POST "http://<this-machine>:5005/ring?seconds=10"
```

A successful call returns:

```json
{"status": "ok", "rang_for_seconds": 3}
```

If the ATA rejects the call (e.g. it requires auth and none/incorrect
credentials were supplied), you'll get a `502` with the underlying SIP error:

```json
{"status": "error", "detail": "nanosip error: 407 Unauthorized"}
```

## Home Assistant example

```yaml
rest_command:
  ring_phone:
    url: "http://<this-machine>:5005/ring?seconds=5"
    method: POST
```
