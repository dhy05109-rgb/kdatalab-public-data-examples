#!/usr/bin/env python3
"""Kalshi vs Polymarket odds and cross-venue arbitrage scanner.

Two views over the same two prediction markets:

* ``--mode markets``    normalised odds (YES/NO, bid/ask, volume, liquidity, close time)
* ``--mode arbitrage``  questions listed on both venues, ranked by YES-probability gap

Use it to find a price disagreement between the two venues, to build a
probability feed for a trading bot, or to back-test an event-driven strategy.

    export RAPIDAPI_KEY=...
    python prediction_market_arbitrage.py --mode markets --query election --limit 10
    python prediction_market_arbitrage.py --min-spread 1.5 --min-match 0.5
    python prediction_market_arbitrage.py --demo

API: Kalshi & Polymarket Odds & Arbitrage API (RapidAPI)
     https://rapidapi.com/김태욱/api/kalshi-polymarket-odds-arbitrage-api
Data: Polymarket Gamma API + Kalshi public market API (no key, no login).
"""

from __future__ import annotations

import argparse

import kdatalab_client as kd

HOST = "kalshi-polymarket-odds-arbitrage-api.p.rapidapi.com"
SIGNUP_URL = "https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/kalshi-polymarket-odds-arbitrage-api"
SAMPLE_MARKETS = "prediction_markets.json"
SAMPLE_ARBITRAGE = "prediction_arbitrage.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Read Kalshi and Polymarket odds, and scan for probability spreads between them.",
        epilog="An odds gap is not free money: fees, settlement rules and matching errors all matter.",
    )
    parser.add_argument("--mode", choices=["arbitrage", "markets"], default="arbitrage",
                        help="arbitrage (default) or markets")
    parser.add_argument("--query", default=None, help="Keyword filter on the question or event title")
    parser.add_argument("--min-spread", type=float, default=1.0,
                        help="Arbitrage: minimum YES gap in percentage points (default 1.0)")
    parser.add_argument("--min-match", type=float, default=0.5,
                        help="Arbitrage: minimum title-match score, 0-1 (default 0.5; lower = more, noisier pairs)")
    parser.add_argument("--min-volume", type=float, default=0.0,
                        help="Markets: minimum lifetime volume in USD (default 0)")
    parser.add_argument("--limit", type=int, default=15, help="Rows to request (default 15)")
    parser.add_argument("--platform", choices=["both", "polymarket", "kalshi"], default="both",
                        help="Markets: which venue (default both)")
    kd.add_output_args(parser)
    return parser.parse_args(argv)


def fetch(args):
    if args.mode == "markets":
        params = {"mode": args.platform, "query": args.query,
                  "minVolumeUsd": args.min_volume or None, "limit": args.limit}
        return kd.fetch(args, HOST, "/markets", params, SAMPLE_MARKETS,
                        "The Kalshi & Polymarket API", SIGNUP_URL)
    params = {"minSpreadPct": args.min_spread, "minMatchScore": args.min_match,
              "query": args.query, "limit": args.limit}
    return kd.fetch(args, HOST, "/arbitrage", params, SAMPLE_ARBITRAGE,
                    "The Kalshi & Polymarket API", SIGNUP_URL)


def render_markets(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    pool = meta.get("poolSize") or {}
    print("Universe: Polymarket %s markets, Kalshi %s events | matched filter: %s"
          % (pool.get("polymarket", "-"), pool.get("kalshi", "-"), meta.get("query") or "(none)"))
    print()

    table = []
    for market in rows:
        table.append([
            market.get("platform", "-"),
            kd.clip(market.get("title"), 58),
            kd.pct(market.get("yesPct"), signed=False),
            kd.money(market.get("volume24hUsd")),
            kd.money(market.get("liquidityUsd")),
            (market.get("closeTime") or "-")[:10],
        ])
    kd.print_table(["VENUE", "QUESTION", "YES", "24H VOL", "LIQUIDITY", "CLOSES"], table,
                   widths=[12, 58, 7, 9, 10, 10])
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv,
                     ["platform", "title", "yesPct", "noPct", "volumeUsd", "volume24hUsd", "liquidityUsd",
                      "closeTime", "url"],
                     [[m.get("platform"), m.get("title"), m.get("yesPct"), m.get("noPct"), m.get("volumeUsd"),
                       m.get("volume24hUsd"), m.get("liquidityUsd"), m.get("closeTime"), m.get("url")] for m in rows])


def render_arbitrage(payload, args):
    meta = payload.get("meta") or {}
    rows = payload.get("data") or []
    print("Scan: YES gap >= %.2f pt, title match >= %.2f | pairs kept: %s"
          % (args.min_spread, args.min_match, meta.get("count", len(rows))))
    print()

    table = []
    for pair in rows:
        poly = pair.get("polymarket") or {}
        kalshi = pair.get("kalshi") or {}
        table.append([
            kd.clip(pair.get("question"), 54),
            kd.pct(poly.get("yesPct")),
            kd.pct(kalshi.get("yesPct")),
            kd.pct(pair.get("spreadPct"), signed=False),
            kd.num(pair.get("matchScore"), 2),
            pair.get("higherYesSide", "-"),
        ])
    if table:
        kd.print_table(["MATCHED QUESTION", "POLY YES", "KALSHI YES", "SPREAD PT", "MATCH", "HIGHER"], table,
                       widths=[54, 9, 10, 9, 6, 11])

    if rows:
        print("\nLinks for the first pair:")
        first = rows[0]
        for side, label in ((first.get("polymarket") or {}, "Polymarket"), (first.get("kalshi") or {}, "Kalshi")):
            if side.get("url"):
                print("  %-10s %s" % (label, side["url"]))
    else:
        print("No pair passed the filter. This is the normal result with strict matching:")
        print("  the two venues word questions differently, and a loose match produces false pairs.")
        print("  Try --min-match 0.35 to inspect weaker candidates, then read both questions before acting.")
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv,
                     ["question", "matchScore", "matchConfidence", "spreadPct", "higherYesSide",
                      "polymarketYesPct", "kalshiYesPct", "polymarketUrl", "kalshiUrl"],
                     [[p.get("question"), p.get("matchScore"), p.get("matchConfidence"), p.get("spreadPct"),
                       p.get("higherYesSide"), (p.get("polymarket") or {}).get("yesPct"),
                       (p.get("kalshi") or {}).get("yesPct"), (p.get("polymarket") or {}).get("url"),
                       (p.get("kalshi") or {}).get("url")] for p in rows])


def main(argv=None):
    args = parse_args(argv)
    payload = fetch(args)
    if args.json:
        kd.dump_json(payload)
        return 0
    if args.mode == "markets":
        render_markets(payload, args)
    else:
        render_arbitrage(payload, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
