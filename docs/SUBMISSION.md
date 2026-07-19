# Sensor Data Collector Service
Answers to the three TASKS, with the implementation in this repository as the reference.
Anything described here as implemented is in the code, limitations are also listed

**Contents**
- [Task 1 — Requirement conflicts](#task-1--requirement-conflicts)
- [Task 2 — How each requirement would be fulfilled](#task-2--how-each-requirement-would-be-fulfilled)
- Task 3 — Implementation
- [AI usage](#ai-usage)

**Governing rule used throughout:** where REQ-1 or REQ-2 conflicts with REQ-3 (12-fator-app principle), 12 factor app principle are preferred

---

# Task 1 — Requirement conflicts

## C-1 — REQ-2 fixes the broker to localhost; REQ-3 forbids fixing it

**What conflicts.** REQ-2 assumes the broker runs on localhost, standard port, no authentication.
REQ-3 requires 12-factor compliance.

**Why.** Factor IV (backing services as attached resources i.e MQTT broker in our case) and Factor III (config in the environment)
require a backing service to be addressable by config and swappable **without a code change**. REQ-2 instead fix the broker to be running on localhost.

**Resolution.** Assuming REQ-2 describes current setup, Move host, port, username, password and TLS to environment variables whose defaults are `localhost, 1883, and no auth.` 

## C-2 — REQ-1's assumption that local time is also in UTC conflicts with REQ-3 (dev/prod parity)

**What conflicts.** An implementation relying on the server's local timezone would introduce an
environment-specific dependency, which is contrary to the Dev/Prod parity principle.

**Solution.** Instead of assuming the server's local time is in UTC and using server time to check
message validity, use UTC time explicitly. In production, a Network Time Protocol (NTP) server is
generally used to provide accurate synchronized time across all machines.

---

## Ambiguities and the assumptions taken

| # | Ambiguity | Assumption taken |
|---|---|---|
| A-1 | Is the range `[-50.00, 110.00]` inclusive? | **Inclusive.** Sensor bounds conventionally include their limits. |
| A-2 | Does `.00` imply a rounding rule? | **No rounding.** A value with more than 2 decimal places is a **format error**, rejected. |
| A-3 | Is the ±600 s window inclusive, and why allow future timestamps? | **Inclusive and symmetric**, deliberately, since it absorbs modest sensor-side clock skew. |
| A-4 | What is "a given topic"? | **One static topic per deployment** (`BROKER_TOPIC`). This is why `device_id` must be in the payload. |
| A-5 | Is there a `device_id` format? | **Exactly 4 digits**, kept as a **string** so leading zeros survive (`int('0001')` would renumber the device to 1). |
| A-6 | JSON payload schema? | `{"device_id": str, "value": number, "timestamp": int}`, typed, not stringly-typed. |
| A-7 | Are fractional timestamps valid? | **No.** REQ-1 says *seconds*, so sub-second precision is a format error. |
| A-8 | "Must be published" — where should the durability live? | **The broker.** Publish at QoS 1 and answer `202` only once it acknowledges; `503` otherwise. |
| A-9 | What is the HTTP response contract? Nothing says what a rejected reading is told. | **Explicit status codes plus machine-readable eCodes.** As written, both requirements are satisfied by a service that silently discards invalid readings and returns `200`, which is what the provided code did. |

---

# Task 2 — How each requirement would be fulfilled

For each: **how it is built**, **how it is proven**, and **what it still does not guarantee**. 

---

## REQ-1 — Messages validation for format and plausibility

**Goal** — Ensure that only valid and plausible sensor readings are accepted and processed.

### Approach

- Extract request data, reject missing fields with an appropriate client error (400 Bad Request).
- Type checks
  - `device_id` — from URL path, as `str`
  - `value` — from the request form, parsed to `Decimal` (not `float`: `Decimal("110.005")` is exact
    where `float("110.005")` is already `110.00499…`)
  - `timestamp` — from the request form, parsed as `int`
- Temperature value checks, in this order
  - Reject `NaN` / `±inf` **first**. They parse successfully and then raise `InvalidOperation` on
    comparison, so without the guard they escape validation and the endpoint answers 500 instead of 400.
  - Reject more than 2 decimal places as a **format error** rather than rounding. Rounding would judge a
    value by one form and publish another — `110.004` would round into range, then be published as
    `110.004`, outside the bounds a consumer applies. Rejecting keeps validated and published values
    identical, and removes the rounding-mode hazard entirely.
  - Then compare inclusively: `-50.00 <= value <= 110.00`
- Timestamp window: `abs(now - timestamp) <= 600`, where `now` is UTC epoch seconds obtained explicitly
  as UTC (`datetime.now(timezone.utc).timestamp()`), never via local-time APIs.
- `device_id`: constrain to `^[0-9]{4}$`, kept as a string so leading zeros survive. `[0-9]` not `\d` —
  Python's `\d` also matches Unicode digits, so fullwidth `１２３４` would otherwise pass.
- Collect **every** field error before responding, so a misconfigured sensor learns about all its
  problems in one round-trip.

### Request contract

`POST /api/sensors/{device_id}/readings` · `application/x-www-form-urlencoded`

| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `device_id` | path | string | yes | Sensor identifier, exactly 4 digits, e.g. `0001` |
| `value` | form | number | yes | Reading in °C, `-50.00`…`110.00`, at most 2 decimal places |
| `timestamp` | form | integer | yes | Unix epoch seconds (UTC), within ±600 s of the current UTC time |

### Response contract

| Situation | Status |
|---|---|
| Validated and confirmed by the broker | `202 Accepted` |
| Missing or invalid input | `400 Bad Request` |
| Broker unavailable or unconfirmed | `503 Service Unavailable` + `Retry-After` |

`202` rather than `200`: the reading has been accepted and forwarded to the broker, but this service has
not *processed* it — that is the consumer's job.

Errors carry a machine-readable code alongside the reason. The code is the stable half of the contract:
the reason text may be reworded, but a code must not change meaning once devices key behaviour off it.
Each maps to one distinct client action, so a sensor can tell a hardware fault from a firmware
formatting bug without parsing prose.

| eCode | Meaning | eCode | Meaning |
|---|---|---|---|
| `0001` | `value` missing | `0005` | `timestamp` missing |
| `0002` | `value` not a number | `0006` | `timestamp` not an integer |
| `0003` | `value` out of range | `0007` | `timestamp` outside ±600 s |
| `0004` | `value` has more than 2 decimals | `0008` | `device_id` not 4 digits |
| | | `0100` | broker unavailable |

**Logging** — one `INFO` line per rejection with `device_id`, code and reason. Enough to diagnose a bad
device; no payload dumps, no secrets.

### Implementation

Validation lives in `api/validation.py` as pure functions, with `now`, the current time, passed in
rather than read inside. That choice makes the ±600 s rule an ordinary function call and lets the tests
run with no clock mocking, Flask, or broker.

### Testing

**Unit — value** (`test_validation.py`, pure, no infra)
- `-50.00`, `110.00` → accept (bounds inclusive)
- `-50.01`, `110.01` → reject (outside the range)
- `20`, `20.5`, `20.50`, `1E+1` → accept (0–2 dp, scientific notation handled)
- `50.004`, `110.004`, `1.5E-5` → reject (excess precision is a format error)
- `NaN`, `Infinity`, `-Infinity` → reject (non-finite guard runs first)
- `"abc"`, `""`, missing → reject

**Unit — timestamp**
- `now`, `now-600`, `now+600` → accept (window inclusive, symmetric)
- `now-601`, `now+601` → reject (bounded both sides)
- `"1752243577.5"` → reject (seconds are integral)
- `"abc"`, `""`, missing → reject

**Unit — device_id**
- `0001` → accepted and kept as a string (leading zeros preserved)
- `123`, `12345`, `abcd`, fullwidth `１２３４` → reject

**Unit — error contract**
- bad value *and* bad timestamp → both errors returned, not just the first
- each failure mode carries its own eCode

**Timezone independence**, the check that proves the C-2 resolution
- run the whole suite under `TZ=UTC` and `TZ=Asia/Karachi` → identical results
- `now` injected as a fixed int, never read from the clock inside the validator

**Route level** (`test_routes.py`, Flask test client, publisher stubbed)
- valid form POST → `202`, body is the parsed reading
- invalid reading → `400`, body has per-field errors with codes
- invalid reading → publisher called **zero** times (proves the REQ-1/REQ-2 seam)
- wrong method (GET) → `405` (free from Flask)
- missing form fields → `400`, not a `500`

### Limitations

- **Clock drift is invisible from inside the service.** If NTP fails, the service rejects 100 % of
  traffic while reporting itself healthy, and it presents as a sensor bug. Needs an external NTP-offset
  probe or rejection-rate alerting. 
- **Two inferred rules could reject valid field traffic**, the 4-digit `device_id` (A-5) and the 2-dp
  precision limit (A-2). Sensors often report finer precision than their specified range.
- **"Format" is verified against my reading of the requirement**, not against real sensor firmware.

## REQ-2 — Publish validated data to MQTT

**Goal.** Anything answered with `2xx` has been accepted by the broker. Nothing invalid is published;
switching brokers is a configuration change.

"Must be published" cannot mean "even when the broker is
down" - nothing delivers to an unreachable next hop while holding nothing itself. What is achievable is
the **acknowledgement boundary: never acknowledge data that has not been handed off.** That is the
requirement actually implemented.

### How it is built

**1. Broker config from the environment.** `MQTT_HOST` / `MQTT_PORT` / `MQTT_USERNAME` /
`MQTT_PASSWORD` / `MQTT_TLS`, defaulting to `localhost`, `1883`, no auth, the C-1 resolution made real.

**2. Non-blocking connection.** `connect_async()` + `loop_start()` rather than `connect()`. A broker
that is down **must not stop the service from starting** — readings are refused with `503` until the
connection is up, and paho's background thread reconnects on its own without a restart. Verified live.

**3. Typed payload.** `{"device_id": "0001", "value": 109.0, "timestamp": 1752243577}`, with
`value` a JSON number and `timestamp` an integer. The provided route read both form fields with `type=str`

**4. QoS 1 plus confirmation**
`publish(topic, payload, qos=1, retain=True)` followed by
`wait_for_publish(timeout=MQTT_PUBLISH_TIMEOUT)`. Without the wait, publishing is fire-and-forget and a
`202` would claim more than we know. The PUBACK is the durability boundary; the timeout bounds the HTTP
request so an unresponsive broker cannot tie up a worker indefinitely, which matters because each sync
gunicorn worker handles one request at a time.

**5. `retain=True`.** The broker keeps the most recent reading per topic and delivers it to any
subscriber on connect, so a consumer starting up has a value immediately instead of waiting for the
next one. Only the last reading is kept.

**6. Durability belongs to the broker, not the process.** Factor VI places state in a backing service,
and the broker *is* that service.

**7. logging.** Publish failures log at `ERROR` with `device_id`.

**8. Graceful shutdown.** `close()` → `loop_stop()` + `disconnect()`, registered via `atexit` in the
application factory (Factor IX).

### How it is proven

**Unit** (`test_publisher.py`, paho stubbed)
- the published payload is valid JSON carrying all three fields at the right types, `value` a number
  and `timestamp` an integer, not strings

**Route level** (`test_routes.py`, publisher stubbed)
- broker confirms → `202`
- publisher raises → `503` with `Retry-After`, never `202`
- invalid reading → publisher called **zero** times (the REQ-1/REQ-2 seam)

**Manual, end to end** (`docker compose up`, subscribed with `mosquitto_sub`)
- valid reading → `202` and the exact payload arrives on the topic
- broker stopped → `503`; broker restarted → `202` again with no application restart
- `MQTT_HOST` points at the broker by container name, proving the C-1 resolution

### Limitations and residual risks
- **Delivery is guaranteed only as far as the broker.** A PUBACK confirms the broker accepted the
  message, not that any consumer received it, and its durability depends on broker configuration
  outside this repository. QoS 1 also means duplicates are possible, and during an outage readings are
  lost unless the sensor retries.

---

## REQ-3 — 12-factor-app principles

- All config via `environs` in `settings.py`; nothing hardcoded **(Factor 3)**
- Broker addressed by `MQTT_HOST` / `MQTT_PORT` **(Factor 4)**
- Changing a broker is just an env change, proven by compose reaching it as `broker` **(Factor 4)**
- All dependencies pinned in `requirements.txt`, including `paho-mqtt` and `gunicorn`, test-only
  dependencies isolated in `requirements-dev.txt` **(Factor 2)**
- Logs, stdout only via `basicConfig` **(Factor 11)**

**Processes / disposability (VI, IX)**
- Stateless, share-nothing; durability delegated to the broker, no local queue or spool
- `connect_async` at startup, so a broker that is down does not prevent the service starting

**Port binding / concurrency (VII, VIII)**
- Dockerfile `CMD` runs gunicorn binding `0.0.0.0:5000` 
- gunicorn installs its own SIGTERM handler, so `docker stop` shuts workers down gracefully and the
  `atexit` cleanup runs 
- App factory → one `Publisher` per worker, so workers do not share an MQTT client id

**Build / release / run (V), dev/prod parity (X)**
- No configuration baked into the image; the same image runs anywhere, only the environment differs
- The container runs exactly what the image contains, no source mount, no command override

# AI usage

AI assistance (Claude, via Claude Code) was used, in these ways:

**Where it helped**
- Explaining the configuration surface for paho-mqtt and Mosquitto, and the trade-offs between QoS
  levels, `retain`, and broker persistence.
- Drafting the publisher and its tests, and the publisher-related route tests.

**References**
- paho-mqtt documentation — <https://pypi.org/project/paho-mqtt/>
- paho-mqtt client setup — <https://www.emqx.com/en/blog/how-to-use-mqtt-in-python>
- The Twelve-Factor App — <https://12factor.net/>