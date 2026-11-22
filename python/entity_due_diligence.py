#!/usr/bin/env python3
"""Company due-diligence report from three public registers in one call.

One name in, three registers out:

* GLEIF LEI            legal entity, jurisdiction, status, parent chain
* ProPublica (IRS 990) US nonprofit revenue, expenses, assets and NTEE code
* Federal Register     US rules, proposed rules and notices mentioning the name

This is a research aid for vendor onboarding, KYC-adjacent checks, nonprofit
prospecting and regulatory monitoring - not a legal opinion or a credit score.

    export RAPIDAPI_KEY=...
    python entity_due_diligence.py --name "Tesla" --country US
    python entity_due_diligence.py --name "Ford Foundation" --days 730 --csv out/dd.csv
    python entity_due_diligence.py --demo

API: Global Entity & Compliance Due Diligence API (RapidAPI)
     https://rapidapi.com/김태욱/api/global-entity-compliance-due-diligence-api
"""

from __future__ import annotations

import argparse

import kdatalab_client as kd

HOST = "global-entity-compliance-due-diligence-api.p.rapidapi.com"
SIGNUP_URL = "https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/global-entity-compliance-due-diligence-api"
SAMPLE = "entity_due_diligence.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a one-name due-diligence report from GLEIF, IRS Form 990 and the Federal Register.",
    )
    parser.add_argument("--name", default="Tesla", help="Legal or trading name to investigate (default: Tesla)")
    parser.add_argument("--country", help="Two-letter jurisdiction filter for GLEIF, e.g. US, DE, GB")
    parser.add_argument("--days", type=int, default=365, help="Federal Register look-back window in days (default 365)")
    parser.add_argument("--limit", type=int, default=5, help="Rows per source to request (default 5)")
    kd.add_output_args(parser)
    return parser.parse_args(argv)


def fetch(args):
    params = {"name": args.name, "country": args.country, "days": args.days, "limit": args.limit}
    return kd.fetch(args, HOST, "/due-diligence", params, SAMPLE,
                    "The Global Entity & Compliance API", SIGNUP_URL)


def render(payload, args):
    meta = payload.get("meta") or {}
    summary = payload.get("summary") or {}
    lei = summary.get("leiMatched") or {}
    nonprofit = summary.get("nonprofitMatched") or {}
    sources = meta.get("sources") or {}

    print("Due diligence: %r%s" % (meta.get("name"), " (%s)" % meta.get("country") if meta.get("country") else ""))
    print()

    pairs = []
    if lei:
        parents = lei.get("parents") or {}
        direct = parents.get("direct") or {}
        ultimate = parents.get("ultimate") or {}
        pairs += [
            ("Legal entity", lei.get("legalName")),
            ("LEI", lei.get("lei")),
            ("Status / jurisdiction", "%s / %s" % (lei.get("entityStatus", "-"), lei.get("jurisdiction", "-"))),
            ("Direct parent", direct.get("legalName") if direct else "none reported"),
            ("Ultimate parent", ultimate.get("legalName") if ultimate else "none reported"),
        ]
    else:
        pairs.append(("Legal entity", "no GLEIF match"))
    if nonprofit:
        pairs.append(("US nonprofit match", "%s (EIN %s, %s)"
                      % (nonprofit.get("name"), nonprofit.get("einFormatted") or nonprofit.get("ein"),
                         nonprofit.get("state") or "-")))
        financials = nonprofit.get("latestFinancials") or {}
        if financials:
            pairs.append(("Latest Form 990", "FY%s revenue %s | expenses %s | assets %s"
                          % (financials.get("taxPeriod") or "-",
                             kd.money(financials.get("totalRevenueUsd")),
                             kd.money(financials.get("totalExpensesUsd")),
                             kd.money(financials.get("totalAssetsUsd")))))
    pairs.append(("Federal Register mentions", "%s in the last %s days"
                  % (summary.get("regulationMentions", "-"), meta.get("regulationWindowDays", "-"))))
    kd.print_kv(pairs)

    flags = summary.get("flags") or []
    if flags:
        print("\nFlags:")
        for flag in flags:
            print("  [%s] %s - %s" % (flag.get("severity", "-"), flag.get("code", "-"), flag.get("detail", "")))

    signals = summary.get("signals") or []
    if signals:
        print("\nSignals:")
        for signal in signals:
            print("  - %s" % signal)

    entities = (payload.get("entities") or {}).get("results") or []
    if entities:
        print("\nGLEIF candidates (%s of %s):"
              % (len(entities), (payload.get("entities") or {}).get("upstreamTotal", "?")))
        kd.print_table(["LEI", "LEGAL NAME", "JURISDICTION", "STATUS"],
                       [[e.get("lei"), kd.clip(e.get("legalName"), 40), e.get("jurisdiction"), e.get("entityStatus")]
                        for e in entities], widths=[22, 40, 14, 8])

    nonprofits = (payload.get("nonprofits") or {}).get("results") or []
    if nonprofits:
        print("\nNonprofit candidates:")
        kd.print_table(["EIN", "NAME", "CITY", "STATE", "NTEE"],
                       [[n.get("einFormatted") or n.get("ein"), kd.clip(n.get("name"), 40),
                         n.get("city"), n.get("state"), n.get("nteeCode")] for n in nonprofits],
                       widths=[11, 40, 16, 6, 6])

    regulations = (payload.get("regulations") or {}).get("results") or []
    if regulations:
        print("\nFederal Register documents (%s of %s in window):"
              % (len(regulations), (payload.get("regulations") or {}).get("upstreamTotal", "?")))
        for doc in regulations:
            agencies = ", ".join(a.get("name", "") for a in (doc.get("agencies") or [])[:2])
            print("  %s  %-8s  %s" % (doc.get("publicationDate", "-"), doc.get("type", "-"),
                                      kd.clip(doc.get("title"), 90)))
            if agencies:
                print("      %s" % kd.clip(agencies, 90))
            if doc.get("htmlUrl"):
                print("      %s" % doc["htmlUrl"])

    if sources:
        print("\nUpstream sources:")
        for name, info in sources.items():
            print("  %-14s ok=%s total=%s" % (name, info.get("ok"), info.get("total")))

    kd.warning_lines(meta)
    print("\n%s" % (meta.get("disclaimer") or "Verify every register before acting on this report."))
    print("GLEIF %s | ProPublica %s | Federal Register %s"
          % ("ok" if (sources.get("gleif") or {}).get("ok") else "failed",
             "ok" if (sources.get("propublica") or {}).get("ok") else "failed",
             "ok" if (sources.get("federalRegister") or {}).get("ok") else "failed"))

    if args.csv:
        kd.write_csv(args.csv, ["section", "key", "value"], _csv_rows(payload))


def _csv_rows(payload):
    rows = []
    summary = payload.get("summary") or {}
    for key, value in (summary.get("leiMatched") or {}).items():
        if not isinstance(value, dict):
            rows.append(["entity", key, value])
    for entity in (payload.get("entities") or {}).get("results") or []:
        rows.append(["gleif_candidate", entity.get("lei"), "%s (%s)" % (entity.get("legalName"), entity.get("jurisdiction"))])
    for doc in (payload.get("regulations") or {}).get("results") or []:
        rows.append(["regulation", doc.get("documentNumber"), "%s %s" % (doc.get("publicationDate"), doc.get("title"))])
    return rows


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
