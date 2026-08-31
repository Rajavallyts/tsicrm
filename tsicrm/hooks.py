app_name = "tsicrm"
app_title = "TSI-CRM"
app_publisher = "TSI"
app_description = "CRM for Tendersoftware"
app_email = "rajavally@tendersoftware.in"
app_license = "mit"


# Fixtures
# ------------------
# Every Custom Field on CRM Lead (currently just Skype), plus its CRM Fields Layout
# records -- the separate mechanism specific to the /crm portal app that controls the
# Quick Entry dialog and Side Panel there (unaffected by Customize Form; autonamed
# "CRM Lead-Quick Entry" / "CRM Lead-Side Panel"). Scoped by `dt` rather than by name,
# so a future field added to CRM Lead via Customize Form is picked up automatically on
# the next export -- no hooks.py edit needed, just re-export (or hand-edit the JSON)
# and review the diff before committing.
fixtures = [
	{"doctype": "Custom Field", "filters": [["dt", "=", "CRM Lead"]]},
	{"doctype": "CRM Fields Layout", "filters": [["dt", "=", "CRM Lead"]]},
	# Role Permission Manager changes on CRM Territory (restricting Create/Write/Delete
	# to Administrator/System Manager) land as Custom DocPerm rows, not on the
	# doctype's own (foreign, unowned) permissions table. Named randomly; scoped by
	# `parent`, not `dt`/`doc_type` like the two entries above.
	{"doctype": "Custom DocPerm", "filters": [["parent", "=", "CRM Territory"]]},
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "tsicrm",
# 		"logo": "/assets/tsicrm/logo.png",
# 		"title": "TSI-CRM",
# 		"route": "/tsicrm",
# 		"has_permission": "tsicrm.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/tsicrm/css/tsicrm.css"
# app_include_js = "/assets/tsicrm/js/tsicrm.js"

# include js, css files in header of web template
# web_include_css = "/assets/tsicrm/css/tsicrm.css"
# web_include_js = "/assets/tsicrm/js/tsicrm.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "tsicrm/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "tsicrm/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "tsicrm.utils.jinja_methods",
# 	"filters": "tsicrm.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "tsicrm.install.before_install"
# after_install = "tsicrm.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "tsicrm.uninstall.before_uninstall"
# after_uninstall = "tsicrm.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "tsicrm.utils.before_app_install"
# after_app_install = "tsicrm.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "tsicrm.utils.before_app_uninstall"
# after_app_uninstall = "tsicrm.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "tsicrm.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["tsicrm.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"tsicrm.tasks.all"
# 	],
# 	"daily": [
# 		"tsicrm.tasks.daily"
# 	],
# 	"hourly": [
# 		"tsicrm.tasks.hourly"
# 	],
# 	"weekly": [
# 		"tsicrm.tasks.weekly"
# 	],
# 	"monthly": [
# 		"tsicrm.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "tsicrm.install.before_tests"

# Overriding Methods
# ------------------------------
#
# crm.api.activities.get_activities is the whitelisted call the /crm portal's
# activity timeline uses (frontend/src/components/Activities/Activities.vue).
# This wraps it -- without editing apps/crm -- to attach `_liked_by` and a
# `comments_count` to each FCRM Note, for the Notes tab's Like/Comment
# feature. See tsicrm/crm_overrides/activities.py.
override_whitelisted_methods = {
	"crm.api.activities.get_activities": "tsicrm.crm_overrides.activities.get_activities",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "tsicrm.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["tsicrm.utils.before_request"]
# after_request = ["tsicrm.utils.after_request"]

# Job Events
# ----------
# before_job = ["tsicrm.utils.before_job"]
# after_job = ["tsicrm.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"tsicrm.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

