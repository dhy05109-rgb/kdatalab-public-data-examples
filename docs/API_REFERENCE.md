# API reference

Every endpoint below returns JSON with a `meta` object (echoing the filters, counts,
warnings and `fetchedAt`) and a `data` array — or `data` object for single-record routes.
All requests go through the RapidAPI gateway:

```bash
curl -s "https://<gateway-host><path>" \
  -H "X-RapidAPI-Key: $RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: <gateway-host>"
```

Errors use HTTP status codes with a JSON body: `400` for a bad parameter (with a `code` such
as `bad_agency`), `401` when the gateway key or proxy secret is missing, `404` for an unknown
path or record, `405` for the wrong method, `503` when an upstream source is throttling.

Plans on every listing: BASIC free 100 requests/month · PRO $9.99 / 10k · ULTRA $29.99 / 50k ·
MEGA $79.99 / 250k.

---

## 1. Kalshi & Polymarket Odds & Arbitrage API

Host `kalshi-polymarket-odds-arbitrage-api.p.rapidapi.com`
· [listing](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/kalshi-polymarket-odds-arbitrage-api)

| Endpoint | Parameters | Returns |
|----------|------------|---------|
| `GET /markets` | `mode=both\|polymarket\|kalshi`, `query`, `minVolumeUsd`, `limit` (1-200) | `platform`, `marketId`, `tickerOrSlug`, `title`, `eventTitle`, `category`, `status`, `yesPct`, `noPct`, `yesBidPct`, `yesAskPct`, `volumeUsd`, `volume24hUsd`, `liquidityUsd`, `closeTime`, `url` |
| `GET /arbitrage` | `minSpreadPct` (default 1.0), `minMatchScore` (default 0.5), `query`, `limit` | `question`, `matchScore`, `matchConfidence`, `spreadPct`, `higherYesSide`, `polymarket{...}`, `kalshi{...}` |

`meta.poolSize` reports how many markets were scanned per venue. Strict matching keeps
`/arbitrage` empty most of the time by design.

## 2. UK & Australia Government Tenders API

Host `uk-australia-government-tenders-api.p.rapidapi.com`
· [listing](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/uk-australia-government-tenders-api)

| Endpoint | Parameters | Returns |
|----------|------------|---------|
| `GET /uk/tenders` | `keyword`, `stage=tender\|award\|planning\|all`, `source=contracts-finder\|find-a-tender\|both`, `days` (1-90), `limit` | `ocid`, `noticeId`, `title`, `description`, `stage`, `status`, `buyerName`, `buyerRegion`, `valueAmount`, `valueCurrency`, `publishedDate`, `deadlineDate`, `daysUntilDeadline`, `cpvCodes`, `noticeType`, `mainCategory`, `noticeUrl` |
| `GET /au/tenders` | `daysBack` (1-90), `limit`, `dateField`, `keyword` | `id`, `title`, `agency`, `supplierName`, `supplierRegion`, `value`, `currency`, `publishDate`, `closeDate`, `status`, `ocid`, `noticeUrl` |

## 3. EU TED Public Procurement API

Host `eu-ted-public-procurement-api.p.rapidapi.com`
· [listing](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/eu-ted-public-procurement-api)

| Endpoint | Parameters | Returns |
|----------|------------|---------|
| `GET /eu/tenders` | `keyword`, `buyerCountries` (e.g. `DEU,FRA`), `cpvCodes`, `noticeTypes` (default `cn-standard`), `onlyActive`, `days` (1-90), `limit` (1-100), `language` (default `eng`) | `publicationNumber`, `noticeType`, `publicationDate`, `deadlineDate`, `daysUntilDeadline`, `title`, `buyerName`, `buyerCountry`, `totalValue`, `currency`, `cpvCodes`, `contractNature`, `procedureType`, `tedUrl`, `xmlUrl`, `pdfUrl` |

TED takes an expert query rather than simple parameters; the generated query is returned in
`meta.tedQuery` so you can verify what was searched.

## 4. US Building Permits API

Host `us-building-permits-api4.p.rapidapi.com` (the slug carries a `4` because
`us-building-permits-api` was already taken on RapidAPI)
· [listing](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-building-permits-api4)

| Endpoint | Parameters | Returns |
|----------|------------|---------|
| `GET /us/permits` | `cities=nyc,chicago,austin,seattle,sanfrancisco`, `daysBack` (1-90), `minEstimatedCost`, `keyword`, `workType=all\|new_construction\|renovation\|demolition\|trade\|other`, `limit` (1-100) | `city`, `permitNumber`, `permitType`, `workType`, `status`, `issuedDate`, `estimatedCost`, `streetAddress`, `zip`, `contractorCompany`, `contractorRole`, `description`, `units`, `floorAreaSqft`, `recordUrl` |

Cold requests scan five portals in parallel (2-7 s); the result is cached for 5 minutes.
Austin does not publish job cost, so `minEstimatedCost > 0` skips it and says so in
`meta.warnings`.

## 5. SEC Capital Flow API — private

Not sold on RapidAPI. Use Actor
[`sec-capital-flow-scraper`](https://apify.com/livable_handloom/sec-capital-flow-scraper):
`mode=all|formD|form4|form13f`, `daysBack`, `query`, `minAmountUsd`, `transactionType`,
`topHoldings`, `maxResults`.

## 6. BioPharma & FDA Regulatory Intel API

Host `biopharma-fda-regulatory-intel-api.p.rapidapi.com`
· [listing](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/biopharma-fda-regulatory-intel-api)

| Endpoint | Parameters |
|----------|------------|
| `GET /trials` | `query`, `status` (default `all`), `phase`, `days` (default 30), `limit` |
| `GET /fda/recalls` | `query`, `category=all\|food\|drug\|device`, `classification`, `days`, `limit` |
| `GET /fda/devices-510k` | `query`, `productCode`, `days`, `limit` |
| `GET /fda/drug-approvals` | `query`, `applicationType`, `days`, `limit` |
| `GET /intel/feed` | `query`, `days`, `limit` (max 60) |

All responses share the same record keys (`recordType`, `id`, `title`, `organization`,
`status`, `keyDate`, `summary`, `phase`, `classification`, `detailUrl`, …) so the feed loads
into one table.

## 7. US Federal Grants & R&D Awards API

Host `us-federal-grants-r-d-awards-api.p.rapidapi.com`
· [listing](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-federal-grants-r-d-awards-api)

| Endpoint | Parameters | Notes |
|----------|------------|-------|
| `GET /awards/search` | `keyword`, `source=all\|nih\|nsf`, `fiscalYear`, `minAmount`, `limit` (1-50) | ordered by amount, largest first |
| `GET /opportunities` | `keyword`, `status=posted\|forecasted\|all`, `limit` | Grants.gov, ordered by open date |
| `GET /feed` | `keyword`, `limit` (1-40) | awards + opportunities, tagged by `recordType` |

`amountBasis` distinguishes an NIH fiscal-year amount from an NSF estimated total award.
NSF pages hold 25 rows per call, so a very broad query may return fewer than `limit`.

## 8. Korea Kimchi Premium & Crypto Spread API

Host `korea-kimchi-premium-crypto-spread-api.p.rapidapi.com`
· [listing](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/korea-kimchi-premium-crypto-spread-api)

| Endpoint | Parameters | Returns |
|----------|------------|---------|
| `GET /premium` | `symbols` (max 12), `krExchange=both\|upbit\|bithumb`, `globalExchange=both\|kraken\|coinbase` | per coin: `kimchiPremiumPct`, `spreadUsd`, `spreadKrw`, `headlineVenue`, `bestVenue`, `venues[]`, `krExchanges{}`, `globalExchanges{}`, `market` |
| `GET /fx` | — | `usdKrw`, `rateDate`, `source`, `fallbackUsed` |
| `GET /markets` | — | supported coins (179) and venue pairs |

USD prices use Kraken/Coinbase spot; the FX rate is the ECB reference rate from Frankfurter
(fallback `open.er-api.com`). Binance is not used because it blocks US IPs.

## 9. Global Entity & Compliance Due Diligence API

Host `global-entity-compliance-due-diligence-api.p.rapidapi.com`
· [listing](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/global-entity-compliance-due-diligence-api)

| Endpoint | Parameters |
|----------|------------|
| `GET /entities/search` | `query` (required), `country`, `status=ACTIVE\|INACTIVE\|all`, `limit` (1-25) |
| `GET /entities/{lei}` | 20-character LEI |
| `GET /nonprofits/search` | `query`, `state`, `ntee`, `limit` (1-25) |
| `GET /nonprofits/{ein}` | 9-digit EIN, hyphen optional |
| `GET /regulations/search` | `query`, `type`, `agency` (slug), `days` (1-1825), `limit` |
| `GET /due-diligence` | `name` (required), `country`, `limit` (1-10), `days` (default 365) |

`/due-diligence` returns `summary` (`leiMatched`, `nonprofitMatched`, `regulationMentions`,
`signals`, `flags`) plus the raw results of all three sources. Flags are advisory signals,
not a screening result.

## 10. US Consumer Finance Complaint & Fair-Lending API

Host `us-consumer-finance-complaint-fair-lending-api.p.rapidapi.com` (expected `us-consumer-finance-complaint-fair-lending-api.p.rapidapi.com`)

| Endpoint | Parameters |
|----------|------------|
| `GET /complaints` | `company`, `product`, `issue`, `state` (max 12), `companyResponse`, `timely=yes\|no`, `q`, `days` (1-1825, default 90), `dateFrom`, `dateTo`, `sort=newest\|oldest`, `limit` (1-50) |
| `GET /companies/search` | `query`, `days` (default 365), `limit` |
| `GET /companies/trending` | `days`, `product`, `state`, `lag` (default 15), `minVolume`, `sort=change\|pct`, `direction=up\|down\|both`, `limit` |
| `GET /company` | `name` or `lei`, `days`, `lag`, `lendingYear`, `includeLending` |
| `GET /products/benchmark` | `product`, `days`, `lag`, `limit` |

`meta.dataFreshness` reports CFPB's own last update and total record count (19,348,396 on
2026-11-22). Complaints publish after the company responds or after 15 days, so the newest
days are incomplete by definition.

## 11. US Disaster & Flood Loss API

Host `us-disaster-flood-loss-intelligence-api.p.rapidapi.com` (expected `us-disaster-flood-loss-intelligence-api.p.rapidapi.com`)

| Endpoint | Parameters |
|----------|------------|
| `GET /disasters` | `state` (max 10), `incidentType`, `declarationType=DR\|EM\|FM`, `program=ih\|ia\|pa\|hm`, `year`, `from`, `to`, `countyFips`, `q`, `sort`, `limit` (1-100) |
| `GET /disaster` | `number` (1-32767), `limit` (1-500) |
| `GET /assistance` | `disaster`, `state`, `county`, `zip`, `mode=owners\|renters\|both`, `minApprovedUsd`, `sort`, `limit` |
| `GET /assistance/counties` | `disaster` (required), `state`, `mode`, `sort`, `maxRows` (200-1000), `limit` |
| `GET /flood/claims` | `state`, `countyFips`, `zip`, `from`, `to`, `event`, `zone`, `occupancy`, `minBuildingPaidUsd`, `sort=newest\|oldest\|paid`, `limit` |
| `GET /county` | `state` (required), `countyFips` (required), `countyName`, `limit` |

A declaration row is one *designated area*, not one disaster: a 60-county disaster appears 60
times. `/disasters` separates `totalAreaRows` from `distinctDisasters`. NFIP rows are
FEMA-redacted and many payments are zero; a zero is not a denial.

---

## Apify Actors

All Actors accept the standard Apify input plus their own fields, and return one dataset item
per record. Synchronous usage (no polling):

```bash
curl -s -X POST \
  "https://api.apify.com/v2/acts/livable_handloom~<actor>/run-sync-get-dataset-items?token=$APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"maxItems": 20}'
```

| Actor | Key inputs |
|-------|-----------|
| `korea-ipo-calendar` | `mode=subscriptionSchedule\|demandForecastSchedule\|demandForecastResults\|newListings`, `maxItems`, `maxPages`, `onlyUpcoming` |
| `korea-cheongyak-calendar` | `mode=announcements\|detail\|competition\|specialSupply`, `beginDate`, `endDate`, `maxItems`, `maxPages`, `includeDetails`, `regionFilter` |
| `eu-ted-procurement-notices` | `keywords`, `titleKeywords`, `noticeTypes`, `buyerCountries`, `cpvCodes`, `publishedFrom`/`publishedTo`, `deadlineFrom`/`deadlineTo`, `onlyActive`, `maxItems`, `languagePreference`, `query` (raw TED expert query) |
| `suumo-japan-rental-scraper` | `startUrls`, `prefecture`, `ward`, `startPage`, `maxItems`, `maxPagesPerUrl` |
| `kalshi-polymarket-scraper` | `mode`, `query`, `minVolumeUsd`, `includeClosed`, `minSpreadPct`, `minMatchScore`, `maxItems` |
| `uk-tenders-scraper` | `source`, `keyword`, `stage`, `publishedFrom`, `publishedTo`, `minValueGbp`, `maxItems` |
| `austender-procurement-scraper` | `tenderTypes`, `keyword`, `agency`, `category`, `daysBack`, `minValue`, `maxItems` |
| `us-building-permits-scraper` | `cities`, `daysBack`, `minEstimatedCost`, `keyword`, `permitType`, `maxResults` |
| `sec-capital-flow-scraper` | `mode=all\|formD\|form4\|form13f`, `daysBack`, `query`, `minAmountUsd`, `maxResults` |

Full input schemas live on each Actor page under the **Input** tab.
