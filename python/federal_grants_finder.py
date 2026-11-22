#!/usr/bin/env python3
"""US federal research funding finder (NIH RePORTER + NSF + Grants.gov).

Answers two questions from one API:

* who already won money for a topic (``--mode awards``)
* what is open to apply for right now (``--mode opportunities``)

and a merged feed of both (``--mode feed``). Handy for grant prospecting,
competitor research on a research field, and startup R&D landscaping.

    export RAPIDAPI_KEY=...
    python federal_grants_finder.py --keyword crispr --source nih --limit 10
    python federal_grants_finder.py --mode opportunities --keyword quantum
    python federal_grants_finder.py --mode feed --keyword battery --csv out/grants.csv
    python federal_grants_finder.py --demo

API: US Federal Grants & R&D Awards API (RapidAPI)
     https://rapidapi.com/김태욱/api/us-federal-grants-r-d-awards-api
Data: NIH RePORTER, NSF Awards API, Grants.gov Search2 (all public, no key upstream).
"""

from __future__ import annotations

import argparse

import kdatalab_client as kd

HOST = "us-federal-grants-r-d-awards-api.p.rapidapi.com"
SIGNUP_URL = "https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-federal-grants-r-d-awards-api"
SAMPLE_AWARDS = "grants_awards.json"
SAMPLE_OPPORTUNITIES = "grants_opportunities.json"
SAMPLE_FEED = "grants_feed.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Search funded US research awards and open federal funding opportunities.",
    )
    parser.add_argument("--mode", choices=["awards", "opportunities", "feed"], default="awards",
                        help="awards (default), opportunities, or feed")
    parser.add_argument("--keyword", default="crispr", help="Search text (default: crispr)")
    parser.add_argument("--source", choices=["all", "nih", "nsf"], default="all",
                        help="Awards: which funder (default all)")
    parser.add_argument("--fiscal-year", type=int, help="Awards: federal fiscal year, e.g. 2026")
    parser.add_argument("--min-amount", type=float, help="Awards: minimum amount in USD")
    parser.add_argument("--status", choices=["posted", "forecasted", "all"], default="posted",
                        help="Opportunities: posted, forecasted, or all (default posted)")
    parser.add_argument("--limit", type=int, default=15, help="Rows to request (default 15)")
    kd.add_output_args(parser)
    return parser.parse_args(argv)


def fetch(args):
    if args.mode == "opportunities":
        params = {"keyword": args.keyword, "status": args.status, "limit": args.limit}
        return kd.fetch(args, HOST, "/opportunities", params, SAMPLE_OPPORTUNITIES,
                        "The US Federal Grants API", SIGNUP_URL)
    if args.mode == "feed":
        params = {"keyword": args.keyword, "limit": args.limit}
        return kd.fetch(args, HOST, "/feed", params, SAMPLE_FEED,
                        "The US Federal Grants API", SIGNUP_URL)
    params = {"keyword": args.keyword, "source": args.source, "fiscalYear": args.fiscal_year,
              "minAmount": args.min_amount, "limit": args.limit}
    return kd.fetch(args, HOST, "/awards/search", params, SAMPLE_AWARDS,
                    "The US Federal Grants API", SIGNUP_URL)


def render_awards(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    totals = meta.get("totalMatches") or {}
    print("Keyword %r | matches upstream: NIH %s, NSF %s | showing %s"
          % (meta.get("keyword"), totals.get("nih", "-"), totals.get("nsf", "-"), len(rows)))
    print("Amount basis: NIH = that fiscal year's award, NSF = estimated total award.")
    print()

    table = [[
        row.get("source", "-"),
        kd.clip(row.get("title"), 52),
        kd.clip(row.get("organization"), 26),
        kd.clip(row.get("piName"), 16),
        kd.money(row.get("amountUsd")),
        row.get("fiscalYear") or "-",
    ] for row in rows]
    kd.print_table(["FUNDER", "AWARD TITLE", "ORGANIZATION", "PI", "AMOUNT", "FY"], table,
                   widths=[7, 52, 26, 16, 9, 5])
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv,
                     ["source", "id", "title", "organization", "agency", "piName", "amountUsd", "amountBasis",
                      "fiscalYear", "startDate", "endDate", "url"],
                     [[r.get("source"), r.get("id"), r.get("title"), r.get("organization"), r.get("agency"),
                       r.get("piName"), r.get("amountUsd"), r.get("amountBasis"), r.get("fiscalYear"),
                       r.get("startDate"), r.get("endDate"), r.get("url")] for r in rows])


def render_opportunities(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    print("Keyword %r | status %s | showing %s"
          % (meta.get("keyword"), meta.get("status", args.status), len(rows)))
    print()
    table = [[
        kd.clip(row.get("title"), 54),
        kd.clip(row.get("agency"), 24),
        (row.get("openDate") or "-")[:10],
        (row.get("closeDate") or "-")[:10],
        row.get("daysToClose") if row.get("daysToClose") is not None else "-",
    ] for row in rows]
    kd.print_table(["OPPORTUNITY", "AGENCY", "OPENS", "CLOSES", "DAYS LEFT"], table,
                   widths=[54, 24, 10, 10, 9])
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv,
                     ["opportunityId", "number", "title", "agency", "status", "openDate", "closeDate",
                      "daysToClose", "url"],
                     [[r.get("opportunityId"), r.get("number"), r.get("title"), r.get("agency"), r.get("status"),
                       r.get("openDate"), r.get("closeDate"), r.get("daysToClose"), r.get("url")] for r in rows])


def render_feed(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    print("Keyword %r | awards + opportunities merged, showing %s" % (meta.get("keyword"), len(rows)))
    print()
    table = []
    for row in rows:
        kind = row.get("recordType", "-")
        if kind == "award":
            extra = "%s | %s" % (kd.clip(row.get("organization"), 24), kd.money(row.get("amountUsd")))
        else:
            close = (row.get("closeDate") or "-")[:10]
            extra = "%s | closes %s" % (kd.clip(row.get("agency"), 24), close)
        table.append([kind, kd.clip(row.get("title"), 54), extra])
    kd.print_table(["RECORD", "TITLE", "DETAIL"], table, widths=[9, 54, 44])
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv,
                     ["recordType", "title", "organization", "agency", "amountUsd", "closeDate", "url"],
                     [[r.get("recordType"), r.get("title"), r.get("organization"), r.get("agency"),
                       r.get("amountUsd"), r.get("closeDate"), r.get("url")] for r in rows])


def main(argv=None):
    args = parse_args(argv)
    payload = fetch(args)
    if args.json:
        kd.dump_json(payload)
        return 0
    if args.mode == "opportunities":
        render_opportunities(payload, args)
    elif args.mode == "feed":
        render_feed(payload, args)
    else:
        render_awards(payload, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
