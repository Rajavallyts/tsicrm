#!/usr/bin/env bash
#
# Applies TSI's Notes Like/Comment UI to apps/crm and rebuilds the frontend.
#
# This is a recovery tool, not a migration step — nothing in tsicrm's patches.txt
# runs it. Use it after apps/crm is reset, re-cloned or upgraded. See README.md in
# this directory for why the diff cannot live inside a Frappe app.

set -euo pipefail

BENCH="${BENCH:-/home/thiru/frappe-bench2}"
CRM="$BENCH/apps/crm"
PATCH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/notes_like_comment.patch"
TARGETS=(
	"frontend/src/components/Activities/NoteArea.vue"
	"frontend/src/components/Activities/Activities.vue"
)

[ -d "$CRM" ] || { echo "no crm app at $CRM" >&2; exit 1; }
[ -f "$PATCH" ] || { echo "missing $PATCH" >&2; exit 1; }

# Already applied? Check for a marker unique to the CURRENT patch content, not just
# any older version of it — toggleLike existed since v1, so grepping for it alone
# would falsely say "already applied" after the patch itself gets updated (v1/v2 ->
# v3) even though the target file is still on the older version. toggle_note_like is
# the call this latest patch introduces.
if grep -q 'toggle_note_like' "$CRM/${TARGETS[0]}"; then
    echo "already applied: ${TARGETS[0]} already references toggle_note_like — nothing to do."
    echo "(if you expected this to apply a NEWER patch, git checkout -- the two files"
    echo " below first, so this guard isn't matching a stale version:)"
    for t in "${TARGETS[@]}"; do echo "   $t"; done
    exit 0
fi

echo "checking patch against $CRM ..."
if ! git -C "$CRM" apply --check "$PATCH"; then
    cat >&2 <<'MSG'

The patch no longer applies. Upstream has changed NoteArea.vue or Activities.vue
around one of the edited spots. Re-apply the Like/Comment footer and the
single-column grid change by hand, then re-capture the diff as described in
README.md — do not force it.
MSG
    exit 1
fi

git -C "$CRM" apply "$PATCH"
echo "applied."

echo "rebuilding the CRM frontend (this takes a couple of minutes) ..."
yarn --cwd "$CRM/frontend" install
NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=4096}" yarn --cwd "$CRM/frontend" build

echo
echo "Done. Clear the site cache and restart the web tier, then open a Lead or"
echo "Deal's Notes tab: notes should render full-width, single column, each with"
echo "a Like (heart) and Comment (speech bubble) row at the bottom."
