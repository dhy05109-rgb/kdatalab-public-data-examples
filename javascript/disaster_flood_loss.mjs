// FEMA disaster declarations and NFIP flood claims (US disaster / flood loss).
//
//   export RAPIDAPI_KEY=...
//   node disaster_flood_loss.mjs --mode=flood --state=LA --event=Ida
//   node disaster_flood_loss.mjs --mode=disasters --state=FL --year=2024
//   node disaster_flood_loss.mjs --demo
//
// API: https://rapidapi.com/김태욱/api/us-disaster-flood-loss-intelligence-api
// The listing "US Disaster & Flood Loss Intelligence API" is live; HOST is its
// final RapidAPI gateway host.

import { rapidapi, sample, demoBanner, table, money, num, clip, parseArgs } from './client.mjs';

const HOST = 'us-disaster-flood-loss-intelligence-api.p.rapidapi.com';
const SAMPLE_DISASTERS = 'fema_disasters.json';
const SAMPLE_FLOOD = 'flood_claims.json';

async function main() {
  const args = parseArgs();
  const mode = args.mode ?? 'flood';
  if (!args.demo && HOST.startsWith('[')) {
    console.log(`This API is not published yet (placeholder ${HOST}).`);
    console.log('Run with --demo to see the response shape, or replace the marker first (PLACEHOLDERS.md).');
    process.exit(3);
  }

  const params = mode === 'disasters'
    ? { state: args.state, year: args.year, q: args.event, limit: args.limit ?? 15 }
    : { state: args.state, event: args.event, from: args.from, to: args.to, limit: args.limit ?? 15 };
  const sampleFile = mode === 'disasters' ? SAMPLE_DISASTERS : SAMPLE_FLOOD;

  const payload = args.demo ? await sample(sampleFile) : await rapidapi(HOST, mode === 'disasters' ? '/disasters' : '/flood/claims', params);
  if (args.demo) demoBanner(sampleFile, payload);

  const rows = payload.data ?? [];
  const meta = payload.meta ?? {};

  if (mode === 'disasters') {
    console.log(`Declarations | ${num(meta.totalAreaRows)} designated-area rows | ${meta.distinctDisasters ?? '?'} disaster(s) | showing ${rows.length}`);
    console.log('');
    table(['NUMBER', 'DATE', 'ST', 'TYPE', 'INCIDENT', 'AREA'],
      rows.map((row) => [
        row.declarationString ?? row.disasterNumber,
        row.declarationDate,
        row.state,
        row.declarationType,
        clip(row.incidentType, 14),
        clip(row.designatedArea, 32),
      ]), [14, 10, 3, 5, 14, 32]);
  } else {
    const totals = meta.totals ?? {};
    console.log(`NFIP claims | ${num(meta.totalClaims)} matching | paid building ${money(totals.paidBuildingUsd)} across the rows shown`);
    console.log('');
    table(['LOSS DATE', 'ST', 'ZIP', 'EVENT', 'ZONE', 'OCCUPANCY', 'PAID BLDG'],
      rows.map((row) => [
        row.dateOfLoss,
        row.state,
        row.zipCode ?? '-',
        clip(row.floodEvent, 22),
        row.ratedFloodZone ?? '-',
        clip(row.occupancy, 22),
        money(row.paidBuildingUsd),
      ]), [10, 3, 6, 22, 5, 22, 10]);
  }

  for (const warning of meta.warnings ?? []) console.log(`! ${warning}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
