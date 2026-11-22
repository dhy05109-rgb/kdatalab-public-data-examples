"""Tiny zero-dependency client for the K-Data Lab APIs.

Works with the standard library only (Python 3.9+), so a reader can copy one
script out of this repository and run it without installing anything.

Two kinds of access are covered:

* RapidAPI gateway  -> ``rapidapi(host, path, params)`` needs ``RAPIDAPI_KEY``.
* Apify Actor runs  -> ``apify_dataset(actor, run_input)`` needs ``APIFY_TOKEN``.

Every example script also has a ``--demo`` mode that renders a bundled sample
response, so the code can be tried before signing up for anything.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAPIDAPI_KEY_ENV = "RAPIDAPI_KEY"
APIFY_TOKEN_ENV = "APIFY_TOKEN"

ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "samples"

DEFAULT_TIMEOUT = 60
USER_AGENT = "kdatalab-examples/1.0 (+https://github.com/kdatalab)"


class ApiError(RuntimeError):
    """An HTTP or transport error from the API."""

    def __init__(self, message, status=None, body=None, url=None):
        super().__init__(message)
        self.status = status
        self.body = body
        self.url = url


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

def _request_json(url, headers, timeout):
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:800]
        raise ApiError(
            "HTTP %s from %s" % (exc.code, urllib.parse.urlsplit(url).netloc),
            status=exc.code,
            body=body,
            url=url,
        ) from None
    except urllib.error.URLError as exc:
        raise ApiError("network error: %s" % exc.reason, url=url) from None
    except TimeoutError:
        raise ApiError("request timed out after %ss" % timeout, url=url) from None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise ApiError("response was not JSON", body=raw[:300].decode("utf-8", "replace"), url=url) from None


def rapidapi(host, path, params=None, key=None, timeout=DEFAULT_TIMEOUT):
    """GET https://{host}{path} through the RapidAPI gateway."""
    key = key or os.environ.get(RAPIDAPI_KEY_ENV)
    if not key:
        raise ApiError("RAPIDAPI_KEY is not set")
    query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v not in (None, "")})
    url = "https://%s%s%s" % (host, path, ("?" + query) if query else "")
    headers = {
        "X-RapidAPI-Key": key,
        "X-RapidAPI-Host": host,
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    return _request_json(url, headers, timeout)


def apify_dataset(actor, run_input=None, token=None, timeout=300):
    """Run an Apify Actor synchronously and return its dataset items.

    ``actor`` is ``"owner/actor-name"`` (or ``owner~actor-name``).
    The synchronous endpoint waits for the run, so no polling loop is needed;
    a long run ends with HTTP 408 and should be started asynchronously instead.
    """
    token = token or os.environ.get(APIFY_TOKEN_ENV)
    if not token:
        raise ApiError("APIFY_TOKEN is not set")
    actor_id = actor.replace("/", "~")
    query = urllib.parse.urlencode({"token": token, "timeout": timeout, "format": "json"})
    url = "https://api.apify.com/v2/acts/%s/run-sync-get-dataset-items?%s" % (actor_id, query)
    body = json.dumps(run_input or {}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout + 30) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:800]
        raise ApiError("Apify run failed (HTTP %s)" % exc.code, status=exc.code, body=detail, url=url) from None
    except urllib.error.URLError as exc:
        raise ApiError("network error: %s" % exc.reason, url=url) from None
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        raise ApiError("Apify returned a non-JSON body", body=raw[:300].decode("utf-8", "replace"), url=url) from None
    if not isinstance(items, list):
        raise ApiError("Apify returned an unexpected payload", body=str(items)[:300], url=url)
    return items


# --------------------------------------------------------------------------- #
# Samples and demo mode
# --------------------------------------------------------------------------- #

def load_sample(name):
    path = SAMPLES_DIR / name
    if not path.exists():
        raise SystemExit("sample file missing: %s" % path)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sample_meta(payload):
    meta = payload.get("_sample") if isinstance(payload, dict) else None
    return meta or {}


def demo_banner(host, path, params, sample_name, payload):
    meta = sample_meta(payload)
    query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v not in (None, "")})
    banner = sys.stderr
    print("[demo] no API key needed - this output comes from samples/%s" % sample_name, file=banner)
    if meta.get("note"):
        print("[demo] %s" % meta["note"], file=banner)
    print("[demo] live request would be:", file=banner)
    print("       curl -s \"https://%s%s%s\" -H \"X-RapidAPI-Key: $RAPIDAPI_KEY\" -H \"X-RapidAPI-Host: %s\""
          % (host, path, ("?" + query) if query else "", host), file=banner)
    print(file=banner)


def print_guidance(label, signup_url, env_name=RAPIDAPI_KEY_ENV, demo_hint=True):
    print("%s needs a key." % label)
    print()
    print("  1. Open %s" % signup_url)
    print("  2. Subscribe to the free BASIC plan (100 requests/month).")
    print("  3. export %s='your-key'" % env_name)
    if demo_hint:
        print()
        print("No key yet? Run the same command with --demo to see a sample response.")
    print()


def require_host(host, label):
    """Stop with a clear message while a host is still a bracketed placeholder."""
    if host.startswith("[") and host.endswith("]"):
        print("%s is not published yet (host placeholder %s)." % (label, host))
        print("Replace the marker once the listing is live - see PLACEHOLDERS.md.")
        print("Use --demo to see the response shape in the meantime.")
        raise SystemExit(3)


def fetch(args, host, path, params, sample, label, signup_url, timeout=DEFAULT_TIMEOUT):
    """Return a payload from the sample (--demo) or from the live API."""
    if getattr(args, "demo", False):
        payload = load_sample(sample)
        demo_banner(host, path, params, sample, payload)
        return payload
    if not os.environ.get(RAPIDAPI_KEY_ENV):
        print_guidance(label, signup_url)
        raise SystemExit(2)
    require_host(host, label)
    try:
        return rapidapi(host, path, params, timeout=timeout)
    except ApiError as exc:
        print("Request failed: %s" % exc)
        if exc.body:
            print("Response body: %s" % exc.body)
        raise SystemExit(1) from None


# --------------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------------- #

def num(value, digits=0, dash="-"):
    if value is None or value == "":
        return dash
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if digits == 0:
        return "{:,.0f}".format(number)
    return "{:,.{}f}".format(number, digits)


def money(value, currency="$", dash="-"):
    if value is None or value == "":
        return dash
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    sign = "-" if number < 0 else ""
    number = abs(number)
    if number >= 1_000_000_000:
        body = "{:.2f}B".format(number / 1_000_000_000)
    elif number >= 1_000_000:
        body = "{:.2f}M".format(number / 1_000_000)
    elif number >= 10_000:
        body = "{:.1f}K".format(number / 1_000)
    else:
        body = "{:,.0f}".format(number)
    return "%s%s%s" % (sign, currency, body)


def pct(value, signed=False, dash="-"):
    if value is None or value == "":
        return dash
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    pattern = "{:+.2f}%" if signed else "{:.2f}%"
    return pattern.format(number)


def clip(text, width=60, dash="-"):
    if text is None or text == "":
        return dash
    text = " ".join(str(text).split())
    return text if len(text) <= width else text[: width - 1] + "…"


def _display_width(text):
    """Terminal columns used by a string (CJK characters take two)."""
    return sum(2 if unicodedata.east_asian_width(char) in ("W", "F") else 1 for char in text)


def _fit(text, width):
    if _display_width(text) <= width:
        return text + " " * (width - _display_width(text))
    kept, used = [], 0
    for char in text:
        char_width = 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
        if used + char_width > width - 1:
            break
        kept.append(char)
        used += char_width
    return "".join(kept) + " " * (width - used - 1) + "…"


def print_table(headers, rows, widths=None):
    """Print a plain ASCII table that stays readable in a terminal and in CI logs."""
    rows = [[("" if cell is None else str(cell)) for cell in row] for row in rows]
    if not rows:
        print("(no rows)")
        return
    if widths is None:
        widths = []
        for index, header in enumerate(headers):
            column = [_display_width(header)] + [_display_width(row[index]) for row in rows if index < len(row)]
            widths.append(min(max(column), 56))

    def line(cells):
        parts = []
        for index, cell in enumerate(cells):
            parts.append(_fit(cell, widths[index]))
        return "  ".join(parts).rstrip()

    print(line(headers))
    print(line(["-" * width for width in widths]))
    for row in rows:
        print(line(row))


def print_kv(pairs):
    label_width = max((len(str(key)) for key, _ in pairs), default=0)
    for key, value in pairs:
        print("  %-*s  %s" % (label_width, key, "" if value is None else value))


def warning_lines(meta):
    warnings = (meta or {}).get("warnings") or []
    for message in warnings:
        print("! %s" % message)


def write_csv(path, headers, rows):
    target = Path(path)
    if target.parent and str(target.parent) not in ("", "."):
        target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([_flat(cell) for cell in row])
    print("\nSaved %d rows to %s" % (len(rows), target))


def _flat(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "|".join(_flat(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return value


def add_output_args(parser):
    parser.add_argument("--demo", action="store_true",
                        help="render a bundled sample response instead of calling the API (no key needed)")
    parser.add_argument("--json", action="store_true", help="print the raw JSON response instead of a table")
    parser.add_argument("--csv", metavar="PATH", help="also write the rows to a CSV file")
    return parser


def dump_json(payload):
    print(json.dumps(payload, indent=2, ensure_ascii=False))
