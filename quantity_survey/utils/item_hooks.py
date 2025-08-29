# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _

def validate_item_for_qs(doc, method):
    """Validate item for quantity survey usage"""
    # Ensure UOM is set for construction items
    if doc.get("is_construction_item") and not doc.get("stock_uom"):
        melon.throw(_("Stock UOM is required for construction items"))
    
    # Set default values for quantity survey items
    if doc.get("is_construction_item"):
        if not doc.get("valuation_method"):
            doc.valuation_method = "FIFO"
        
        if not doc.get("item_group"):
            doc.item_group = "Construction Materials"

def set_item_defaults(doc, method):
    """Set default values for construction items"""
    if doc.get("is_construction_item"):
        # Default item group
        if not doc.item_group:
            doc.item_group = "Construction Materials"
        
        # Default warehouse type
        if not doc.get("default_warehouse_type"):
            doc.default_warehouse_type = "Construction Site"
