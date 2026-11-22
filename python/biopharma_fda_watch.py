#!/usr/bin/env python3
"""BioPharma and FDA watch: trials, recalls, 510(k) clearances, drug approvals.

One feed over ClinicalTrials.gov v2 and openFDA (recall enforcement reports,
510(k) device clearances, Drugs@FDA original approvals).

Use it for competitive pipelines, pharmacovigilance, medtech lead lists, and a
daily "what the FDA did" digest.

    export RAPIDAPI_KEY=...
    python biopharma_fda_watch.py --mode feed --keyword oncology --days 14
    python biopharma_fda_watch.py --mode recalls --classification Class%20I
    python biopharma_fda_watch.py --mode trials --keyword diabetes --status recruiting
    python biopharma_fda_watch.py --demo

API: BioPharma & FDA Regulatory Intel API (RapidAPI)
     https://rapidapi.com/김태욱/api/biopharma-fda-regulatory-intel-api
Data: ClinicalTrials.gov v2 and openFDA (public, no key upstream).
"""

from __future__ import annotations

import argparse

import kdatalab_client as kd

HOST = "biopharma-fda-regulatory-intel-api.p.rapidapi.com"
SIGNUP_URL = "https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/biopharma-fda-regulatory-intel-api"
SAMPLE_FEED = "fda_feed.json"
SAMPLE_RECALLS = "fda_recalls.json"
SAMPLE_TRIALS = "fda_trials.json"
SAMPLE_510K = "fda_510k.json"
SAMPLE_APPROVALS = "fda_approvals.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Watch clinical trials, FDA recalls, 510(k) clearances and drug approvals.",
    )
    parser.add_argument("--mode", choices=["feed", "recalls", "trials", "510k", "approvals"], default="feed",
                        help="View to run (default feed)")
    parser.add_argument("--keyword", help="Search text (drug, device, condition, company)")
    parser.add_argument("--days", type=int, default=30, help="Look-back window in days (default 30)")
    parser.add_argument("--status", default="all",
                        help="Trials: overall status, e.g. recruiting (default all)")
    parser.add_argument("--classification", default="all",
                        help="Recalls: Class I, Class II, Class III (default all)")
    parser.add_argument("--limit", type=int, default=20, help="Rows to request (default 20)")
    kd.add_output_args(parser)
    return parser.parse_args(argv)


def fetch(args):
    label = "The BioPharma & FDA API"
    if args.mode == "recalls":
        params = {"query": args.keyword, "classification": args.classification, "days": args.days, "limit": args.limit}
        return kd.fetch(args, HOST, "/fda/recalls", params, SAMPLE_RECALLS, label, SIGNUP_URL)
    if args.mode == "trials":
        params = {"query": args.keyword, "status": args.status, "days": args.days, "limit": args.limit}
        return kd.fetch(args, HOST, "/trials", params, SAMPLE_TRIALS, label, SIGNUP_URL)
    if args.mode == "510k":
        params = {"query": args.keyword, "days": args.days, "limit": args.limit}
        return kd.fetch(args, HOST, "/fda/devices-510k", params, SAMPLE_510K, label, SIGNUP_URL)
    if args.mode == "approvals":
        params = {"query": args.keyword, "days": args.days, "limit": args.limit}
        return kd.fetch(args, HOST, "/fda/drug-approvals", params, SAMPLE_APPROVALS, label, SIGNUP_URL)
    params = {"query": args.keyword, "days": args.days, "limit": args.limit}
    return kd.fetch(args, HOST, "/intel/feed", params, SAMPLE_FEED, label, SIGNUP_URL)


def render_feed(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    print("Window: %s to %s | showing %s records" % (meta.get("fromDate"), meta.get("toDate"), len(rows)))
    print()
    kd.print_table(["TYPE", "DATE", "ORGANIZATION", "TITLE", "STATUS"],
                   [[r.get("recordType", "-"), r.get("keyDate") or "-", kd.clip(r.get("organization"), 24),
                     kd.clip(r.get("title"), 56), kd.clip(r.get("status"), 18)] for r in rows],
                   widths=[16, 10, 24, 56, 18])
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv,
                     ["recordType", "id", "keyDate", "title", "organization", "country", "status", "classification",
                      "phase", "detailUrl"],
                     [[r.get("recordType"), r.get("id"), r.get("keyDate"), r.get("title"), r.get("organization"),
                       r.get("country"), r.get("status"), r.get("classification"), r.get("phase"),
                       r.get("detailUrl")] for r in rows])


def render_recalls(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    print("FDA recalls: %s to %s | %s matches | showing %s"
          % (meta.get("fromDate"), meta.get("toDate"), meta.get("totalMatches", "?"), len(rows)))
    print()
    kd.print_table(["REPORT DATE", "CLASS", "CATEGORY", "FIRM", "PRODUCT / REASON"],
                   [[r.get("keyDate") or "-", r.get("classification") or "-", kd.clip(r.get("category"), 12),
                     kd.clip(r.get("organization"), 24), kd.clip(r.get("summary") or r.get("title"), 64)]
                    for r in rows], widths=[11, 7, 12, 24, 64])
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv,
                     ["id", "keyDate", "classification", "category", "organization", "summary", "status",
                      "sourceUrl"],
                     [[r.get("id"), r.get("keyDate"), r.get("classification"), r.get("category"), r.get("organization"),
                       r.get("summary"), r.get("status"), r.get("sourceUrl")] for r in rows])


def render_trials(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    print("Clinical trials updated %s to %s | showing %s" % (meta.get("fromDate"), meta.get("toDate"), len(rows)))
    print()
    kd.print_table(["UPDATED", "PHASE", "STATUS", "SPONSOR", "TITLE"],
                   [[r.get("keyDate") or "-", kd.clip(r.get("phase"), 12), kd.clip(r.get("status"), 16),
                     kd.clip(r.get("organization"), 24), kd.clip(r.get("title"), 56)] for r in rows],
                   widths=[10, 12, 16, 24, 56])
    kd.warning_lines(meta)


def render_approvals(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    print("FDA approvals %s to %s | showing %s" % (meta.get("fromDate"), meta.get("toDate"), len(rows)))
    print()
    kd.print_table(["DATE", "APPLICATION", "SPONSOR", "PRODUCT"],
                   [[r.get("keyDate") or "-", kd.clip(r.get("id"), 16), kd.clip(r.get("organization"), 24),
                     kd.clip(r.get("productName") or r.get("title"), 58)] for r in rows],
                   widths=[10, 16, 24, 58])


def render_510k(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    print("510(k) clearances %s to %s | showing %s" % (meta.get("fromDate"), meta.get("toDate"), len(rows)))
    print()
    kd.print_table(["DATE", "NUMBER", "APPLICANT", "DEVICE"],
                   [[r.get("keyDate") or "-", kd.clip(r.get("id"), 14), kd.clip(r.get("organization"), 26),
                     kd.clip(r.get("productName") or r.get("title"), 56)] for r in rows],
                   widths=[10, 14, 26, 56])


def main(argv=None):
    args = parse_args(argv)
    payload = fetch(args)
    if args.json:
        kd.dump_json(payload)
        return 0
    if args.mode == "recalls":
        render_recalls(payload, args)
    elif args.mode == "trials":
        render_trials(payload, args)
    elif args.mode == "approvals":
        render_approvals(payload, args)
    elif args.mode == "510k":
        render_510k(payload, args)
    else:
        render_feed(payload, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
