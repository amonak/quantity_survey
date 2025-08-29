# Copyright (c) 2025, Alphamonak Solutions


from . import __version__ as app_version

app_name = "quantity_survey"
app_title = "Quantity Survey"
app_publisher = "Monak"
app_description = "Comprehensive Quantity Surveying Module for Monak v8"
app_icon = "fa fa-file-text"
app_color = "blue"
app_email = "amonak@monakerp.com"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
    "/assets/quantity_survey/css/quantity_survey.css",
    "/assets/quantity_survey/css/mobile.css"
]
app_include_js = [
    "/assets/quantity_survey/js/quantity_survey.js"
]

# include js, css files in header of web template
web_include_css = "/assets/quantity_survey/css/quantity_survey.css"
web_include_js = "/assets/quantity_survey/js/quantity_survey.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "quantity_survey/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "BoQ": "public/js/boq.js",
    "Valuation": "public/js/valuation.js",
    "Variation Order": "public/js/variation_order.js",
    "Payment Certificate": "public/js/payment_certificate.js",
    "Cost Plan": "public/js/cost_plan.js",
    "Tender": "public/js/tender.js",
    "Final Account": "public/js/final_account.js"
}
doctype_list_js = {
    "BoQ": "public/js/boq_list.js",
    "Valuation": "public/js/valuation_list.js",
    "Payment Certificate": "public/js/payment_certificate_list.js"
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

before_install = "quantity_survey.install.before_install"
after_install = "quantity_survey.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "quantity_survey.uninstall.before_uninstall"
# after_uninstall = "quantity_survey.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See melon.core.notifications.get_notification_config

notification_config = "quantity_survey.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "melon.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "melon.desk.doctype.event.event.has_permission",
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

doc_events = {
    "Project": {
        "validate": "quantity_survey.utils.project_hooks.validate_project",
        "on_update": "quantity_survey.utils.project_hooks.update_project_status"
    },
    "Item": {
        "validate": "quantity_survey.utils.item_hooks.validate_item_for_qs"
    },
    "BoQ": {
        "validate": "quantity_survey.quantity_surveying.doctype.boq.boq.validate_boq",
        "on_submit": "quantity_survey.quantity_surveying.doctype.boq.boq.on_submit",
        "on_cancel": "quantity_survey.quantity_surveying.doctype.boq.boq.on_cancel"
    },
    "Valuation": {
        "validate": "quantity_survey.quantity_surveying.doctype.valuation.valuation.validate_valuation",
        "on_submit": "quantity_survey.quantity_surveying.doctype.valuation.valuation.on_submit",
        "on_cancel": "quantity_survey.quantity_surveying.doctype.valuation.valuation.on_cancel"
    },
    "Payment Certificate": {
        "validate": "quantity_survey.quantity_surveying.doctype.payment_certificate.payment_certificate.validate_payment",
        "on_submit": "quantity_survey.quantity_surveying.doctype.payment_certificate.payment_certificate.on_submit",
        "on_cancel": "quantity_survey.quantity_surveying.doctype.payment_certificate.payment_certificate.on_cancel"
    },
    "Variation Order": {
        "validate": "quantity_survey.quantity_surveying.doctype.variation_order.variation_order.validate_variation_order",
        "on_submit": "quantity_survey.quantity_surveying.doctype.variation_order.variation_order.on_submit",
        "on_cancel": "quantity_survey.quantity_surveying.doctype.variation_order.variation_order.on_cancel"
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "daily": [
        "quantity_survey.tasks.daily_tasks.send_payment_reminders",
        "quantity_survey.tasks.daily_tasks.update_project_progress"
    ],
    "weekly": [
        "quantity_survey.tasks.weekly_tasks.generate_progress_reports",
        "quantity_survey.tasks.weekly_tasks.cleanup_temp_files"
    ],
    "monthly": [
        "quantity_survey.tasks.monthly_tasks.archive_completed_projects",
        "quantity_survey.tasks.monthly_tasks.generate_monthly_summary"
    ]
}

# Testing
# -------

# before_tests = "quantity_survey.install.before_tests"

# Overriding Methods
# ------------------------------

override_whitelisted_methods = {
    "monak.projects.doctype.project.project.get_project_status": "quantity_survey.utils.project_overrides.get_project_status_with_qs"
}

# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Melon apps
override_doctype_dashboards = {
    "Project": "quantity_survey.utils.project_dashboard.get_dashboard_data"
}

# exempt linked doctypes from being automatically cancelled
auto_cancel_exempted_doctypes = ["Measurement Entry", "Progress Photo"]

# User Data Protection
# --------------------

# Remove the placeholder user_data_fields and add proper ones if needed
# user_data_fields = []

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"quantity_survey.auth.validate"
# ]

# Website Routes
# --------------

website_route_rules = [
    {"from_route": "/quantity-survey/<path:app_path>", "to_route": "quantity-survey"},
]

# Mobile App
# ----------

# Enable mobile app integration
mobile_app_enabled = True

# Service Worker for offline functionality
web_page_context = {
    "quantity-survey": {
        "base_template": "templates/web.html",
        "route": "/quantity-survey",
        "title": "Quantity Survey Mobile App"
    }
}

# Additional Settings for Monak v8
# ----------------------------------

# Standard field customizations and fixtures
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": {"module": "Quantity Survey"}
    },
    {
        "doctype": "Property Setter", 
        "filters": {"module": "Quantity Survey"}
    },
    {
        "doctype": "Role",
        "filters": {"name": ["in", ["Quantity Survey Manager", "Quantity Survey Officer", "Construction Manager"]]}
    },
    {
        "doctype": "Quantity Survey Settings"
    }
]

# Boot session info for mobile app
boot_session = "quantity_survey.boot.boot_session"

# Website context
website_context = {
    "favicon": "/assets/quantity_survey/images/favicon.ico",
    "splash_image": "/assets/quantity_survey/images/splash.png",
    "brand_html": "Quantity Survey"
}
