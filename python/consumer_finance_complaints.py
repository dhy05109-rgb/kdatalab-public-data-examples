#!/usr/bin/env python3
"""US consumer-finance complaint and fair-lending explorer (CFPB + HMDA).

Four views over the CFPB Consumer Complaint Database and the HMDA mortgage
lending data:

* ``complaints``  individual complaints for a company, product, issue or state
* ``trending``    companies whose complaint volume rose against the prior period
* ``benchmark``   complaint share by product, with the top issues and companies
* ``company``     one company's complaint profile plus its HMDA denial rate

Typical uses: fintech competitor monitoring, compliance early warning, sales
signals for vendors serving banks, and fair-lending research.

    export RAPIDAPI_KEY=...
    python consumer_finance_complaints.py --company "JPMORGAN CHASE & CO." --product Mortgage
    python consumer_finance_complaints.py --mode trending --min-volume 100
    python consumer_finance_complaints.py --mode benchmark --product "Credit card"
    python consumer_finance_complaints.py --demo

API: US Consumer Finance Complaint & Fair-Lending API (RapidAPI)
     https://rapidapi.com/김태욱/api/us-consumer-finance-complaint-fair-lending-api
Data: CFPB Consumer Complaint Database (CC0) + FFIEC HMDA Data Browser (public).
"""

from __future__ import annotations

import argparse

import kdatalab_client as kd

# RapidAPI 10 (CFPB complaints + HMDA) gateway host — the listing is live.
HOST = "us-consumer-finance-complaint-fair-lending-api.p.rapidapi.com"
SIGNUP_URL = "https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-consumer-finance-complaint-fair-lending-api"
SAMPLE_COMPLAINTS = "cfpb_complaints.json"
SAMPLE_TRENDING = "cfpb_trending.json"
SAMPLE_BENCHMARK = "cfpb_benchmark.json"
SAMPLE_COMPANY = "cfpb_company.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Explore CFPB consumer complaints and HMDA mortgage denial rates.",
    )
    parser.add_argument("--mode", choices=["complaints", "trending", "benchmark", "company"],
                        default="complaints", help="View to run (default complaints)")
    parser.add_argument("--company", default="JPMORGAN CHASE & CO.",
                        help="Complaints: exact CFPB company name (use --mode company to resolve one)")
    parser.add_argument("--product", help="Product filter, e.g. 'Mortgage', 'Credit card', 'Checking or savings account'")
    parser.add_argument("--issue", help="Issue filter, e.g. 'Trouble during payment process'")
    parser.add_argument("--state", help="Two-letter state code")
    parser.add_argument("--days", type=int, default=90, help="Look-back window in days (default 90)")
    parser.add_argument("--limit", type=int, default=10, help="Rows to request (default 10)")
    kd.add_output_args(parser)
    return parser.parse_args(argv)


def fetch(args):
    if args.mode == "trending":
        params = {"days": args.days, "product": args.product, "state": args.state,
                  "minVolume": 25, "limit": args.limit}
        return kd.fetch(args, HOST, "/companies/trending", params, SAMPLE_TRENDING,
                        "The US Consumer Finance API (RapidAPI 10)", SIGNUP_URL)
    if args.mode == "benchmark":
        params = {"product": args.product, "days": args.days, "limit": args.limit}
        return kd.fetch(args, HOST, "/products/benchmark", params, SAMPLE_BENCHMARK,
                        "The US Consumer Finance API (RapidAPI 10)", SIGNUP_URL)
    if args.mode == "company":
        params = {"name": args.company, "days": args.days, "includeLending": "true"}
        return kd.fetch(args, HOST, "/company", params, SAMPLE_COMPANY,
                        "The US Consumer Finance API (RapidAPI 10)", SIGNUP_URL)
    params = {"company": args.company, "product": args.product, "issue": args.issue,
              "state": args.state, "days": args.days, "limit": args.limit}
    return kd.fetch(args, HOST, "/complaints", params, SAMPLE_COMPLAINTS,
                    "The US Consumer Finance API (RapidAPI 10)", SIGNUP_URL)


def render_complaints(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    window = meta.get("window") or {}
    freshness = meta.get("dataFreshness") or {}
    print("Company %r | product %s | %s to %s | showing %s of %s matches"
          % (meta.get("company"), meta.get("product") or "all",
             window.get("from", "-"), window.get("to", "-"), len(rows), meta.get("totalMatches", "?")))
    last_updated = (freshness.get("lastUpdated") or "-")
    print("CFPB publishes after the company responds (or 15 days), so the newest day or two are still incomplete. "
          "Last update: %s" % last_updated)
    print()

    kd.print_table(["DATE", "COMPANY", "PRODUCT", "ISSUE", "ST", "RESPONSE"],
                   [[r.get("dateReceived"), kd.clip(r.get("company"), 26), kd.clip(r.get("product"), 18),
                     kd.clip(r.get("issue"), 34), r.get("state"), kd.clip(r.get("companyResponse"), 20)]
                    for r in rows], widths=[10, 26, 18, 34, 3, 20])
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv,
                     ["id", "dateReceived", "company", "product", "subProduct", "issue", "subIssue", "state",
                      "zipCode", "companyResponse", "timely", "url"],
                     [[r.get("id"), r.get("dateReceived"), r.get("company"), r.get("product"), r.get("subProduct"),
                       r.get("issue"), r.get("subIssue"), r.get("state"), r.get("zipCode"),
                       r.get("companyResponse"), r.get("timely"), r.get("url")] for r in rows])


def render_trending(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    recent = meta.get("recent") or {}
    print("Complaint volume change | %s to %s vs the prior period | showing %s"
          % (recent.get("from", "-"), recent.get("to", "-"), len(rows)))
    print()
    kd.print_table(["COMPANY", "RECENT", "PRIOR", "CHANGE", "CHANGE %", "SHARE"],
                   [[kd.clip(r.get("company"), 44), kd.num(r.get("recentComplaints")), kd.num(r.get("priorComplaints")),
                     kd.num(r.get("change")), kd.pct(r.get("changePct"), signed=True), kd.pct(r.get("shareOfRecentPct"))]
                    for r in rows], widths=[44, 9, 9, 9, 9, 7])
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv, ["company", "recentComplaints", "priorComplaints", "change", "changePct", "shareOfRecentPct"],
                     [[r.get("company"), r.get("recentComplaints"), r.get("priorComplaints"), r.get("change"),
                       r.get("changePct"), r.get("shareOfRecentPct")] for r in rows])


def render_benchmark(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    print("Product benchmark | showing %s" % len(rows))
    print()
    table = []
    for row in rows:
        top_issue = (row.get("topIssues") or [{}])[0]
        table.append([kd.clip(row.get("product"), 30), kd.num(row.get("complaints")),
                      kd.pct(row.get("sharePct")), kd.pct(row.get("changePct"), signed=True),
                      "%s (%s)" % (kd.clip(top_issue.get("issue"), 30), kd.num(top_issue.get("complaints")))])
    kd.print_table(["PRODUCT", "COMPLAINTS", "SHARE", "CHANGE", "TOP ISSUE"], table,
                   widths=[30, 11, 7, 8, 34])
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv, ["product", "complaints", "sharePct", "changePct", "topIssue"],
                     [[r.get("product"), r.get("complaints"), r.get("sharePct"), r.get("changePct"),
                       ((r.get("topIssues") or [{}])[0]).get("issue")] for r in rows])


def render_company(payload, args):
    data = payload.get("data") or {}
    complaints = data.get("complaints") or {}
    lending = data.get("lending") or {}
    print("Company: %s" % data.get("company"))
    kd.print_kv([
        ("Complaints (window)", "%s (prior %s, %s)"
         % (kd.num(complaints.get("total")), kd.num(complaints.get("priorTotal")),
            kd.pct(complaints.get("changePct"), signed=True))),
        ("Timely response", kd.pct(complaints.get("timelyRatePct"))),
        ("HMDA year", lending.get("year")),
        ("Originated / denied", "%s / %s" % (kd.num((lending.get("actionsTaken") or {}).get("originated")),
                                             kd.num((lending.get("actionsTaken") or {}).get("denied")))),
        ("Denial rate", kd.pct(lending.get("denialRatePct"))),
        ("Average origination", kd.money(lending.get("averageOriginationUsd"))),
    ])
    products = complaints.get("products") or []
    if products:
        print()
        kd.print_table(["PRODUCT", "COMPLAINTS", "SHARE"],
                       [[kd.clip(p.get("product"), 36), kd.num(p.get("complaints")), kd.pct(p.get("sharePct"))]
                        for p in products[:8]], widths=[36, 11, 7])
    kd.warning_lines(payload.get("meta") or {})


def main(argv=None):
    args = parse_args(argv)
    payload = fetch(args)
    if args.json:
        kd.dump_json(payload)
        return 0
    if args.mode == "trending":
        render_trending(payload, args)
    elif args.mode == "benchmark":
        render_benchmark(payload, args)
    elif args.mode == "company":
        render_company(payload, args)
    else:
        render_complaints(payload, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
