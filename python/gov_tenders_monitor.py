#!/usr/bin/env python3
"""Monitor UK, Australian and EU public procurement notices from the terminal.

Three sources, one table:

* UK  Contracts Finder + Find a Tender (RapidAPI or Apify)
* AU  AusTender OCDS contract notices (RapidAPI or Apify)
* EU  TED contract and award notices (RapidAPI)

Filter by keyword, stage, value and deadline, then export to CSV. Useful for
B2B sales teams, bid writers, suppliers expanding into a new market, and
analysts tracking public spending.

    export RAPIDAPI_KEY=...
    python gov_tenders_monitor.py --region all --keyword solar --days 30
    python gov_tenders_monitor.py --region uk --stage award --min-value 1000000
    python gov_tenders_monitor.py --region au --keyword ICT --csv out/au_tenders.csv
    python gov_tenders_monitor.py --demo

APIs (RapidAPI):
  UK/AU  https://rapidapi.com/김태욱/api/uk-australia-government-tenders-api
  EU     https://rapidapi.com/김태욱/api/eu-ted-public-procurement-api
Apify Actors:
  https://apify.com/livable_handloom/uk-tenders-scraper
  https://apify.com/livable_handloom/austender-procurement-scraper
"""

from __future__ import annotations

import argparse

import kdatalab_client as kd

HOST_UK_AU = "uk-australia-government-tenders-api.p.rapidapi.com"
HOST_EU = "eu-ted-public-procurement-api.p.rapidapi.com"
SIGNUP_UK_AU = "https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/uk-australia-government-tenders-api"
SIGNUP_EU = "https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/eu-ted-public-procurement-api"

APIFY_ACTORS = {
    "uk": "livable_handloom/uk-tenders-scraper",
    "au": "livable_handloom/austender-procurement-scraper",
}

SAMPLES = {"uk": "tenders_uk.json", "au": "tenders_au.json", "eu": "tenders_eu.json"}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Search UK, Australian and EU public tender notices.",
        epilog="Values are published amounts, not guaranteed contract values.",
    )
    parser.add_argument("--region", choices=["uk", "au", "eu", "all"], default="all",
                        help="Market to query (default all)")
    parser.add_argument("--keyword", help="Free-text keyword filter")
    parser.add_argument("--days", type=int, default=30, help="Look-back window in days (default 30)")
    parser.add_argument("--stage", choices=["tender", "award", "planning", "all"], default="tender",
                        help="UK only: procurement stage (default tender)")
    parser.add_argument("--min-value", type=float, default=0.0, help="Drop rows below this amount (default 0)")
    parser.add_argument("--limit", type=int, default=20, help="Rows per region (default 20)")
    parser.add_argument("--source", choices=["rapidapi", "apify"], default="rapidapi",
                        help="rapidapi (default) or apify; apify supports uk/au only")
    kd.add_output_args(parser)
    return parser.parse_args(argv)


# --------------------------------------------------------------------------- #
# RapidAPI
# --------------------------------------------------------------------------- #

def fetch_region(args, region):
    if region == "uk":
        params = {"keyword": args.keyword, "stage": args.stage, "days": args.days, "limit": args.limit}
        payload = kd.fetch(args, HOST_UK_AU, "/uk/tenders", params, SAMPLES["uk"],
                           "The UK & Australia Tenders API", SIGNUP_URL_UK_AU)
    elif region == "au":
        params = {"keyword": args.keyword, "daysBack": args.days, "limit": args.limit}
        payload = kd.fetch(args, HOST_UK_AU, "/au/tenders", params, SAMPLES["au"],
                           "The UK & Australia Tenders API", SIGNUP_URL_UK_AU)
    else:
        params = {"keyword": args.keyword, "days": args.days, "limit": args.limit}
        payload = kd.fetch(args, HOST_EU, "/eu/tenders", params, SAMPLES["eu"],
                           "The EU TED Procurement API", SIGNUP_URL_EU)
    return payload.get("data") or [], payload.get("meta") or {}


# --------------------------------------------------------------------------- #
# Apify
# --------------------------------------------------------------------------- #

def run_apify(args, region):
    actor = APIFY_ACTORS[region]
    if region == "uk":
        run_input = {"keyword": args.keyword or "", "stage": args.stage, "maxItems": args.limit}
        if args.days:
            from datetime import date, timedelta
            run_input["publishedFrom"] = (date.today() - timedelta(days=args.days)).isoformat()
    else:
        run_input = {"keyword": args.keyword or "", "daysBack": args.days, "maxItems": args.limit,
                     "tenderTypes": ["atm", "cn"]}
    print("Running %s as an Apify Actor..." % region.upper())
    try:
        return kd.apify_dataset(actor, run_input)
    except kd.ApiError as exc:
        print("Run failed: %s" % exc)
        if exc.body:
            print("Response body: %s" % exc.body)
        raise SystemExit(1) from None


# --------------------------------------------------------------------------- #
# Normalisation
# --------------------------------------------------------------------------- #

def normalise(region, rows):
    out = []
    for row in rows:
        if region == "uk":
            out.append({
                "region": "UK", "id": row.get("ocid") or row.get("noticeId"),
                "published": row.get("publishedDate"),
                "deadline": (row.get("deadlineDate") or "")[:10] or None,
                "buyer": row.get("buyerName"), "title": row.get("title"),
                "value": row.get("valueAmount"), "currency": row.get("valueCurrency") or "GBP",
                "url": row.get("noticeUrl"),
            })
        elif region == "au":
            out.append({
                "region": "AU", "id": row.get("id") or row.get("ocid"),
                "published": (row.get("publishDate") or row.get("contractPublished") or "")[:10] or None,
                "deadline": (row.get("closingDate") or row.get("closeDate") or row.get("deadlineDate") or "")[:10] or None,
                "buyer": row.get("agency") or row.get("buyerName"), "title": row.get("title"),
                "value": row.get("value") if row.get("value") is not None else row.get("valueAmount"),
                "currency": row.get("currency") or "AUD",
                "url": row.get("noticeUrl") or row.get("url"),
            })
        else:
            out.append({
                "region": "EU", "id": row.get("publicationNumber"),
                "published": row.get("publicationDate"),
                "deadline": row.get("deadlineDate"),
                "buyer": row.get("buyerName"), "title": row.get("title"),
                "value": row.get("totalValue") if row.get("totalValue") is not None else row.get("estimatedValue"),
                "currency": row.get("currency") or "EUR",
                "url": row.get("tedUrl"),
            })
    return out


def render(rows, args):
    rows = sorted(rows, key=lambda r: (r.get("published") or ""), reverse=True)
    if args.min_value:
        rows = [r for r in rows if (r.get("value") or 0) >= args.min_value]
    table = [[
        r.get("region", "-"),
        r.get("published") or "-",
        r.get("deadline") or "-",
        kd.clip(r.get("buyer"), 24),
        kd.money(r.get("value"), currency=""),
        (r.get("currency") or "")[:3],
        kd.clip(r.get("title"), 56),
    ] for r in rows]
    kd.print_table(["REG", "PUBLISHED", "DEADLINE", "BUYER", "VALUE", "CUR", "TITLE"], table,
                   widths=[4, 10, 10, 24, 9, 4, 56])
    print("\n%d notice(s)" % len(rows))

    if args.csv:
        kd.write_csv(args.csv, ["region", "id", "published", "deadline", "buyer", "title", "value", "currency", "url"],
                     [[r.get("region"), r.get("id"), r.get("published"), r.get("deadline"), r.get("buyer"),
                       r.get("title"), r.get("value"), r.get("currency"), r.get("url")] for r in rows])


def main(argv=None):
    args = parse_args(argv)
    regions = ["uk", "au", "eu"] if args.region == "all" else [args.region]
    if args.source == "apify" and args.region == "eu":
        raise SystemExit("EU TED is sold through RapidAPI; use --source rapidapi for --region eu")

    rows, warnings = [], []
    for region in regions:
        if args.demo:
            payload = kd.load_sample(SAMPLES[region])
            kd.demo_banner(
                HOST_EU if region == "eu" else HOST_UK_AU,
                {"uk": "/uk/tenders", "au": "/au/tenders", "eu": "/eu/tenders"}[region],
                {"keyword": args.keyword, "days": args.days, "limit": args.limit},
                SAMPLES[region], payload,
            )
            data, meta = payload.get("data") or [], payload.get("meta") or {}
        elif args.source == "apify":
            data = run_apify(args, region)
            meta = {}
        else:
            data, meta = fetch_region(args, region)
        rows.extend(normalise(region, data))
        warnings.extend(meta.get("warnings") or [])

    if args.json:
        kd.dump_json(rows)
        return 0
    render(rows, args)
    for message in warnings:
        print("! %s" % message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
