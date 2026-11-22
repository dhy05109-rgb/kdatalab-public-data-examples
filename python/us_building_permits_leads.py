#!/usr/bin/env python3
"""US building-permit leads from five city open-data portals.

NYC, Chicago, Austin, Seattle and San Francisco permits, normalised into one
schema (permit number, work type, issued date, construction cost, address,
contractor) and ranked with a simple lead score so a sales team can start from
the biggest jobs.

    export RAPIDAPI_KEY=...
    python us_building_permits_leads.py --cities nyc,chicago --days 14 --min-cost 100000
    python us_building_permits_leads.py --keyword solar --work-type renovation
    python us_building_permits_leads.py --source apify --min-cost 250000   # needs APIFY_TOKEN
    python us_building_permits_leads.py --demo

API: US Building Permits API (RapidAPI)
     https://rapidapi.com/김태욱/api/us-building-permits-api4
Apify: https://apify.com/livable_handloom/us-building-permits-scraper
Privacy: owner and applicant names, emails, phones and unit numbers are removed
before a record reaches you; company names are kept.
"""

from __future__ import annotations

import argparse
import math

import kdatalab_client as kd

HOST = "us-building-permits-api4.p.rapidapi.com"
SIGNUP_URL = "https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-building-permits-api4"
APIFY_ACTOR = "livable_handloom/us-building-permits-scraper"
SAMPLE = "us_permits.json"

CITIES = ["nyc", "chicago", "austin", "seattle", "sanfrancisco"]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Find and rank US building permits as sales leads.",
    )
    parser.add_argument("--source", choices=["rapidapi", "apify"], default="rapidapi",
                        help="rapidapi (default) or apify")
    parser.add_argument("--cities", default=",".join(CITIES),
                        help="Comma-separated: " + ",".join(CITIES))
    parser.add_argument("--days", type=int, default=14, help="Look-back window in days (default 14)")
    parser.add_argument("--min-cost", type=float, default=0.0, help="Minimum construction cost in USD")
    parser.add_argument("--keyword", help="Free-text filter on the job description")
    parser.add_argument("--work-type", default="all",
                        help="all, new_construction, renovation, demolition, trade, other (default all)")
    parser.add_argument("--limit", type=int, default=20, help="Rows to request (default 20)")
    kd.add_output_args(parser)
    return parser.parse_args(argv)


def fetch(args):
    label = "The US Building Permits API"
    if args.source == "apify":
        if args.demo:
            raise SystemExit("--demo only covers the RapidAPI path; drop --source apify to see the sample")
        run_input = {
            "cities": [c.strip() for c in args.cities.split(",") if c.strip()],
            "daysBack": args.days,
            "minEstimatedCost": args.min_cost or 0,
            "keyword": args.keyword or "",
            "permitType": "" if args.work_type == "all" else args.work_type,
            "maxResults": args.limit,
        }
        print("Running the US building-permits Actor on Apify...")
        try:
            return {"data": kd.apify_dataset(APIFY_ACTOR, run_input), "meta": {"source": "apify"}}
        except kd.ApiError as exc:
            print("Run failed: %s" % exc)
            if exc.body:
                print("Response body: %s" % exc.body)
            raise SystemExit(1) from None
    params = {"cities": args.cities, "daysBack": args.days, "minEstimatedCost": args.min_cost or None,
              "keyword": args.keyword, "workType": args.work_type, "limit": args.limit}
    return kd.fetch(args, HOST, "/us/permits", params, SAMPLE, label, SIGNUP_URL)


def lead_score(permit):
    """A transparent 0-100 heuristic - edit it for your own sales motion.

    * construction value: up to 55 points (log scale, $1k -> ~12, $1M -> ~55)
    * work type: new construction +20, renovation +12, trade +6
    * a named contractor: +10 (someone to call)
    * multi-unit or large floor area: +8
    """
    cost = permit.get("estimatedCost") or 0
    score = min(55.0, 12.0 * math.log10(cost / 1000.0 + 1.0)) if cost > 0 else 0.0
    score += {"new_construction": 20, "renovation": 12, "trade": 6}.get(permit.get("workType"), 0)
    if permit.get("contractorCompany"):
        score += 10
    if (permit.get("units") or 0) >= 5 or (permit.get("floorAreaSqft") or 0) >= 2000:
        score += 8
    return min(100, round(score))


def render(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    if args.min_cost:
        rows = [r for r in rows if (r.get("estimatedCost") or 0) >= args.min_cost]
    rows = sorted(rows, key=lambda r: lead_score(r), reverse=True)

    print("Cities: %s | last %s days | showing %s permit(s)"
          % (meta.get("cities") or args.cities, meta.get("daysBack", args.days), len(rows)))
    if meta.get("rowsScanned"):
        print("Scanned %s rows upstream" % meta["rowsScanned"])
    print()

    kd.print_table(["SCORE", "ISSUED", "CITY", "TYPE", "COST", "ADDRESS", "CONTRACTOR"],
                   [[lead_score(r), r.get("issuedDate") or "-", kd.clip(r.get("cityName") or r.get("city"), 14),
                     kd.clip(r.get("workType"), 14), kd.money(r.get("estimatedCost")),
                     kd.clip(r.get("streetAddress"), 30), kd.clip(r.get("contractorCompany"), 26)] for r in rows],
                   widths=[5, 10, 14, 14, 9, 30, 26])
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv,
                     ["score", "city", "permitNumber", "workType", "permitType", "status", "issuedDate",
                      "estimatedCost", "streetAddress", "zip", "contractorCompany", "contractorRole", "units",
                      "floorAreaSqft", "recordUrl"],
                     [[lead_score(r), r.get("city"), r.get("permitNumber"), r.get("workType"), r.get("permitType"),
                       r.get("status"), r.get("issuedDate"), r.get("estimatedCost"), r.get("streetAddress"),
                       r.get("zip"), r.get("contractorCompany"), r.get("contractorRole"), r.get("units"),
                       r.get("floorAreaSqft"), r.get("recordUrl")] for r in rows])


def main(argv=None):
    args = parse_args(argv)
    payload = fetch(args)
    if args.json:
        kd.dump_json(payload)
        return 0
    render(payload, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
