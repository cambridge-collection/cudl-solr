#!/usr/bin/env bash
# Post Solr JSON item files to a Solr core the way cudl-search's PUT /item
# does: one Solr document per entry in "pages", with the item-level fields
# copied onto each.
#
# Usage: scripts/index_solr_json.sh FILE_OR_DIR...
#   SOLR_URL  core URL (default http://localhost:8983/solr/cdcp)
#   JOBS      parallel posts (default 4)
#
# Failed files are listed on stderr; the exit status is non-zero if any fail.
set -euo pipefail

SOLR_URL=${SOLR_URL:-http://localhost:8983/solr/cdcp}
JOBS=${JOBS:-4}

if [ "$#" -eq 0 ]; then
    echo "Usage: $0 FILE_OR_DIR..." >&2
    exit 2
fi

post_one() {
    local response
    response=$(curl -s -X POST -H 'Content-Type: application/json; charset=UTF-8' \
        "$SOLR_URL/update/json/docs?split=/pages&f=/pages/*&f=/*" --data-binary @"$1")
    if ! grep -q '"status":0' <<<"$response"; then
        echo "FAILED $1: $(grep -o '"msg":"[^"]*' <<<"$response" | head -c 200)" >&2
        return 1
    fi
}
export -f post_one
export SOLR_URL

status=0
find "$@" -name '*.json' -type f -print0 \
    | xargs -0 -P "$JOBS" -I{} bash -c 'post_one "$1"' _ {} || status=$?

curl -s "$SOLR_URL/update?commit=true" >/dev/null
exit "$status"
