# K-Data Lab — Public Data APIs & Scrapers Starter Kit

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Node 18+](https://img.shields.io/badge/node-18%2B-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![Zero dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](requirements.txt)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Runnable examples for 11 public-data APIs and scrapers** — prediction-market odds,
government tenders, building permits, FDA recalls, federal research grants, the Korean
kimchi premium, corporate due diligence, CFPB complaints, FEMA flood losses, SEC filings,
and the Korean IPO / apartment-subscription calendar.

No SDK to install. No lock-in. Every script is plain Python (`urllib`) or plain
JavaScript (`fetch`), so you can read it in one sitting, copy the one you need, and point
it at your own pipeline. Each example also runs with **`--demo`**, which renders a bundled response from `samples/` (captured from the live API
wherever possible), so you can see the shape of the data before you sign up for anything.

```bash
git clone https://github.com/dhy05109-rgb/kdatalab-public-data-examples.git
cd kdatalab-public-data-examples

python python/kimchi_premium_tracker.py --demo
python python/federal_grants_finder.py --demo
python python/entity_due_diligence.py --demo
```

---

## Contents

- [Quick start](#quick-start)
- [API catalog](#api-catalog)
- [Recipes](#recipes)
  - [Kimchi premium tracker](#kimchi-premium-tracker-upbit--bithumb-vs-kraken--coinbase)
  - [Kalshi vs Polymarket arbitrage](#kalshi-vs-polymarket-arbitrage-scanner)
  - [US research grants finder](#us-research-grants-finder-nih-reporter--nsf--grantsgov)
  - [Company due diligence](#company-due-diligence-gleif-lei--irs-form-990--federal-register)
  - [CFPB complaints and HMDA denial rates](#cfpb-consumer-complaints--hmda-mortgage-denial-rates)
  - [FEMA disasters and flood losses](#fema-disaster-declarations--nfip-flood-claims)
  - [SEC capital-flow signals](#sec-form-d-form-4-and-13f-capital-flow-signals)
  - [Government tenders](#government-tenders-eu-ted-uk-contracts-finder-austender)
  - [Korea IPO and cheongyak](#korea-ipo-calendar--apartment-cheongyak-export)
  - [FDA and clinical trials](#fda-recalls-clinical-trials-510k-and-drug-approvals)
  - [US building permits](#us-building-permits-lead-list)
- [Data sources and licences](#data-sources-and-licences)
- [Pricing and limits](#pricing-and-limits)
- [FAQ](#faq)
- [Repository layout](#repository-layout)
- [Status and roadmap](#status-and-roadmap)

---

## Quick start

### RapidAPI (real-time JSON, 10 listings live)

1. Open any API page from the [catalog](#api-catalog) and subscribe to its **BASIC**
   plan — free, 100 requests per month.
2. Copy your key from the **Endpoints** tab (`X-RapidAPI-Key`).
3. Run anything:

```bash
export RAPIDAPI_KEY="your-rapidapi-key"

python python/kimchi_premium_tracker.py --symbols BTC,ETH,SOL --min-premium 1.5
node   javascript/prediction_markets.mjs --mode markets --limit 10
bash   curl/quickstart.sh 8          # prints the one-line curl for API 8
bash   curl/quickstart.sh --run 8    # actually calls it
```

The same key works for every RapidAPI listing in this repository.

### Apify (bulk scraping runs, pay per 1,000 records)

1. Open an Actor from the [Apify catalog](#apify-actors--bulk-dataset-runs) and press **Try for free**.
2. Copy a token: Apify Console → **Settings → API & Integrations**.
3. Run:

```bash
export APIFY_TOKEN="apify_api_..."

python python/korea_ipo_cheongyak_export.py --market ipo --upcoming
python python/gov_tenders_monitor.py --region uk --source apify --keyword software
```

### No key at all

Every Python and JavaScript example accepts `--demo`, and every `--help` works offline:

```bash
for file in python/*.py; do python "$file" --demo >/dev/null || echo "FAILED: $file"; done
```

---

## API catalog

### RapidAPI — request/response JSON

| # | API | What you get | Gateway host | Status |
|---|-----|--------------|--------------|--------|
| 1 | [Kalshi & Polymarket Odds & Arbitrage](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/kalshi-polymarket-odds-arbitrage-api) | Normalised YES/NO odds from two prediction markets, plus cross-venue probability spreads | `kalshi-polymarket-odds-arbitrage-api.p.rapidapi.com` | live |
| 2 | [UK & Australia Government Tenders](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/uk-australia-government-tenders-api) | Contracts Finder, Find a Tender and AusTender notices: buyer, value, CPV/UNSPSC, deadline | `uk-australia-government-tenders-api.p.rapidapi.com` | live |
| 3 | [EU TED Public Procurement](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/eu-ted-public-procurement-api) | EU TED contract and award notices, expert query built for you | `eu-ted-public-procurement-api.p.rapidapi.com` | live |
| 4 | [US Building Permits](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-building-permits-api4) | NYC, Chicago, Austin, Seattle, San Francisco permits with cost, address and contractor | `us-building-permits-api4.p.rapidapi.com` | live |
| 5 | SEC Capital Flow | Form D raises, Form 4 insider trades, 13F holdings | — | **private** (see [FAQ](#why-is-sec-capital-flow-not-on-rapidapi)) |
| 6 | [BioPharma & FDA Regulatory Intel](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/biopharma-fda-regulatory-intel-api) | ClinicalTrials.gov studies, FDA recalls, 510(k) clearances, drug approvals | `biopharma-fda-regulatory-intel-api.p.rapidapi.com` | live |
| 7 | [US Federal Grants & R&D Awards](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-federal-grants-r-d-awards-api) | NIH RePORTER and NSF awards plus open Grants.gov opportunities | `us-federal-grants-r-d-awards-api.p.rapidapi.com` | live |
| 8 | [Korea Kimchi Premium & Crypto Spread](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/korea-kimchi-premium-crypto-spread-api) | Upbit/Bithumb vs Kraken/Coinbase for 179 coins, with the live USD/KRW rate | `korea-kimchi-premium-crypto-spread-api.p.rapidapi.com` | live |
| 9 | [Global Entity & Compliance Due Diligence](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/global-entity-compliance-due-diligence-api) | GLEIF LEI, ProPublica Form 990 and Federal Register in one report | `global-entity-compliance-due-diligence-api.p.rapidapi.com` | live |
| 10 | [US Consumer Finance Complaint & Fair-Lending](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-consumer-finance-complaint-fair-lending-api) | CFPB complaints (19.3M records) and HMDA mortgage denial rates | `us-consumer-finance-complaint-fair-lending-api.p.rapidapi.com` | live |
| 11 | [US Disaster & Flood Loss Intelligence](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-disaster-flood-loss-intelligence-api) | FEMA declarations, IHP aid, NFIP flood claims (2.7M) | `us-disaster-flood-loss-intelligence-api.p.rapidapi.com` | live |

> **Note.** All 10 public RapidAPI listings are now live (`us-consumer-finance-complaint-fair-lending-api` and `us-disaster-flood-loss-intelligence-api` included). See [PLACEHOLDERS.md](PLACEHOLDERS.md) for setup history.

### Apify Actors — bulk dataset runs

| # | Actor | Dataset | Price |
|---|-------|---------|-------|
| 1 | [`korea-ipo-calendar`](https://apify.com/livable_handloom/korea-ipo-calendar) | Korean IPO subscription windows, book-building competition rates, listing performance | $10 / 1,000 |
| 2 | [`korea-cheongyak-calendar`](https://apify.com/livable_handloom/korea-cheongyak-calendar) | 청약홈 sale notices, per-type prices, competition rates, award scores | $8 / 1,000 |
| 3 | [`eu-ted-procurement-notices`](https://apify.com/livable_handloom/eu-ted-procurement-notices) | EU TED notices | $2 / 1,000 |
| 4 | [`suumo-japan-rental-scraper`](https://apify.com/livable_handloom/suumo-japan-rental-scraper) | SUUMO rental listings (Tokyo, Osaka, …) | $2 / 1,000 |
| 5 | [`kalshi-polymarket-scraper`](https://apify.com/livable_handloom/kalshi-polymarket-scraper) | Prediction-market odds and spreads | $3 / 1,000 |
| 6 | [`uk-tenders-scraper`](https://apify.com/livable_handloom/uk-tenders-scraper) | UK Contracts Finder + Find a Tender | $5 / 1,000 |
| 7 | [`austender-procurement-scraper`](https://apify.com/livable_handloom/austender-procurement-scraper) | AusTender OCDS + ATM | $5 / 1,000 |
| 8 | [`us-building-permits-scraper`](https://apify.com/livable_handloom/us-building-permits-scraper) | Five-city building permits | $5 / 1,000 |
| 9 | [`sec-capital-flow-scraper`](https://apify.com/livable_handloom/sec-capital-flow-scraper) | SEC Form D / Form 4 / 13F signals | $15 / 1,000 |
| 10 | `biopharma-fda-intel-scraper` | BioPharma + FDA feed | $8 / 1,000 · **coming soon** |
| 11 | `us-federal-grants-awards-scraper` | NIH + NSF + Grants.gov | $5 / 1,000 · **coming soon** |

Each run also has a $0.005 start fee. Prices are per dataset item and are listed on the
Actor page.

---

## Recipes

### Kimchi premium tracker (Upbit / Bithumb vs Kraken / Coinbase)

The **kimchi premium** is the gap between a coin's Korean won price and its USD price
abroad, converted at the live rate. The API returns both an all-in premium and every
Korean × global venue pair, so you can see *where* the spread is widest instead of trusting
one average.

```bash
python python/kimchi_premium_tracker.py --symbols BTC,ETH,XRP --min-premium 2
python python/kimchi_premium_tracker.py --watch 60 --kr upbit --global kraken
node   javascript/kimchi_premium.mjs --symbols=BTC,ETH,SOL
```

```
FX: 1 USD = 1,339.44 KRW  (2026-11-20, Frankfurter (European Central Bank reference rate))

COIN      KOREA (KRW)     USD EQUIV    GLOBAL (USD)   PREMIUM    SPREAD USD   BEST VENUE
--------  --------------  -----------  -------------  ---------  -----------  ------------------------------
BTC       79,707,000      59,507.71    57,853.15      +2.86%     1654.56      bithumb/coinbase +2.92%
ETH       2,257,000       1,685.03     1,639.04       +2.81%     45.99        upbit/coinbase +2.82%
XRP       1,233           0.92         0.90           +2.69%     0.02         bithumb/coinbase +2.78%
```

Endpoints: `GET /premium`, `GET /fx`, `GET /markets` · [Docs](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/korea-kimchi-premium-crypto-spread-api)

### Kalshi vs Polymarket arbitrage scanner

Two regulated-ish prediction markets list overlapping questions — US elections, Fed
decisions, crypto prices, sports. When both sides price the same event differently, the
YES gap is the trade candidate. The scanner matches questions by title similarity and
reports the spread, the match score and which side is higher.

```bash
python python/prediction_market_arbitrage.py --min-spread 2 --min-match 0.5
python python/prediction_market_arbitrage.py --mode markets --query "fed" --limit 10
node   javascript/prediction_markets.mjs --mode=arbitrage
```

Matching is deliberately strict: a loose match turns *"Netanyahu out"* and *"Israeli
election"* into a fake 40-point spread. The endpoint therefore often returns zero pairs;
lower `--min-match` to inspect weaker candidates, then read both questions yourself. Fees,
settlement rules and liquidity also have to be checked before anything is executable.

Endpoints: `GET /markets`, `GET /arbitrage` · [Docs](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/kalshi-polymarket-odds-arbitrage-api)

### US research grants finder (NIH RePORTER + NSF + Grants.gov)

Who already won money for a topic, and what is open to apply for now. Useful for research
commercialisation, grant-writing shops, university BD teams and competitor landscaping.

```bash
python python/federal_grants_finder.py --keyword crispr --source nih --min-amount 500000
python python/federal_grants_finder.py --mode opportunities --keyword quantum
python python/federal_grants_finder.py --mode feed --keyword battery --csv out/grants.csv
```

The response keeps NIH and NSF amounts distinct (`amountBasis`: one fiscal year vs estimated
total award), because adding them together silently would be wrong.

Endpoints: `GET /awards/search`, `GET /opportunities`, `GET /feed` · [Docs](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-federal-grants-r-d-awards-api)

### Company due diligence (GLEIF LEI + IRS Form 990 + Federal Register)

One name in, three public registers out: the legal entity and its parent chain from GLEIF,
US nonprofit finances from ProPublica's Form 990 mirror, and every US federal rule or notice
that mentions the name.

```bash
python python/entity_due_diligence.py --name "Tesla" --country US
python python/entity_due_diligence.py --name "Ford Foundation" --days 730
node   javascript/entity_diligence.mjs --name=Tesla
```

Output includes machine-readable `flags` (e.g. `HIGH_REGULATORY_ATTENTION`) and `signals`,
plus a disclaimer — this is a research aid, not a KYC system, credit rating or legal opinion.

Endpoints: `GET /due-diligence`, `/entities/search`, `/entities/{lei}`, `/nonprofits/search`,
`/nonprofits/{ein}`, `/regulations/search` · [Docs](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/global-entity-compliance-due-diligence-api)

### CFPB consumer complaints + HMDA mortgage denial rates

The CFPB complaint database is public and enormous (19.3M records) but the raw API is
awkward: company names are case-sensitive exact matches, offset paging is ignored, and the
latest two weeks are still filling in. This API resolves company names, slices by date
window and corrects for the publication lag, then joins the company to its HMDA mortgage
lending record (applications, denials, denial rate, average loan).

```bash
python python/consumer_finance_complaints.py --company "JPMORGAN CHASE & CO." --product Mortgage
python python/consumer_finance_complaints.py --mode trending --min-volume 100
python python/consumer_finance_complaints.py --mode company --company "Synchrony Bank"
```

Endpoints: `GET /complaints`, `/companies/search`, `/companies/trending`, `/company`,
`/products/benchmark` · host placeholder `us-consumer-finance-complaint-fair-lending-api.p.rapidapi.com`

### FEMA disaster declarations + NFIP flood claims

OpenFEMA's three registers normalised into one view: disaster declarations (one row per
designated area), Individual & Households Program aid with approval rates, and 2.7M NFIP
flood-insurance claim transactions with flood zone, occupancy and paid amounts. Location is
already redacted by FEMA — no names, no street addresses.

```bash
python python/disaster_flood_intel.py --mode disasters --state FL --year 2024
python python/disaster_flood_intel.py --mode flood --state LA --event Ida
python python/disaster_flood_intel.py --mode county --state FL --fips 12086
node   javascript/disaster_flood_loss.mjs --mode=flood --state=LA --event=Ida
```

NFIP payments are often zero or null; a zero payment is not a denied claim. The response
carries `totalsCover` so nobody mistakes row totals for the whole population.

Endpoints: `GET /disasters`, `/disaster`, `/assistance`, `/assistance/counties`,
`/flood/claims`, `/county` · host placeholder `us-disaster-flood-loss-intelligence-api.p.rapidapi.com`

### SEC Form D, Form 4 and 13F capital-flow signals

Private placements (Form D), insider buys and sells (Form 4) and institutional holdings
(13F-HR) from EDGAR, merged into one signal feed. This one is **Apify only**: SEC throttles
shared cloud egress IPs aggressively, so the Actor runs from dedicated addresses and retries
with pacing instead of returning empty results.

```bash
export APIFY_TOKEN=...
curl -s -X POST "https://api.apify.com/v2/acts/livable_handloom~sec-capital-flow-scraper/run-sync-get-dataset-items?token=$APIFY_TOKEN" \
  -H "Content-Type: application/json" -d '{"mode":"form4","daysBack":7,"maxResults":20}'
```

[Actor page](https://apify.com/livable_handloom/sec-capital-flow-scraper) · $15 / 1,000 records

### Government tenders: EU TED, UK Contracts Finder, AusTender

One table across three procurement systems, with buyer, value, currency, publication date,
deadline and the original notice URL.

```bash
python python/gov_tenders_monitor.py --region all --keyword solar --days 30
python python/gov_tenders_monitor.py --region uk --stage award --min-value 1000000
python python/gov_tenders_monitor.py --region au --source apify --keyword ICT --csv out/au.csv
```

```
REG   PUBLISHED   DEADLINE    BUYER                     VALUE      CUR   TITLE
----  ----------  ----------  ------------------------  ---------  ----  --------------------------------------------------------
EU    2026-11-19  2026-11-27  Ville de Morangis         7.20M      EUR   France - Construction work for buildings relating to le…
UK    2026-11-18  2026-12-15  Plus Dane Housing Ltd.    500.0K     GBP   GB-Bootle: Stanley Road, Bootle - Roof Terrace Refurbish…
```

RapidAPI endpoints: `/uk/tenders`, `/au/tenders`, `/eu/tenders`.
Apify Actors: [`uk-tenders-scraper`](https://apify.com/livable_handloom/uk-tenders-scraper),
[`austender-procurement-scraper`](https://apify.com/livable_handloom/austender-procurement-scraper)

### Korea IPO calendar & apartment cheongyak export

The Korean IPO pipeline from 38.co.kr — subscription windows, book-building competition
rates, lock-up commitments, final offer price, and how each listing traded against its offer
— and the government 청약홈 sale calendar with per-house-type prices, competition rates and
award-score ranges. Both are published only in Korean HTML, which is why a scraper is the
only practical access.

```bash
python python/korea_ipo_cheongyak_export.py --market ipo --mode demandForecastResults
python python/korea_ipo_cheongyak_export.py --market cheongyak --mode competition --pages 5
python python/korea_ipo_cheongyak_export.py --list-modes
```

```
COMPANY           MODE              START       END         BAND LOW   BAND HIGH   FINAL     STATUS
----------------  ----------------  ----------  ----------  ---------  ----------  --------  --------
이나인페이        공모주 청약일정   2026-12-16  2026-12-17  7,500      10,500      -         upcoming
제논              공모주 청약일정   2026-12-14  2026-12-15  9,700      12,200      -         upcoming
```

Actors: [`korea-ipo-calendar`](https://apify.com/livable_handloom/korea-ipo-calendar) ($10 / 1,000),
[`korea-cheongyak-calendar`](https://apify.com/livable_handloom/korea-cheongyak-calendar) ($8 / 1,000)

### FDA recalls, clinical trials, 510(k) and drug approvals

A single feed over ClinicalTrials.gov v2 and openFDA: studies updated in a window, recall
enforcement reports by class, 510(k) device clearances and Drugs@FDA original approvals.

```bash
python python/biopharma_fda_watch.py --mode feed --keyword oncology --days 14
python python/biopharma_fda_watch.py --mode recalls --classification "Class I"
python python/biopharma_fda_watch.py --mode trials --status recruiting --keyword diabetes
```

Endpoints: `GET /intel/feed`, `/trials`, `/fda/recalls`, `/fda/devices-510k`,
`/fda/drug-approvals` · [Docs](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/biopharma-fda-regulatory-intel-api)

### US building permits lead list

Five city open-data portals (NYC, Chicago, Austin, Seattle, San Francisco) normalised into
one permit schema, then ranked with a transparent lead score. Owner and applicant names,
emails, phones and unit numbers are removed before a record reaches you; company names stay,
because a contractor is the part a supplier can actually call.

```bash
python python/us_building_permits_leads.py --cities nyc,chicago --days 14 --min-cost 100000
python python/us_building_permits_leads.py --keyword solar --work-type renovation
python python/us_building_permits_leads.py --source apify --min-cost 250000
```

The score in `lead_score()` is deliberately simple and editable: construction value (log
scale, up to 55), work type (+20 new construction, +12 renovation, +6 trade), a named
contractor (+10), multi-unit or large floor area (+8).

Endpoints: `GET /us/permits` · [Docs](https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-building-permits-api4)

---

## Data sources and licences

Everything here repackages data that a government, exchange or official register already
publishes, in the public and redacted form the source releases. The code adds no personal
data of its own and keeps every redaction the source applies.

| Dataset | Original source | Licence / terms |
|---------|-----------------|-----------------|
| Prediction-market odds | Polymarket Gamma API, Kalshi public market API | public venue APIs |
| UK tenders | Contracts Finder, Find a Tender (OCDS) | Open Government Licence v3 |
| Australia tenders | AusTender OCDS (Department of Finance) | CC BY 3.0 AU |
| EU tenders | TED — Tenders Electronic Daily (v3 API) | EU open data |
| US building permits | NYC, Chicago, Austin, Seattle, SF open-data portals | city open-data terms |
| FDA and trials | ClinicalTrials.gov v2, openFDA | public domain / CC0 |
| US grants | NIH RePORTER, NSF Awards, Grants.gov | US government public data |
| Kimchi premium | Upbit, Bithumb, Kraken, Coinbase tickers; ECB rate via Frankfurter | exchange public tickers |
| Corporate due diligence | GLEIF LEI, ProPublica Nonprofit Explorer (IRS 990), Federal Register | CC0 / public domain |
| CFPB complaints | CFPB Consumer Complaint Database | CC0 |
| HMDA lending | FFIEC / CFPB HMDA Data Browser | public data |
| FEMA disasters and flood | OpenFEMA v2 / NFIP v3 | public domain |
| SEC filings | SEC EDGAR | US government public data |
| Korea IPO | 38.co.kr (38커뮤니케이션) | public company-level pages |
| Korea cheongyak | 청약홈 applyhome.co.kr (한국부동산원) | public project-level pages |

The **code** in this repository is MIT licensed. The **data** keeps the licence of its
source; check the source terms before redistributing a dataset.

---

## Pricing and limits

**RapidAPI** — identical plans on every listing:

| Plan | Price | Requests / month |
|------|-------|------------------|
| BASIC | free | 100 (hard limit) |
| PRO | $9.99 | 10,000 |
| ULTRA | $29.99 | 50,000 |
| MEGA | $79.99 | 250,000 |

**Apify** — pay per event: $0.005 start + the per-record price in the
[Apify catalog](#apify-actors--bulk-dataset-runs). A 100-record run of the Korean IPO Actor costs about $1.005.

Practical notes:

- Responses are cached inside the API for 15 seconds to 5 minutes depending on the dataset,
  so repeated polling is cheap.
- The CFPB and FEMA datasets publish on a lag; the API reports `dataFreshness` and windows
  rather than pretending the newest day is complete.
- `limit` caps are enforced per endpoint (usually 100 rows) because the upstream sources
  paginate differently.

---

## FAQ

### Do I need a paid plan?

No. Every RapidAPI listing has a free BASIC plan with 100 requests per month, which is
enough to evaluate the data and run the examples. Apify Actors can be tried on the free
plan with monthly credits.

### Is one RapidAPI key enough for all of them?

Yes. Subscribe to each API once with the same account; the same `X-RapidAPI-Key` then works
for every host in the catalog.

### Why is SEC Capital Flow not on RapidAPI?

SEC rate-limits shared cloud egress IPs hard enough that a shared-hosted proxy returns
throttled or empty results under load. Rather than sell a flaky endpoint, SEC data is served
by the Apify Actor, which runs from dedicated addresses with pacing and retries. The RapidAPI
listing is kept private until that changes.

### Why does the arbitrage endpoint return zero pairs?

Because strict matching is the honest default. Loosening the title match produces pairs like
"Will Netanyahu be PM" vs "Will Israel hold an election" with a huge fake spread. Treat any
pair as a *candidate*: read both rules, check fees and liquidity, then decide.

### Does this repository handle personal data?

No. Each dataset is the public, redacted release from its source: building permits arrive
without owner/applicant names, emails, phones or unit numbers; NFIP claims are FEMA-redacted
(no names, rounded locations); complaints and corporate records are the public registers
themselves. The scripts make no requests of their own and collect nothing about you.

### Can I run the examples in CI?

Yes. `make check` compiles every Python file, syntax-checks every `.mjs`, and runs each
`--demo`, so a broken sample or typo fails the build without needing any API key.

### Why Python 3.9+ and Node 18+?

Both are the oldest versions with everything used here (`urllib` behaviour, `fetch` as a
global). Nothing outside the standard library is required.

---

## Repository layout

```
kdatalab-public-data-examples/
├── README.md
├── LICENSE                     MIT
├── .env.example                RAPIDAPI_KEY / APIFY_TOKEN
├── .gitignore
├── requirements.txt            empty on purpose - standard library only
├── package.json                ES modules, Node 18+
├── Makefile                    make check
├── PLACEHOLDERS.md             setup history: every placeholder that was replaced
├── .github/workflows/ci.yml    py_compile + every --demo on Python 3.9/3.12 and Node 18/20
├── python/
│   ├── kdatalab_client.py      tiny shared client (RapidAPI + Apify + demo)
│   ├── kimchi_premium_tracker.py
│   ├── prediction_market_arbitrage.py
│   ├── federal_grants_finder.py
│   ├── entity_due_diligence.py
│   ├── consumer_finance_complaints.py
│   ├── disaster_flood_intel.py
│   ├── korea_ipo_cheongyak_export.py
│   ├── gov_tenders_monitor.py
│   ├── biopharma_fda_watch.py
│   └── us_building_permits_leads.py
├── javascript/
│   ├── client.mjs
│   ├── kimchi_premium.mjs
│   ├── prediction_markets.mjs
│   ├── entity_diligence.mjs
│   └── disaster_flood_loss.mjs
├── curl/
│   └── quickstart.sh           one-line curl for APIs 1-11 + Apify
├── samples/                    captured and illustrative responses used by --demo
└── docs/
    ├── API_REFERENCE.md        endpoint and parameter tables
    └── SEO_TOPICS.md           repository description, topics and keyword map
```

---

## Status and roadmap

| Item | State |
|------|-------|
| RapidAPI 1, 2, 3, 4, 6, 7, 8, 9, 10, 11 | public, BASIC free plan + 3 paid tiers |
| RapidAPI 5 (SEC) | private; served by the Apify Actor |
| Apify 1-9 | public, pay per event |
| Apify 10 (BioPharma), 11 (Grants) | coming soon (identity verification on the seller account) |
| Developer hub site | `https://k-data-lab.pages.dev` |

---

## Contributing

Issues and pull requests are welcome — especially a broken endpoint, a source that changed
its schema, or a cleaner example for a dataset. Run `make check` before opening a PR.

## Disclaimer

This project is not affiliated with RapidAPI, Apify, Polymarket, Kalshi, the CFPB, FEMA,
the SEC, the European Union, the UK government, the Australian Department of Finance, NIH,
NSF, or any Korean government agency. Data is provided as-is for research and engineering.
Nothing here is investment, legal, tax or credit advice.

## License

[MIT](LICENSE) © 2026 K-Data Lab
