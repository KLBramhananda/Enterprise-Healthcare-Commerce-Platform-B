app_name = "keemeds_commerce"
app_title = "KeeMeds Commerce"
app_publisher = "Bramhananda K L"
app_description = "Enterprise Healthcare Commerce Platform inspired by Tata 1mg for KeeMeds Medical Stores."
app_email = "bramhanandaklhg@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "keemeds_commerce",
# 		"logo": "/assets/keemeds_commerce/logo.png",
# 		"title": "KeeMeds Commerce",
# 		"route": "/keemeds_commerce",
# 		"has_permission": "keemeds_commerce.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/keemeds_commerce/css/keemeds_commerce.css"
# app_include_js = "/assets/keemeds_commerce/js/keemeds_commerce.js"

# include js, css files in header of web template
# web_include_css = "/assets/keemeds_commerce/css/keemeds_commerce.css"
# web_include_js = "/assets/keemeds_commerce/js/keemeds_commerce.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "keemeds_commerce/public/scss/website"

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
# app_include_icons = "keemeds_commerce/public/icons.svg"

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

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "keemeds_commerce.utils.jinja_methods",
# 	"filters": "keemeds_commerce.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "keemeds_commerce.install.before_install"
# after_install = "keemeds_commerce.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "keemeds_commerce.uninstall.before_uninstall"
# after_uninstall = "keemeds_commerce.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "keemeds_commerce.utils.before_app_install"
# after_app_install = "keemeds_commerce.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "keemeds_commerce.utils.before_app_uninstall"
# after_app_uninstall = "keemeds_commerce.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "keemeds_commerce.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "keemeds_commerce.notifications.get_notification_config"

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
# 		"keemeds_commerce.tasks.all"
# 	],
# 	"daily": [
# 		"keemeds_commerce.tasks.daily"
# 	],
# 	"hourly": [
# 		"keemeds_commerce.tasks.hourly"
# 	],
# 	"weekly": [
# 		"keemeds_commerce.tasks.weekly"
# 	],
# 	"monthly": [
# 		"keemeds_commerce.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "keemeds_commerce.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "keemeds_commerce.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "keemeds_commerce.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "keemeds_commerce.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["keemeds_commerce.utils.before_request"]
# after_request = ["keemeds_commerce.utils.after_request"]

# Job Events
# ----------
# before_job = ["keemeds_commerce.utils.before_job"]
# after_job = ["keemeds_commerce.utils.after_job"]

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
# 	"keemeds_commerce.auth.validate"
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

