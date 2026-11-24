#!/usr/bin/env python3
"""US disaster, FEMA aid and flood-insurance loss intelligence.

Built on FEMA OpenFEMA: disaster declarations, Individual & Households Program
(IHP) aid, and National Flood Insurance Program (NFIP) claims.

* ``--mode disasters``  federal declarations, one designated area per row
* ``--mode flood``      NFIP claims with flood zone, occupancy and paid amounts
* ``--mode county``     one county: declaration history, NFIP claims, IHP totals
* ``--mode assistance`` IHP aid rows with approval rates

Who uses this: insurers and MGAs pricing flood risk, real-estate and lending
teams screening collateral, municipal and resilience analysts, and reporters
covering a named storm.

    export RAPIDAPI_KEY=...
    python disaster_flood_intel.py --mode disasters --state FL --year 2024
    python disaster_flood_intel.py --mode flood --state LA --event Ida
    python disaster_flood_intel.py --mode county --state FL --fips 12086
    python disaster_flood_intel.py --demo

API: US Disaster & Flood Loss API (RapidAPI)
     https://rapidapi.com/김태욱/api/us-disaster-flood-loss-intelligence-api
Data: OpenFEMA v2 DisasterDeclarationsSummaries, HousingAssistanceOwners/Renters,
      v3 NfipClaims (public domain, redacted by FEMA - no names or street addresses).
"""

from __future__ import annotations

import argparse

import kdatalab_client as kd

# RapidAPI 11 (FEMA + NFIP) gateway host — the listing is live.
HOST = "us-disaster-flood-loss-intelligence-api.p.rapidapi.com"
SIGNUP_URL = "https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-disaster-flood-loss-intelligence-api"
SAMPLE_DISASTERS = "fema_disasters.json"
SAMPLE_FLOOD = "flood_claims.json"
SAMPLE_COUNTY = "fema_county.json"
SAMPLE_ASSISTANCE = "fema_assistance.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Explore FEMA disaster declarations, IHP aid and NFIP flood claims.",
    )
    parser.add_argument("--mode", choices=["disasters", "flood", "county", "assistance"],
                        default="disasters", help="View to run (default disasters)")
    parser.add_argument("--state", help="Two-letter state code, e.g. FL, LA, PR")
    parser.add_argument("--year", type=int, help="Disasters: declaration year")
    parser.add_argument("--event", help="Flood: event name contains, e.g. Ida")
    parser.add_argument("--fips", help="County FIPS code, e.g. 12086 (Miami-Dade)")
    parser.add_argument("--disaster", type=int, help="Disaster number, e.g. 4834 (needed for assistance)")
    parser.add_argument("--from", dest="from_", help="Flood: date of loss from (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to", help="Flood: date of loss to (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, default=15, help="Rows to request (default 15)")
    kd.add_output_args(parser)
    return parser.parse_args(argv)


def fetch(args):
    label = "The US Disaster & Flood Loss API (RapidAPI 11)"
    if args.mode == "flood":
        params = {"state": args.state, "event": args.event, "from": args.from_, "to": args.to,
                  "countyFips": args.fips, "limit": args.limit}
        return kd.fetch(args, HOST, "/flood/claims", params, SAMPLE_FLOOD, label, SIGNUP_URL)
    if args.mode == "county":
        params = {"state": args.state or "FL", "countyFips": args.fips or "12086", "limit": args.limit}
        return kd.fetch(args, HOST, "/county", params, SAMPLE_COUNTY, label, SIGNUP_URL)
    if args.mode == "assistance":
        params = {"disaster": args.disaster or 4339, "state": args.state, "limit": args.limit}
        return kd.fetch(args, HOST, "/assistance/counties", params, SAMPLE_ASSISTANCE, label, SIGNUP_URL)
    params = {"state": args.state, "year": args.year, "q": args.event, "limit": args.limit}
    return kd.fetch(args, HOST, "/disasters", params, SAMPLE_DISASTERS, label, SIGNUP_URL)


def render_disasters(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    print("Declarations | %s | area rows %s across %s disaster(s) | showing %s"
          % (kd.clip(str((meta.get("window") or {}).get("year") or meta.get("states") or "all"), 24),
             kd.num(meta.get("totalAreaRows")), meta.get("distinctDisasters", "?"), len(rows)))
    print("One row = one designated area (a 60-county disaster appears 60 times).")
    print()
    kd.print_table(["NUMBER", "DATE", "STATE", "TYPE", "INCIDENT", "AREA"],
                   [[r.get("declarationString") or r.get("disasterNumber"), r.get("declarationDate"), r.get("state"),
                     r.get("declarationType"), kd.clip(r.get("incidentType"), 14), kd.clip(r.get("designatedArea"), 30)]
                    for r in rows], widths=[14, 10, 5, 5, 14, 30])
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv,
                     ["disasterNumber", "declarationString", "declarationDate", "state", "declarationType",
                      "incidentType", "title", "designatedArea", "countyFips", "individualHousing"],
                     [[r.get("disasterNumber"), r.get("declarationString"), r.get("declarationDate"), r.get("state"),
                       r.get("declarationType"), r.get("incidentType"), r.get("title"), r.get("designatedArea"),
                       r.get("countyFips"), (r.get("programs") or {}).get("individualHousing")] for r in rows])


def render_flood(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    totals = meta.get("totals") or {}
    print("NFIP claims | %s | %s matching claims | totals cover only the rows shown"
          % (kd.clip(str((meta.get("filters") or {}).get("event") or "all events"), 30), kd.num(meta.get("totalClaims"))))
    if totals:
        print("  paid building %s | claims with payment %s | SFHA claims %s"
              % (kd.money(totals.get("paidBuildingUsd")), totals.get("claimsWithPayment"),
                 totals.get("specialFloodHazardAreaClaims")))
    print()
    kd.print_table(["LOSS DATE", "ST", "ZIP", "EVENT", "ZONE", "OCCUPANCY", "PAID BLDG"],
                   [[r.get("dateOfLoss"), r.get("state"), r.get("zipCode") or "-", kd.clip(r.get("floodEvent"), 22),
                     r.get("ratedFloodZone") or "-", kd.clip(r.get("occupancy"), 22), kd.money(r.get("paidBuildingUsd"))]
                    for r in rows], widths=[10, 3, 6, 22, 5, 22, 10])
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv,
                     ["dateOfLoss", "state", "countyFips", "zipCode", "floodEvent", "ratedFloodZone", "zoneRisk",
                      "specialFloodHazardArea", "occupancy", "paidBuildingUsd", "paidContentsUsd",
                      "buildingDamageUsd", "buildingCoverageUsd"],
                     [[r.get("dateOfLoss"), r.get("state"), r.get("countyFips"), r.get("zipCode"), r.get("floodEvent"),
                       r.get("ratedFloodZone"), r.get("zoneRisk"), r.get("specialFloodHazardArea"), r.get("occupancy"),
                       r.get("paidBuildingUsd"), r.get("paidContentsUsd"), r.get("buildingDamageUsd"),
                       r.get("buildingCoverageUsd")] for r in rows])


def render_county(payload, args):
    meta = payload.get("meta") or {}
    data = payload.get("data") or {}
    disasters = meta.get("disasters") or {}
    flood = meta.get("flood") or {}
    aid_rows = data.get("assistance") or []
    aid = aid_rows[0] if aid_rows else {}
    print("County: %s, %s (FIPS %s)"
          % (meta.get("countyName") or "-", meta.get("state") or args.state, meta.get("countyFips") or args.fips))
    print()
    kd.print_kv([
        ("Declarations", "%s distinct disasters / %s designated-area rows"
         % (kd.num(disasters.get("distinct")), kd.num(disasters.get("areaRows")))),
        ("NFIP claims", "%s total, %s in the last 12 months"
         % (kd.num(flood.get("totalClaims")), kd.num(flood.get("claimsLast12Months")))),
        ("IHP aid (one row)", "%s approved, approval rate %s"
         % (kd.money(aid.get("totalApprovedIhpUsd")), kd.pct(aid.get("approvalRatePct")))),
    ])
    recent = data.get("recentDisasters") or []
    if recent:
        print("\nRecent declarations:")
        kd.print_table(["NUMBER", "DATE", "TYPE", "INCIDENT", "TITLE"],
                       [[r.get("declarationString"), r.get("declarationDate"), r.get("declarationType"),
                         kd.clip(r.get("incidentType"), 14), kd.clip(r.get("title"), 32)] for r in recent],
                       widths=[14, 10, 5, 14, 32])
    kd.warning_lines(meta)


def render_assistance(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    totals = meta.get("totals") or {}
    print("IHP aid by county | disaster %s | approval rate %s"
          % (meta.get("disasterNumber", args.disaster), kd.pct(totals.get("approvalRatePct"))))
    print()
    kd.print_table(["COUNTY", "REGISTRATIONS", "APPROVED", "APPROVAL %", "APPROVED USD"],
                   [[kd.clip(r.get("county"), 34), kd.num(r.get("validRegistrations")),
                     kd.num(r.get("approvedForFemaAssistance")), kd.pct(r.get("approvalRatePct")),
                     kd.money(r.get("totalApprovedIhpUsd"))] for r in rows],
                   widths=[34, 13, 10, 10, 12])
    kd.warning_lines(meta)


def main(argv=None):
    args = parse_args(argv)
    payload = fetch(args)
    if args.json:
        kd.dump_json(payload)
        return 0
    if args.mode == "flood":
        render_flood(payload, args)
    elif args.mode == "county":
        render_county(payload, args)
    elif args.mode == "assistance":
        render_assistance(payload, args)
    else:
        render_disasters(payload, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
