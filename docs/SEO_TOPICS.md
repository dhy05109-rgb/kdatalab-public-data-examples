# SEO and discovery plan

The goal of the repository is not stars for their own sake: it is to be the page a developer
lands on when they search for one of these datasets, and to make the paid API the obvious
next click. That means the **repository name, description, topics, README headings and file
names** all have to carry the same real search phrases.

## 1. Repository name

**Recommended:** `kdatalab-public-data-examples`

Why:

- `public data` and `examples` are the two words used in most GitHub searches for this space
  ("public data api examples", "open data python examples").
- The `kdatalab` prefix builds the brand across RapidAPI, Apify and the hub site.
- It stays readable in a URL and does not promise a specific dataset, so the repo can grow.

Alternatives if the primary is taken:

| Name | When to use it |
|------|----------------|
| `awesome-public-data-apis-starter` | if you want the "awesome list" search traffic; slightly overused |
| `public-data-api-recipes` | if the emphasis is on short, copyable recipes |
| `kdatalab-starter-kit` | if the repo later covers non-data tooling too |

Do **not** name it after one dataset (`kimchi-premium-api`): it would cap the repo at one
keyword and one audience.

## 2. Repository description (the "About" field, ≤ 350 characters)

Primary:

> Runnable Python & JavaScript examples for 11 public-data APIs and scrapers: prediction-market odds, government tenders, building permits, FDA, research grants, kimchi premium, company due diligence, CFPB, FEMA and Korean IPO data. No dependencies, no keys needed for `--demo`.

Short variant (for places that truncate):

> 11 public-data APIs and scrapers with runnable Python/JS examples — prediction markets, tenders, permits, FDA, grants, kimchi premium, due diligence, CFPB, FEMA, Korean IPO.

## 3. Topics (all 20 slots)

```
public-data
open-data
api-client
rapidapi
apify
python
javascript
prediction-markets
polymarket
kalshi
kimchi-premium
crypto-arbitrage
government-tenders
building-permits
fda
clinical-trials
korea-ipo
gleif
cfpb
data-engineering
```

Deliberately mixed: 6 broad (`python`, `javascript`, `public-data`, `open-data`, `api-client`,
`data-engineering`) for discovery, 14 specific for intent. GitHub allows 20; do not waste a
slot on `awesome` or `hacktoberfest`.

## 4. Keyword → file map

Each script's docstring, filename and README heading should agree on one primary phrase.

| File | Primary keyword | Secondary keywords |
|------|-----------------|--------------------|
| `python/kimchi_premium_tracker.py` | kimchi premium tracker | upbit bithumb kraken coinbase, korea crypto arbitrage, usd krw spread |
| `python/prediction_market_arbitrage.py` | kalshi polymarket arbitrage | prediction market api, polymarket odds api, event contract spread |
| `python/federal_grants_finder.py` | nih grants api / nsf awards | grants.gov opportunities, research funding api, federal grant search |
| `python/entity_due_diligence.py` | gleif lei api | propublica form 990, federal register api, company due diligence api |
| `python/consumer_finance_complaints.py` | cfpb complaints api | hmda denial rate, consumer complaint database, fair lending data |
| `python/disaster_flood_intel.py` | fema disaster api | nfip flood claims, openfema, flood loss data |
| `python/korea_ipo_cheongyak_export.py` | korea ipo calendar api | 공모주 청약일정, cheongyak api, korea apartment subscription |
| `python/gov_tenders_monitor.py` | government tenders api | eu ted api, uk contracts finder, austender, public procurement |
| `python/biopharma_fda_watch.py` | fda recalls api | clinicaltrials.gov api, 510k clearance, drug approval data |
| `python/us_building_permits_leads.py` | building permits api | construction lead list, nyc permit data, contractor leads |
| `javascript/*.mjs` | same as their Python twin | add "javascript", "node fetch" |
| `curl/quickstart.sh` | public data api curl | rapidapi curl example |

README headings are already written as `<dataset> (<sources>)` — keep that pattern when
adding a recipe, because GitHub indexes headings as anchors and Google shows them in
snippets.

## 5. Repository settings checklist

- [ ] **About**: description above, website `https://k-data-lab.pages.dev` once the hub site is live.
- [ ] **Topics**: all 20 above.
- [ ] **Social preview**: 1280×640 card with the title and the 11 dataset names (add later).
- [ ] **Releases**: tag `v1.0.0` with a short changelog; a release page is indexed.
- [ ] **README first 160 characters**: must contain "public data APIs" and the strongest
  datasets (prediction markets, tenders, permits) because that is the meta description.
- [ ] **Pin** the repository on the profile so it is the first thing a visitor sees.
- [ ] **Discussions** on (optional): question pages rank for long-tail queries.

## 6. Launch copy

**X / Twitter**

> 11 public-data APIs, one starter kit.
>
> Prediction markets · EU/UK/AU tenders · US permits · FDA · NIH grants · kimchi premium ·
> GLEIF due diligence · CFPB · FEMA flood · Korean IPO/청약
>
> Python + JS, zero dependencies, `--demo` works without a key.
> [repo link]

**Hacker News (Show HN)**

> Show HN: Runnable examples for 11 public-data APIs (prediction markets, tenders, FEMA)

**Reddit** (`r/datasets`, `r/Python`, `r/algotrading` — read each sub's self-promotion rules
first): lead with the free `--demo` and the data-source table, not the paid plans.

## 7. What to avoid

- Keyword stuffing in the README title (`Public Data API Open Data API Free API …`) — it
  reads as spam and GitHub search weighs the description and topics more.
- Promising "free" for data that is metered. Say "free BASIC plan, 100 requests/month".
- Publishing unverified endpoint paths. Every path in this repo is taken from the deployed
  OpenAPI spec; keep it that way when adding recipes.
