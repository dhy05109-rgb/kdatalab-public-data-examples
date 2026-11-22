#!/usr/bin/env python3
"""Export the Korean IPO calendar and apartment subscription (cheongyak) data to CSV.

Two Apify Actors behind one command:

* ``korea-ipo-calendar``    38.co.kr - subscription windows, book-building
  competition rates, lock-up commitments, final offer price, listing performance.
* ``korea-cheongyak-calendar`` applyhome.co.kr - sale notices, per-house-type
  prices, competition rates, award-score ranges and special-supply allocations.

    export APIFY_TOKEN=...
    python korea_ipo_cheongyak_export.py --market ipo --mode subscriptionSchedule --upcoming
    python korea_ipo_cheongyak_export.py --market cheongyak --mode competition --pages 5
    python korea_ipo_cheongyak_export.py --market both --max-items 200 --csv out/korea.csv
    python korea_ipo_cheongyak_export.py --demo

Actors: https://apify.com/livable_handloom/korea-ipo-calendar
        https://apify.com/livable_handloom/korea-cheongyak-calendar
Pricing: pay per event - $0.005 start + $0.010 per IPO record, $0.008 per cheongyak record.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

import kdatalab_client as kd

ACTORS = {
    "ipo": {
        "actor": "livable_handloom/korea-ipo-calendar",
        "label": "Korea IPO Calendar (38.co.kr)",
        "url": "https://apify.com/livable_handloom/korea-ipo-calendar",
        "modes": ["subscriptionSchedule", "demandForecastSchedule", "demandForecastResults", "newListings"],
        "default_mode": "subscriptionSchedule",
        "per_record_usd": 0.010,
        "columns": ["companyName", "mode", "subscriptionStart", "subscriptionEnd", "forecastStart", "forecastEnd",
                    "forecastDate", "listingDate", "offerPriceMin", "offerPriceMax", "finalOfferPrice",
                    "subscriptionCompetitionRate", "institutionCompetitionRate", "lockupCommitmentRatePct",
                    "offerPrice", "openPrice", "openVsOfferPct", "firstDayClosePrice", "currentPrice",
                    "vsOfferPricePct", "bookrunners", "status", "detailUrl"],
    },
    "cheongyak": {
        "actor": "livable_handloom/korea-cheongyak-calendar",
        "label": "Korea Cheongyak Home (applyhome.co.kr)",
        "url": "https://apify.com/livable_handloom/korea-cheongyak-calendar",
        "modes": ["announcements", "detail", "competition", "specialSupply"],
        "default_mode": "announcements",
        "per_record_usd": 0.008,
        "columns": ["houseName", "mode", "region", "noticeDate", "subscriptionStart", "subscriptionEnd",
                    "winnerAnnounceDate", "houseType", "exclusiveArea", "supplyArea", "generalSupplyHouseholds",
                    "supplyPriceManwon", "rank", "applicationRegion", "applications", "competitionRate",
                    "shortfallHouseholds", "minAwardScore", "maxAwardScore", "avgAwardScore", "builderName",
                    "specialSupplyType", "allocatedHouseholds", "appliedHouseholds", "houseManageNo", "pblancNo"],
    },
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Export Korean IPO or apartment-subscription data from Apify Actors to CSV/JSON.",
    )
    parser.add_argument("--market", choices=["ipo", "cheongyak", "both"], default="ipo",
                        help="Which dataset to export (default ipo)")
    parser.add_argument("--mode", help="Actor mode; see --list-modes. Default: the Actor's own default")
    parser.add_argument("--max-items", type=int, default=100, help="Hard cap on saved records (default 100)")
    parser.add_argument("--pages", type=int, default=3, help="Pages to walk, ~10-20 rows each (default 3)")
    parser.add_argument("--upcoming", action="store_true", help="IPO only: keep rows dated today or later")
    parser.add_argument("--details", action="store_true", help="Cheongyak: attach the parsed notice detail")
    parser.add_argument("--list-modes", action="store_true", help="Print the modes of each Actor and exit")
    parser.add_argument("--csv", metavar="PATH", help="CSV path (default out/korea_<market>_<date>.csv)")
    parser.add_argument("--json", action="store_true", help="print raw JSON instead of a table")
    parser.add_argument("--demo", action="store_true", help="render the bundled sample dataset (no token needed)")
    return parser.parse_args(argv)


def build_input(market, args):
    config = ACTORS[market]
    mode = args.mode or config["default_mode"]
    if mode not in config["modes"]:
        raise SystemExit("--mode %s is not a %s mode; choose one of: %s"
                         % (mode, market, ", ".join(config["modes"])))
    if market == "ipo":
        return {"mode": mode, "maxItems": args.max_items, "maxPages": args.pages, "onlyUpcoming": bool(args.upcoming)}
    return {"mode": mode, "maxItems": args.max_items, "maxPages": args.pages, "includeDetails": bool(args.details)}


def run_actor(market, args):
    config = ACTORS[market]
    if args.demo:
        payload = kd.load_sample("korea_ipo.json" if market == "ipo" else "korea_cheongyak.json")
        meta = kd.sample_meta(payload)
        print("[demo] no Apify token needed - this output comes from the bundled sample dataset", file=sys.stderr)
        if meta.get("note"):
            print("[demo] %s" % meta["note"], file=sys.stderr)
        print("[demo] actor: %s" % config["actor"], file=sys.stderr)
        print("[demo] input: %s" % json.dumps(build_input(market, args), ensure_ascii=False), file=sys.stderr)
        print(file=sys.stderr)
        return payload.get("items") or []
    if not os.environ.get(kd.APIFY_TOKEN_ENV):
        print("%s runs on Apify." % config["label"])
        print()
        print("  1. Open %s" % config["url"])
        print("  2. Sign in, then copy an API token: Apify Console -> Settings -> API & Integrations")
        print("  3. export APIFY_TOKEN='apify_api_...'")
        print()
        print("No token yet? Run the same command with --demo to see the output shape.")
        print()
        raise SystemExit(2)
    print("Running %s (mode=%s, up to %d records). A run usually takes 10-90 seconds..."
          % (config["label"], build_input(market, args).get("mode"), args.max_items), file=sys.stderr)
    try:
        return kd.apify_dataset(config["actor"], build_input(market, args))
    except kd.ApiError as exc:
        print("Run failed: %s" % exc)
        if exc.body:
            print("Response body: %s" % exc.body)
        raise SystemExit(1) from None


def columns_for(market, rows):
    seen, columns = set(), []
    for name in ACTORS[market]["columns"]:
        seen.add(name)
        columns.append(name)
    for row in rows:
        for key, value in row.items():
            if key in seen or isinstance(value, (dict, list)):
                continue
            seen.add(key)
            columns.append(key)
    return columns


def print_rows(market, rows, args):
    config = ACTORS[market]
    cost = 0.005 + len(rows) * config["per_record_usd"]
    print("Records: %d | estimated charge: $%.3f (start $0.005 + %d x $%.3f)"
          % (len(rows), cost, len(rows), config["per_record_usd"]))
    print()
    if market == "ipo":
        table = [[r.get("companyName"), kd.clip(r.get("modeLabel") or r.get("mode"), 16),
                  r.get("subscriptionStart") or r.get("forecastStart") or r.get("listingDate") or "-",
                  r.get("subscriptionEnd") or r.get("forecastEnd") or "-",
                  kd.num(r.get("offerPriceMin")), kd.num(r.get("offerPriceMax")),
                  kd.num(r.get("finalOfferPrice")),
                  kd.num(r.get("subscriptionCompetitionRate"), 2),
                  kd.num(r.get("institutionCompetitionRate"), 2),
                  kd.clip(r.get("bookrunners"), 18), r.get("status")] for r in rows]
        kd.print_table(["COMPANY", "MODE", "START", "END", "BAND LOW", "BAND HIGH", "FINAL", "RETAIL RATE",
                        "INST RATE", "BOOKRUNNER", "STATUS"], table,
                       widths=[16, 16, 10, 10, 9, 10, 8, 10, 9, 18, 8])
    else:
        table = [[r.get("houseName"), kd.clip(r.get("region"), 10), kd.clip(r.get("modeLabel") or r.get("mode"), 14),
                  r.get("noticeDate") or "-", kd.clip(r.get("houseType"), 12),
                  kd.num(r.get("generalSupplyHouseholds")), kd.num(r.get("supplyPriceManwon")),
                  kd.num(r.get("applications")), kd.num(r.get("competitionRate"), 2),
                  kd.clip(r.get("rank"), 6)] for r in rows]
        kd.print_table(["HOUSE", "REGION", "MODE", "NOTICE", "TYPE", "HOUSEHOLDS", "PRICE(만원)", "APPLIED",
                        "RATE", "RANK"], table, widths=[24, 10, 14, 10, 12, 10, 10, 8, 7, 6])


def export(market, rows, args, today):
    path = args.csv or ("out/korea_%s_%s.csv" % (market, today.strftime("%Y%m%d")))
    if args.csv and args.market == "both":
        stem, dot, extension = path.rpartition(".")
        path = "%s_%s.%s" % (stem, market, extension) if dot else "%s_%s" % (path, market)
    columns = columns_for(market, rows)
    kd.write_csv(path, columns, [[row.get(column) for column in columns] for row in rows])


def main(argv=None):
    args = parse_args(argv)
    if args.list_modes:
        for name, config in ACTORS.items():
            print("%-10s %s" % (name, ", ".join(config["modes"])))
        return 0

    today = dt.date.today()
    markets = ["ipo", "cheongyak"] if args.market == "both" else [args.market]
    collected = {}
    for market in markets:
        if len(markets) > 1 and not args.json:
            print("=== %s ===" % ACTORS[market]["label"])
        rows = run_actor(market, args)
        collected[market] = rows
        if not args.json:
            print_rows(market, rows, args)
        if rows and (args.csv or not args.demo):
            export(market, rows, args, today)
    if args.json:
        kd.dump_json(collected if len(markets) > 1 else collected[markets[0]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
