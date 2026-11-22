// Kalshi and Polymarket odds, plus the cross-venue YES spread.
//
//   export RAPIDAPI_KEY=...
//   node prediction_markets.mjs --mode=markets --query=election --limit=10
//   node prediction_markets.mjs --mode=arbitrage --min-spread=1.5
//   node prediction_markets.mjs --demo
//
// API: https://rapidapi.com/김태욱/api/kalshi-polymarket-odds-arbitrage-api

import { rapidapi, sample, demoBanner, table, money, pct, clip, parseArgs } from './client.mjs';

const HOST = 'kalshi-polymarket-odds-arbitrage-api.p.rapidapi.com';

async function main() {
  const args = parseArgs();
  const mode = args.mode ?? 'markets';
  const demoFile = mode === 'arbitrage' ? 'prediction_arbitrage.json' : 'prediction_markets.json';
  const params = mode === 'arbitrage'
    ? { minSpreadPct: args['min-spread'] ?? 1.0, minMatchScore: args['min-match'] ?? 0.5, limit: args.limit ?? 15 }
    : { mode: args.platform ?? 'both', query: args.query, minVolumeUsd: args['min-volume'], limit: args.limit ?? 15 };

  const payload = args.demo
    ? await sample(demoFile)
    : await rapidapi(HOST, mode === 'arbitrage' ? '/arbitrage' : '/markets', params);
  if (args.demo) demoBanner(demoFile, payload);

  const rows = payload.data ?? [];

  if (mode === 'arbitrage') {
    console.log(`Pairs kept: ${payload.meta?.count ?? rows.length}`);
    console.log('');
    if (rows.length === 0) {
      console.log('No pair passed the filter. Strict title matching usually returns nothing:');
      console.log('the two venues word the same question differently. Loosen --min-match, then read both questions.');
      return;
    }
    table(['MATCHED QUESTION', 'POLY YES', 'KALSHI YES', 'SPREAD PT', 'MATCH', 'HIGHER'],
      rows.map((pair) => [
        clip(pair.question, 54),
        pct(pair.polymarket?.yesPct),
        pct(pair.kalshi?.yesPct),
        pct(pair.spreadPct),
        pair.matchScore?.toFixed(2) ?? '-',
        pair.higherYesSide ?? '-',
      ]), [54, 9, 10, 9, 6, 11]);
    return;
  }

  console.log(`Polymarket ${payload.meta?.poolSize?.polymarket ?? '-'} markets | Kalshi ${payload.meta?.poolSize?.kalshi ?? '-'} events`);
  console.log('');
  table(['VENUE', 'QUESTION', 'YES', '24H VOL', 'LIQUIDITY', 'CLOSES'],
    rows.map((market) => [
      market.platform,
      clip(market.title, 56),
      pct(market.yesPct),
      money(market.volume24hUsd),
      money(market.liquidityUsd),
      (market.closeTime ?? '-').slice(0, 10),
    ]), [12, 56, 7, 9, 10, 10]);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
