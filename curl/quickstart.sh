#!/usr/bin/env bash
# K-Data Lab - one-line curl samples for every RapidAPI listing (1-11).
#
#   ./quickstart.sh              # print every request (no key needed)
#   ./quickstart.sh 8            # print one request
#   ./quickstart.sh --run 8      # actually call API 8 (needs RAPIDAPI_KEY)
#   export RAPIDAPI_KEY=... && ./quickstart.sh --run all
#
# Apify examples are at the bottom; they need APIFY_TOKEN instead of a RapidAPI key.

set -euo pipefail

KEY="${RAPIDAPI_KEY:-YOUR_KEY}"

# number|name|host|path+query
ENTRIES=(
  "1|Prediction markets (Kalshi + Polymarket)|kalshi-polymarket-odds-arbitrage-api.p.rapidapi.com|/markets?limit=3"
  "2|UK + Australia tenders|uk-australia-government-tenders-api.p.rapidapi.com|/uk/tenders?days=30&limit=3"
  "3|EU TED procurement|eu-ted-public-procurement-api.p.rapidapi.com|/eu/tenders?keyword=solar&days=30&limit=3"
  "4|US building permits|us-building-permits-api4.p.rapidapi.com|/us/permits?daysBack=14&limit=3"
  "5|SEC capital flow (Apify only - RapidAPI listing is private)|[APIFY_ONLY]|sec-capital-flow-scraper"
  "6|BioPharma + FDA intel|biopharma-fda-regulatory-intel-api.p.rapidapi.com|/intel/feed?days=30&limit=3"
  "7|US federal grants + R&D awards|us-federal-grants-r-d-awards-api.p.rapidapi.com|/awards/search?keyword=crispr&limit=3"
  "8|Korea kimchi premium + FX|korea-kimchi-premium-crypto-spread-api.p.rapidapi.com|/premium?symbols=BTC,ETH"
  "9|Global entity + compliance due diligence|global-entity-compliance-due-diligence-api.p.rapidapi.com|/due-diligence?name=Tesla&country=US"
  "10|US consumer finance complaints + HMDA|us-consumer-finance-complaint-fair-lending-api.p.rapidapi.com|/complaints?product=Mortgage&days=30&limit=3"
  "11|US disaster + flood loss|us-disaster-flood-loss-intelligence-api.p.rapidapi.com|/flood/claims?state=LA&event=Ida&limit=3"
)

print_entry() {
  local entry="$1"
  IFS='|' read -r number name host path <<<"$entry"
  if [[ "$host" == "[APIFY_ONLY]" ]]; then
    printf '# %s. %s\n' "$number" "$name"
    print_apify_sec
    return 0
  fi
  printf '# %s. %s\n' "$number" "$name"
  printf 'curl -s "https://%s%s" -H "X-RapidAPI-Key: %s" -H "X-RapidAPI-Host: %s"\n\n' \
    "$host" "$path" "$KEY" "$host"
}

print_apify_sec() {
  printf 'curl -s -X POST "https://api.apify.com/v2/acts/livable_handloom~sec-capital-flow-scraper/run-sync-get-dataset-items?token=$APIFY_TOKEN" -H "Content-Type: application/json" -d '\''{"mode":"all","daysBack":7,"maxResults":20}'\''\n\n'
}

run_entry() {
  local entry="$1"
  IFS='|' read -r number name host path <<<"$entry"
  if [[ "$host" == "[APIFY_ONLY]" ]]; then
    printf '# %s. %s runs on Apify; see the Apify block below\n' "$number" "$name" >&2
    return 0
  fi
  if [[ "$host" == \[*\] ]]; then
    printf '# %s. %s is not published yet (placeholder %s) - skipped\n' "$number" "$name" "$host" >&2
    return 0
  fi
  printf '# %s. %s\n' "$number" "$name" >&2
  curl -sS "https://${host}${path}" \
    -H "X-RapidAPI-Key: ${KEY}" \
    -H "X-RapidAPI-Host: ${host}" \
    -H "Accept: application/json"
  printf '\n'
}

main() {
  local mode="print" target="all"
  if [[ "${1:-}" == "--run" ]]; then
    mode="run"
    target="${2:-all}"
    if [[ -z "${RAPIDAPI_KEY:-}" ]]; then
      echo "RAPIDAPI_KEY is not set. Export it first, or run without --run to print the commands." >&2
      echo "  export RAPIDAPI_KEY='your-key'   # free BASIC plan: 100 requests/month" >&2
      exit 2
    fi
  elif [[ -n "${1:-}" ]]; then
    target="$1"
  fi

  local found=0
  for entry in "${ENTRIES[@]}"; do
    IFS='|' read -r number _ _ _ <<<"$entry"
    if [[ "$target" == "all" || "$target" == "$number" ]]; then
      found=1
      if [[ "$mode" == "run" ]]; then run_entry "$entry"; else print_entry "$entry"; fi
    fi
  done
  if [[ "$found" == "0" ]]; then
    echo "Unknown API number: $target (use 1-11 or all)" >&2
    exit 1
  fi

  if [[ "$mode" == "print" && "$target" == "all" ]]; then
    cat <<'APIFY'
# --- Apify Actors (token auth, per-1,000-record pricing) ----------------------
# export APIFY_TOKEN='apify_api_...'
# Korea IPO calendar:
curl -s -X POST "https://api.apify.com/v2/acts/livable_handloom~korea-ipo-calendar/run-sync-get-dataset-items?token=$APIFY_TOKEN" -H "Content-Type: application/json" -d '{"mode":"subscriptionSchedule","maxItems":20}'
# Korea apartment subscription (cheongyak):
curl -s -X POST "https://api.apify.com/v2/acts/livable_handloom~korea-cheongyak-calendar/run-sync-get-dataset-items?token=$APIFY_TOKEN" -H "Content-Type: application/json" -d '{"mode":"announcements","maxItems":20}'
# UK tenders:
curl -s -X POST "https://api.apify.com/v2/acts/livable_handloom~uk-tenders-scraper/run-sync-get-dataset-items?token=$APIFY_TOKEN" -H "Content-Type: application/json" -d '{"keyword":"software","maxItems":20}'
# Australia tenders:
curl -s -X POST "https://api.apify.com/v2/acts/livable_handloom~austender-procurement-scraper/run-sync-get-dataset-items?token=$APIFY_TOKEN" -H "Content-Type: application/json" -d '{"daysBack":7,"maxItems":20}'
APIFY
  fi
}

main "$@"
