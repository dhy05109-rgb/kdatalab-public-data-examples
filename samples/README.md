# Sample responses

Every example runs `--demo` without a key and renders one of these files. Two kinds:

| Kind | Meaning | Files |
|------|---------|-------|
| `captured` | trimmed from a real response, taken from the live API on the date in `_sample.capturedAt` | `kimchi_premium`, `entity_due_diligence`, `grants_*`, `cfpb_*`, `fema_*`, `flood_claims`, `fda_*`, `korea_ipo`, `korea_cheongyak` |
| `illustrative` | hand-built in the shape documented by the API (the published OpenAPI example), because the dataset was too large or the response was empty to trim | `prediction_markets`, `prediction_arbitrage`, `tenders_uk`, `tenders_au`, `tenders_eu`, `us_permits` |

Each file carries a `_sample` object with `kind`, `note` and, when captured, `capturedAt`.
The demo banner prints that note, so a reader always knows whether they are looking at real
data or an example shape.

Rows are trimmed to 1–5 records to keep the repository small and to avoid shipping a whole
dataset. Lists inside a record (e.g. `venues[]`) are sometimes cut to two entries; the note
says so.

## Refreshing a sample

```bash
export RAPIDAPI_KEY=...
python python/kimchi_premium_tracker.py --symbols BTC,ETH,XRP --json > samples/kimchi_premium.json
```

Then add the `_sample` object back (it is stripped by `--json`) and keep only a few rows.
Captured samples should never contain a key, a token, or personal data.
