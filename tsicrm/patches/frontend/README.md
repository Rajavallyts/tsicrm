# The pieces of TSICRM that cannot live in TSICRM

Frappe offers a hook by which one app can replace another app's *DocType controller*,
its *whitelisted method*, or its *desk form script* — but nothing by which one app can
replace another app's Vue component. The `/crm` portal UI is a compiled Vue SPA: the
component is built into a bundle at build time, and by the time any Python hook runs,
the decision has already been made. One diff has to be applied to `apps/crm` itself
for that reason, and the `.patch` file in this directory is the copy of record.

## `notes_like_comment.patch` — Like/Comment on the Notes tab

Adds a Like (heart + count, via the standard `frappe.desk.like.toggle_like`) and
Comment (speech bubble + count, flat replies — no nesting) row to the bottom of each
note card on a Lead/Deal's Notes tab, and drops the tab's grid down to a single,
full-width column so a card's height is driven by its content instead of a fixed
`h-48`. Comments reuse the generic `Comment` doctype pointed at the note
(`reference_doctype: "FCRM Note"`), posted through the same `crm.api.comment.add_comment`
whitelisted method the Lead/Deal comment box already calls — no new doctype, no
schema change on either side.

Two files carry the diff: `NoteArea.vue` (the card itself — the footer row and the
expandable thread) and `Activities.vue` (the one-line grid-class change for the Notes
tab). Neither touches the Like/Comment logic's data source directly — the
`_liked_by` and `comments_count` fields they read, and the two actions the footer
triggers (liking, reading the comment thread), all go through **tsicrm-owned
whitelisted methods** in `tsicrm/crm_overrides/activities.py`, registered via
`override_whitelisted_methods` in `hooks.py` — not by editing `apps/crm`. That part
needed no patch file at all — Frappe's whitelisted-method override hook covers it
cleanly, the same category of tool `tsilearn` uses for `lms.lms.utils.*`. This patch
is only for the two pieces Frappe has no hook for: the Vue template and its footer
markup.

Why the footer calls into `tsicrm.crm_overrides.activities` instead of the generic
Frappe/CRM endpoints directly: `frappe.client.get_list` (for reading comments) and
`frappe.desk.like.toggle_like` (for liking) both gate on permission checks that are
independent of, and narrower than, the org-hierarchy permission that actually governs
whether a user can see the note in the first place (permission on the parent Lead/
Deal). Both broke for non-Administrator roles that could already view and comment on
a note through the CRM's own permission model. `get_note_comments` and
`toggle_note_like` re-gate on the note's parent document instead — the same boundary
`get_activities` already uses — before doing the read/write, so a role that can see
the note can act on it.

| | |
|---|---|
| crm version | 1.82.0 |
| commit | `48cb3cccec12ef798f8faacc165fff3dc008a8fa` |
| branch | `main` |
| captured | 2026-08-31 (v3 — see changelog below) |

### Changelog

- **v1** — Like/Comment footer added to `NoteArea.vue`; single-column grid in
  `Activities.vue`. Comments read via `frappe.client.get_list` directly; likes via
  `frappe.desk.like.toggle_like` directly.
- **v2** — Comment reads moved to `tsicrm.crm_overrides.activities.get_note_comments`.
  `frappe.client.get_list` against `Comment` enforced `Comment`'s own DocPerm, which
  didn't grant non-Administrator roles read access — invisible when testing as
  Administrator, since Administrator bypasses all permission checks. Also fixed
  `_attach_notes_engagement`'s count query and this read to filter
  `comment_type: "Comment"`, since Frappe auto-creates a `comment_type: "Like"` row
  on every like and it was inflating both the count and the thread.
- **v3** — Likes moved to `tsicrm.crm_overrides.activities.toggle_note_like`. Same
  root cause as v2 but one level deeper: `frappe.desk.like.toggle_like` gates on
  `frappe.has_permission("FCRM Note", "read", doc=note)` — FCRM Note's own DocPerm
  plus Frappe's default user-permission check on its `reference_docname` link field —
  which is independent of the org-hierarchy check that actually governs note
  visibility. `toggle_note_like` gates on the parent Lead/Deal instead and performs
  the same `_liked_by` write `toggle_like` does.

Applying it:

```bash
/home/thiru/frappe-bench2/apps/tsicrm/tsicrm/patches/frontend/apply.sh
```

## Applying it

`apply.sh` checks the patch applies cleanly, applies it, and rebuilds the CRM
frontend. It refuses to run if the diff is already present, so it's safe to run
twice. The frontend build is memory-hungry — the script raises Node's heap limit for
it; if a build OOMs, retry with a higher `NODE_OPTIONS` `--max-old-space-size` rather
than assuming the diff itself is wrong.

## After a crm upgrade

`git apply` will fail as soon as upstream touches the surrounding lines of a patched
file. When it does, re-apply the Like/Comment footer and the grid-class change by
hand, then re-capture the diff:

```bash
git -C /home/thiru/frappe-bench2/apps/crm diff -- \
  frontend/src/components/Activities/Activities.vue \
  frontend/src/components/Activities/NoteArea.vue \
  > /home/thiru/frappe-bench2/apps/tsicrm/tsicrm/patches/frontend/notes_like_comment.patch
```

If the working tree's file *mode* bits have drifted from the repo (common on a
Windows-mounted checkout — `git status` shows every file as modified with nothing but
`old mode 100644` / `new mode 100755` lines), add `-c core.fileMode=false` before
`diff` so the captured patch stays limited to real content changes:

```bash
git -C /home/thiru/frappe-bench2/apps/crm -c core.fileMode=false diff -- \
  frontend/src/components/Activities/Activities.vue \
  frontend/src/components/Activities/NoteArea.vue \
  > /home/thiru/frappe-bench2/apps/tsicrm/tsicrm/patches/frontend/notes_like_comment.patch
```

Then update the table above. Keep the diff minimal — it has to survive every
upstream rebase, and every line added is a line to re-apply by hand later.
