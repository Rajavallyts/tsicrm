#!/usr/bin/env bash
#
# Adds a "Notes" tab to a Client (CRM Organization)'s detail page and rebuilds
# the frontend.
#
# This is a recovery tool, not a migration step -- nothing in tsicrm's patches.txt
# runs it. Use it after apps/crm is reset, re-cloned or upgraded. See README.md in
# this directory for why the diff cannot live inside a Frappe app.
#
# The backend half of this feature -- get_organization_activities in
# tsicrm/tsicrm/crm_overrides/activities.py -- needs no patch at all; it's a
# normal tsicrm-owned whitelisted-method override, already deployed the same
# way as every other file in tsicrm/tsicrm/crm_overrides/. This script only
# covers the one piece Frappe has no hook for: the Vue page itself.

set -euo pipefail

BENCH="${BENCH:-/home/thiru/frappe-bench2}"
CRM="$BENCH/apps/crm"
PATCH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/organization_notes.patch"
TARGET="frontend/src/pages/Organization.vue"

[ -d "$CRM" ] || { echo "no crm app at $CRM" >&2; exit 1; }
[ -f "$PATCH" ] || { echo "missing $PATCH" >&2; exit 1; }

# Already applied? notesTabs is the marker this patch introduces -- it doesn't
# exist anywhere upstream.
if grep -q 'notesTabs' "$CRM/$TARGET"; then
    echo "already applied: $TARGET already references notesTabs — nothing to do."
    echo "(if you expected this to apply a NEWER patch, git checkout -- the file"
    echo " below first, so this guard isn't matching a stale version:)"
    echo "   $TARGET"
    exit 0
fi

echo "checking patch against $CRM ..."
if ! git -C "$CRM" apply --check "$PATCH"; then
    cat >&2 <<'MSG'

The patch no longer applies. Upstream has changed Organization.vue around one
of the edited spots. Re-apply the Notes tab (the Activities import, the
notesTabs constant, the "Notes" tab entry, and the <Activities> branch in the
tab-panel template) by hand, then re-capture the diff as described in
README.md -- do not force it.
MSG
    exit 1
fi

git -C "$CRM" apply "$PATCH"
echo "applied."

echo "rebuilding the CRM frontend (this takes a couple of minutes) ..."
yarn --cwd "$CRM/frontend" install
NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=4096}" yarn --cwd "$CRM/frontend" build

echo
echo "Done. Clear the site cache and restart the web tier, then open a Client:"
echo "there should now be a Notes tab alongside Deals and Contacts, with the"
echo "same New Note / Like / Comment behaviour as a Lead or Deal's Notes tab."
