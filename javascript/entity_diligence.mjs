// Company due diligence: GLEIF legal entity + IRS Form 990 + Federal Register.
//
//   export RAPIDAPI_KEY=...
//   node entity_diligence.mjs --name=Tesla --country=US
//   node entity_diligence.mjs --demo
//
// API: https://rapidapi.com/김태욱/api/global-entity-compliance-due-diligence-api

import { rapidapi, sample, demoBanner, table, money, clip, parseArgs } from './client.mjs';

const HOST = 'global-entity-compliance-due-diligence-api.p.rapidapi.com';
const SAMPLE = 'entity_due_diligence.json';

async function main() {
  const args = parseArgs();
  const params = { name: args.name ?? 'Tesla', country: args.country, days: args.days ?? 365, limit: args.limit ?? 5 };

  const payload = args.demo ? await sample(SAMPLE) : await rapidapi(HOST, '/due-diligence', params);
  if (args.demo) demoBanner(SAMPLE, payload);

  const summary = payload.summary ?? {};
  const lei = summary.leiMatched ?? {};
  const nonprofit = summary.nonprofitMatched ?? {};

  console.log(`Due diligence: ${payload.meta?.name ?? args.name}`);
  console.log('');
  console.log(`  Legal entity        ${lei.legalName ?? 'no GLEIF match'}`);
  console.log(`  LEI                 ${lei.lei ?? '-'}`);
  console.log(`  Status / country    ${lei.entityStatus ?? '-'} / ${lei.jurisdiction ?? lei.country ?? '-'}`);
  console.log(`  Direct parent       ${lei.parents?.direct?.legalName ?? 'none reported'}`);
  console.log(`  Ultimate parent     ${lei.parents?.ultimate?.legalName ?? 'none reported'}`);
  console.log(`  US nonprofit        ${nonprofit.name ?? 'no match'}${nonprofit.einFormatted ? ` (EIN ${nonprofit.einFormatted})` : ''}`);
  console.log(`  Federal Register    ${summary.regulationMentions ?? '-'} mentions in ${payload.meta?.regulationWindowDays ?? '-'} days`);

  const flags = summary.flags ?? [];
  if (flags.length) {
    console.log('\nFlags:');
    for (const flag of flags) console.log(`  [${flag.severity}] ${flag.code} - ${flag.detail}`);
  }

  const regulations = payload.regulations?.results ?? [];
  if (regulations.length) {
    console.log('\nRecent federal documents:');
    table(['DATE', 'TYPE', 'TITLE'],
      regulations.map((doc) => [doc.publicationDate, doc.type, clip(doc.title, 78)]), [10, 8, 78]);
  }

  const entities = payload.entities?.results ?? [];
  if (entities.length) {
    console.log('\nGLEIF candidates:');
    table(['LEI', 'LEGAL NAME', 'JURISDICTION', 'STATUS'],
      entities.map((entity) => [entity.lei, clip(entity.legalName, 40), entity.jurisdiction, entity.entityStatus]),
      [22, 40, 14, 8]);
  }

  const financials = nonprofit.latestFinancials;
  if (financials) {
    console.log(`\nLatest Form 990: revenue ${money(financials.totalRevenueUsd)} | expenses ${money(financials.totalExpensesUsd)}`);
  }
  console.log(`\n${payload.meta?.disclaimer ?? 'Verify every register before acting on this report.'}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
