"""
Overrides crm.api.activities.get_activities -- the single whitelisted method
the /crm portal's activity timeline calls (frontend/src/components/Activities/
Activities.vue calls it by this exact dotted path, and nothing inside apps/crm
calls it internally) -- to attach engagement data to each FCRM Note for the
Notes tab's Like/Comment feature: `_liked_by` (so the heart can show liked
state) and `comments_count` (so the count shows without expanding the card).

Registered via override_whitelisted_methods in hooks.py, the same category of
mechanism tsilearn uses to monkey-patch lms.lms.utils.* -- apps/crm stays
untouched; this app never edits it.

Because override_whitelisted_methods only intercepts the RPC dispatch (a call
by dotted-path string), not the Python function object, it works cleanly here
precisely because get_activities has exactly one call site anywhere: the
frontend's whitelisted RPC call. There's no second internal `from
crm.api.activities import get_activities` elsewhere in apps/crm to worry about
rebinding, unlike tsilearn's lms.lms.utils overrides.
"""

import json

import frappe
from frappe import _
from crm.api.activities import get_activities as _upstream_get_activities


@frappe.whitelist()
def get_activities(name: str):
	activities, calls, notes, tasks, attachments = _upstream_get_activities(name)
	notes = _attach_notes_engagement(notes)
	return activities, calls, notes, tasks, attachments


def _attach_notes_engagement(notes):
	"""Attach `_liked_by` and `comments_count` to each note dict.

	`_liked_by` isn't in the fields list the upstream query selects, so it's
	fetched here in one extra bulk query keyed by note name; `comments_count`
	is computed in one grouped query against the generic Comment doctype --
	comments on a note use the standard reference_doctype/reference_name
	pointer, same as Lead/Deal comments do.
	"""
	if not notes:
		return notes

	note_names = [note["name"] for note in notes]

	liked_by_rows = frappe.db.get_all(
		"FCRM Note",
		filters={"name": ("in", note_names)},
		fields=["name", "_liked_by"],
	)
	liked_by_note = {row.name: row._liked_by for row in liked_by_rows}

	count_rows = frappe.db.get_all(
		"Comment",
		filters={
			"reference_doctype": "FCRM Note",
			"reference_name": ("in", note_names),
			"comment_type": "Comment",
		},
		fields=["reference_name", "count(name) as count"],
		group_by="reference_name",
	)
	counts_by_note = {row.reference_name: row.count for row in count_rows}

	for note in notes:
		note["_liked_by"] = liked_by_note.get(note["name"])
		note["comments_count"] = counts_by_note.get(note["name"], 0)

	return notes



@frappe.whitelist()
def get_note_comments(note: str):
	"""Return the flat comment thread for one FCRM Note.

	frappe.client.get_list enforces the Comment doctype's own DocPerm, which on
	this site doesn't grant regular roles read access to Comment directly --
	Administrator only "worked" because Administrator bypasses every
	permission check. This mirrors how notes/likes/counts already work: gate
	on read access to the note's reference document (the same boundary
	get_activities uses), then read with frappe.db.get_all so Comment's own
	DocPerm doesn't get in the way of something the user is already allowed
	to see through the note.
	"""
	if not frappe.db.exists("FCRM Note", note):
		frappe.throw(_("Note not found"), frappe.DoesNotExistError)

	reference_doctype, reference_docname = frappe.db.get_value(
		"FCRM Note", note, ["reference_doctype", "reference_docname"]
	)
	if reference_doctype and reference_docname:
		if not frappe.has_permission(reference_doctype, "read", reference_docname):
			frappe.throw(_("Not permitted"), frappe.PermissionError)

	return frappe.db.get_all(
		"Comment",
		filters={
			"reference_doctype": "FCRM Note",
			"reference_name": note,
			"comment_type": "Comment",
		},
		fields=["name", "content", "owner", "creation"],
		order_by="creation asc",
	)


@frappe.whitelist()
def toggle_note_like(note: str, add: str = "Yes"):
	"""Toggle the current user's like on an FCRM Note.

	frappe.desk.like.toggle_like gates on frappe.has_permission("FCRM Note",
	"read", doc=note) -- FCRM Note's own DocPerm plus Frappe's default
	user-permission check on its reference_docname link field. That's a
	different, independently-evaluated boundary from the one that actually
	governs note visibility: get_lead_activities/get_deal_activities check
	permission on the parent CRM Lead/Deal only (via crm's own org-hierarchy
	permission hook, crm.permissions.org_hierarchy) and then fetch notes with
	a raw frappe.db.get_all query that bypasses FCRM Note's DocPerm entirely.
	A role that can already see and comment on a note can still get a
	PermissionError from toggle_like if it fails FCRM Note's own, unrelated
	permission check -- this is what happened for non-Administrator users.

	This mirrors get_note_comments: gate on read access to the note's parent
	document instead (the same boundary get_activities and get_note_comments
	already use), then perform the same write frappe.desk.like.toggle_like
	does -- a direct `_liked_by` update plus a "Liked" Comment row -- without
	routing through FCRM Note's own permission engine.
	"""
	if not frappe.db.exists("FCRM Note", note):
		frappe.throw(_("Note not found"), frappe.DoesNotExistError)

	reference_doctype, reference_docname = frappe.db.get_value(
		"FCRM Note", note, ["reference_doctype", "reference_docname"]
	)
	if reference_doctype and reference_docname:
		if not frappe.has_permission(reference_doctype, "read", reference_docname):
			frappe.throw(_("Not permitted"), frappe.PermissionError)

	user = frappe.session.user
	liked_by_value = frappe.db.get_value("FCRM Note", note, "_liked_by")
	liked_by = json.loads(liked_by_value) if liked_by_value else []

	if add == "Yes":
		if user not in liked_by:
			liked_by.append(user)
			# Same as frappe.desk.like.add_comment / Document.add_comment --
			# insert(ignore_permissions=True), so Comment's own DocPerm can't
			# block this either.
			frappe.get_doc(
				{
					"doctype": "Comment",
					"comment_type": "Like",
					"comment_email": user,
					"comment_by": frappe.utils.get_fullname(user),
					"reference_doctype": "FCRM Note",
					"reference_name": note,
					"content": _("Liked"),
				}
			).insert(ignore_permissions=True)
	else:
		if user in liked_by:
			liked_by.remove(user)
			# Same as frappe.desk.like.remove_like.
			like_comments = frappe.get_all(
				"Comment",
				filters={
					"comment_type": "Like",
					"reference_doctype": "FCRM Note",
					"reference_name": note,
					"owner": user,
				},
			)
			frappe.delete_doc(
				"Comment",
				[c.name for c in like_comments],
				ignore_permissions=True,
				force=True,
			)

	frappe.db.set_value("FCRM Note", note, "_liked_by", json.dumps(liked_by), update_modified=False)
	return liked_by
