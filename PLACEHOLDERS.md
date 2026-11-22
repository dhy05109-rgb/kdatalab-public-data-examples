# Placeholders — status log

> **Update:** All 10 public RapidAPI listings (`us-consumer-finance-complaint-fair-lending-api`
> and `us-disaster-flood-loss-intelligence-api` included) and the Cloudflare Pages hub
> (`https://k-data-lab.pages.dev`) are now live and replaced in all files. This document
> is kept for reference.

| Marker | Meaning | Replace with |
|--------|---------|--------------|
| `us-consumer-finance-complaint-fair-lending-api.p.rapidapi.com` | RapidAPI 10 (CFPB complaints + HMDA) gateway host | the listing's `X-RapidAPI-Host`, expected `us-consumer-finance-complaint-fair-lending-api.p.rapidapi.com` |
| `us-disaster-flood-loss-intelligence-api.p.rapidapi.com` | RapidAPI 11 (FEMA + NFIP) gateway host | the listing's `X-RapidAPI-Host`, expected `us-disaster-flood-loss-api.p.rapidapi.com` |
| `https://k-data-lab.pages.dev` | the Cloudflare Pages developer hub | `https://<project>.pages.dev` or the custom domain |

## Where each marker appears

| Marker | Files |
|--------|-------|
| `us-consumer-finance-complaint-fair-lending-api.p.rapidapi.com` | `README.md` (catalog row), `python/consumer_finance_complaints.py` (`HOST`), `curl/quickstart.sh` (entry 10), `docs/API_REFERENCE.md` (section 10) |
| `us-disaster-flood-loss-intelligence-api.p.rapidapi.com` | `README.md` (catalog row), `python/disaster_flood_intel.py` (`HOST`), `javascript/disaster_flood_loss.mjs` (`HOST`), `curl/quickstart.sh` (entry 11), `docs/API_REFERENCE.md` (section 11) |
| `https://k-data-lab.pages.dev` | `README.md` (status table), `docs/SEO_TOPICS.md` (settings checklist) |

## Replace all occurrences

Run from the repository root (macOS users: `sed -i ''` instead of `sed -i`).

```bash
# 10 - CFPB + HMDA
grep -rl '\[PENDING_10_URL\]' . --exclude-dir=.git \
  | xargs sed -i 's|\[PENDING_10_URL\]|us-consumer-finance-complaint-fair-lending-api.p.rapidapi.com|g'

# 11 - FEMA + NFIP
grep -rl '\[PENDING_11_URL\]' . --exclude-dir=.git \
  | xargs sed -i 's|\[PENDING_11_URL\]|us-disaster-flood-loss-api.p.rapidapi.com|g'

# hub site
grep -rl '\[PENDING_HUB_URL\]' . --exclude-dir=.git \
  | xargs sed -i 's|\[PENDING_HUB_URL\]|https://YOUR-HUB.pages.dev|g'
```

## Verify

```bash
grep -rn 'PENDING_' . --exclude-dir=.git --exclude-dir=.cache
# expect no output
make check
```

The scripts also fail closed: while a host is still a marker, live mode prints
"… is not published yet" instead of calling a bogus host, and `--demo` still works.

## Second-step edits after 10 and 11 are public

These are not markers because they are sentences, not hosts:

1. `README.md` catalog rows for 10 and 11: change **publishing** to **live**, and turn the
   names into links to
   `https://rapidapi.com/%EA%B9%80%ED%83%9C%EC%9A%B1/api/us-consumer-finance-complaint-fair-lending-api`
   and `…/us-disaster-flood-loss-api` (use the final slug — check the listing URL, RapidAPI
   may append a number if the slug is taken).
2. `README.md` Apify catalog rows 10 and 11: drop **coming soon** and add links to
   `https://apify.com/livable_handloom/biopharma-fda-intel-scraper` and
   `https://apify.com/livable_handloom/us-federal-grants-awards-scraper` once the Actors are
   public (they need the seller's identity verification first).
3. `README.md` status table: update the three rows to match.
4. `curl/quickstart.sh`: nothing else — the entries pick up the replacement automatically.
5. Re-run `bash curl/quickstart.sh --run 10` and `--run 11` with a real key before announcing.
