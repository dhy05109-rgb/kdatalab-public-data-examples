#!/usr/bin/env python3
"""Korean kimchi premium tracker (Upbit / Bithumb vs Kraken / Coinbase).

Computes the kimchi premium - the gap between the Korean won price of a coin
and its USD price elsewhere, converted at the live USD/KRW rate - and flags
coins whose premium crosses a threshold you set. Useful for a crypto arbitrage
watchlist, a spread dashboard, or an alerting job.

    export RAPIDAPI_KEY=...
    python kimchi_premium_tracker.py --symbols BTC,ETH,XRP --min-premium 2
    python kimchi_premium_tracker.py --watch 60 --min-premium 3
    python kimchi_premium_tracker.py --demo

API: Korea Kimchi Premium & Crypto Spread API (RapidAPI)
     https://rapidapi.com/김태욱/api/korea-kimchi-premium-crypto-spread-api
Data: Upbit, Bithumb, Kraken, Coinbase public tickers + ECB reference FX rate.
"""

from __future__ import annotations

import argparse
import time

import kdatalab_client as kd

HOST = "korea-kimchi-premium-crypto-spread-api.p.rapidapi.com"
SIGNUP_URL = "https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/korea-kimchi-premium-crypto-spread-api"
SAMPLE = "kimchi_premium.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Track the Korea kimchi premium across Upbit/Bithumb and Kraken/Coinbase.",
        epilog="Prices are live public tickers; nothing here is investment advice.",
    )
    parser.add_argument("--symbols", default="BTC,ETH,XRP,SOL,DOGE",
                        help="Comma-separated coins (max 12). Default: BTC,ETH,XRP,SOL,DOGE")
    parser.add_argument("--kr", default="both", choices=["both", "upbit", "bithumb"],
                        help="Korean venue (default: both)")
    parser.add_argument("--global", dest="global_", default="both", choices=["both", "kraken", "coinbase"],
                        help="Global venue (default: both)")
    parser.add_argument("--min-premium", type=float, default=0.0,
                        help="Only print coins at or above this premium %%, and mark them ALERT")
    parser.add_argument("--watch", type=float, metavar="SECONDS",
                        help="Refresh every N seconds until Ctrl-C")
    kd.add_output_args(parser)
    return parser.parse_args(argv)


def fetch_premium(args):
    params = {
        "symbols": args.symbols,
        "krExchange": args.kr,
        "globalExchange": args.global_,
    }
    return kd.fetch(
        args, HOST, "/premium", params, SAMPLE,
        "The Korea Kimchi Premium API", SIGNUP_URL,
    )


def _kr_book(coin):
    ticker = (coin.get("headlineVenue") or {}).get("krExchange") or ""
    return (coin.get("krExchanges") or {}).get(ticker) or {}


def render(payload, args):
    meta = payload.get("meta") or {}
    fx = meta.get("fx") or {}
    rows = payload.get("data") or []

    print("FX: 1 USD = %s KRW  (%s, %s)"
          % (kd.num(fx.get("usdKrw"), 2), fx.get("rateDate") or "-", fx.get("source") or "-"))
    if fx.get("fallbackUsed"):
        print("! primary FX source failed; a fallback rate was used")
    print("Venues: KR=%s  global=%s  fetched %s"
          % (meta.get("krExchange", args.kr), meta.get("globalExchange", args.global_),
             meta.get("fetchedAt", "-")))
    print()

    table = []
    alerts = []
    for coin in rows:
        premium = coin.get("kimchiPremiumPct")
        if args.min_premium and (premium is None or premium < args.min_premium):
            continue
        best = coin.get("bestVenue") or {}
        kr_book = _kr_book(coin)
        best_label = "%s/%s %s" % (
            best.get("krExchange", "-"), best.get("globalExchange", "-"), kd.pct(best.get("premiumPct"), signed=True)
        )
        table.append([
            coin.get("symbol", "-"),
            kd.num(kr_book.get("priceKrw"), 0),
            kd.num(kr_book.get("priceUsd"), 2),
            kd.num((coin.get("market") or {}).get("globalReferenceUsd"), 2),
            kd.pct(premium, signed=True),
            kd.num(coin.get("spreadUsd"), 2),
            best_label,
        ])
        if args.min_premium and premium is not None and premium >= args.min_premium:
            alerts.append("ALERT %s premium %s >= %.2f%% (best %s/%s %s)"
                          % (coin.get("symbol"), kd.pct(premium, signed=True), args.min_premium,
                             best.get("krExchange", "-"), best.get("globalExchange", "-"),
                             kd.pct(best.get("premiumPct"), signed=True)))

    kd.print_table(
        ["COIN", "KOREA (KRW)", "USD EQUIV", "GLOBAL (USD)", "PREMIUM", "SPREAD USD", "BEST VENUE"],
        table,
        widths=[8, 14, 11, 13, 9, 11, 30],
    )
    if alerts:
        print()
        for line in alerts:
            print(line)
    if args.min_premium and not table:
        print("(no coin at or above %.2f%%)" % args.min_premium)
    kd.warning_lines(meta)

    if args.csv:
        kd.write_csv(args.csv,
                     ["symbol", "krwPrice", "usdEquivalentPrice", "globalUsdPrice", "kimchiPremiumPct",
                      "spreadUsd", "spreadKrw", "bestKr", "bestGlobal", "bestPremiumPct"],
                     [[c.get("symbol"),
                       _kr_book(c).get("priceKrw"),
                       _kr_book(c).get("priceUsd"),
                       (c.get("market") or {}).get("globalReferenceUsd"),
                       c.get("kimchiPremiumPct"), c.get("spreadUsd"), c.get("spreadKrw"),
                       (c.get("bestVenue") or {}).get("krExchange"), (c.get("bestVenue") or {}).get("globalExchange"),
                       (c.get("bestVenue") or {}).get("premiumPct")] for c in rows])


def main(argv=None):
    args = parse_args(argv)
    while True:
        payload = fetch_premium(args)
        if args.json:
            kd.dump_json(payload)
        else:
            render(payload, args)
        if not args.watch or args.demo:
            return 0
        print("\n--- refresh in %.0fs (Ctrl-C to stop) ---\n" % args.watch)
        time.sleep(args.watch)


if __name__ == "__main__":
    raise SystemExit(main())
