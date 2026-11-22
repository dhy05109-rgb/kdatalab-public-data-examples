// Korea kimchi premium: Upbit / Bithumb vs Kraken / Coinbase, in USD and KRW.
//
//   export RAPIDAPI_KEY=...
//   node kimchi_premium.mjs --symbols=BTC,ETH,SOL --min-premium=2
//   node kimchi_premium.mjs --demo
//
// API: https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/korea-kimchi-premium-crypto-spread-api

import { rapidapi, sample, demoBanner, table, money, pct, clip, parseArgs } from './client.mjs';

const HOST = 'korea-kimchi-premium-crypto-spread-api.p.rapidapi.com';
const SAMPLE = 'kimchi_premium.json';

async function main() {
  const args = parseArgs();
  const params = {
    symbols: args.symbols ?? 'BTC,ETH,XRP,SOL,DOGE',
    krExchange: args.kr ?? 'both',
    globalExchange: args.global ?? 'both',
  };
  const minPremium = Number(args['min-premium'] ?? 0);

  const payload = args.demo ? await sample(SAMPLE) : await rapidapi(HOST, '/premium', params);
  if (args.demo) demoBanner(SAMPLE, payload);

  const { meta = {}, data = [] } = payload;
  const fx = meta.fx ?? {};
  console.log(`FX: 1 USD = ${Number(fx.usdKrw ?? 0).toLocaleString('en-US')} KRW (${fx.rateDate ?? '-'}, ${fx.source ?? '-'})`);
  console.log('');

  const rows = data
    .filter((coin) => !minPremium || (coin.kimchiPremiumPct ?? -Infinity) >= minPremium)
    .map((coin) => {
      const ticker = coin.headlineVenue?.krExchange;
      const kr = coin.krExchanges?.[ticker] ?? {};
      return [
        coin.symbol,
        Number(kr.priceKrw ?? 0).toLocaleString('en-US'),
        kr.priceUsd?.toFixed(2) ?? '-',
        (coin.market?.globalReferenceUsd ?? 0).toFixed(2),
        pct(coin.kimchiPremiumPct, true),
        coin.spreadUsd?.toFixed(2) ?? '-',
        `${clip(coin.bestVenue?.krExchange, 8)}/${clip(coin.bestVenue?.globalExchange, 8)} ${pct(coin.bestVenue?.premiumPct, true)}`,
      ];
    });

  table(['COIN', 'KOREA (KRW)', 'USD EQUIV', 'GLOBAL (USD)', 'PREMIUM', 'SPREAD USD', 'BEST VENUE'], rows,
    [8, 14, 11, 13, 9, 11, 26]);

  if (minPremium) {
    const alerts = data.filter((coin) => (coin.kimchiPremiumPct ?? -Infinity) >= minPremium);
    console.log(`\n${alerts.length} coin(s) at or above ${minPremium}%`);
    for (const coin of alerts) console.log(`  ALERT ${coin.symbol} ${pct(coin.kimchiPremiumPct, true)}`);
  }
  for (const warning of meta.warnings ?? []) console.log(`! ${warning}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
