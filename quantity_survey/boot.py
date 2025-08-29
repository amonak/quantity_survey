# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _

def boot_session(bootinfo):
    """Add quantity survey specific data to boot info"""
    
    # Add settings to bootinfo
    if melon.has_permission("Quantity Survey Settings", "read"):
        bootinfo.quantity_survey_settings = melon.get_single("Quantity Survey Settings").as_dict()
    
    # Add user permissions for quantity survey doctypes
    bootinfo.quantity_survey_permissions = get_user_permissions()
    
    # Add system defaults
    bootinfo.quantity_survey_defaults = {
        'default_company': melon.defaults.get_user_default("Company"),
        'default_currency': melon.defaults.get_global_default("currency"),
        'fiscal_year': melon.defaults.get_global_default("fiscal_year")
    }

def get_user_permissions():
    """Get user permissions for quantity survey doctypes"""
    permissions = {}
    
    qs_doctypes = [
        'BoQ', 'Valuation', 'Payment Certificate', 'Variation Order',
        'Cost Plan', 'Tender Package', 'Final Account'
    ]
    
    for doctype in qs_doctypes:
        permissions[doctype] = {
            'read': melon.has_permission(doctype, "read"),
            'write': melon.has_permission(doctype, "write"),
            'create': melon.has_permission(doctype, "create"),
            'submit': melon.has_permission(doctype, "submit"),
            'cancel': melon.has_permission(doctype, "cancel")
        }
    
    return permissions
