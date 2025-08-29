# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _

def get_notification_config():
    """Get notification configuration for Quantity Survey app"""
    
    return {
        "for_doctype": {
            "Bill of Quantities": {
                "status": "Open",
                "docstatus": 0
            },
            "Valuation": {
                "status": "Draft",
                "docstatus": 0
            },
            "Payment Certificate": {
                "status": "Pending Approval",
                "docstatus": 0
            },
            "Variation Order": {
                "status": "Pending Approval", 
                "docstatus": 0
            },
            "Cost Plan": {
                "status": "Draft",
                "docstatus": 0
            },
            "Tender": {
                "status": "Open",
                "docstatus": 0
            },
            "Final Account": {
                "status": "Draft",
                "docstatus": 0
            }
        },
        "for_other_doctypes": {
            "Project": ["Quantity Survey Manager", "Construction Manager"]
        },
        "targets": {
            "Bill of Quantities": {
                "color": "#1976d2",
                "conditions": [
                    {
                        "target_field": "total_amount",
                        "color": "#28a745"
                    }
                ]
            },
            "Valuation": {
                "color": "#17a2b8",
                "conditions": [
                    {
                        "target_field": "total_work_done",
                        "color": "#28a745"
                    }
                ]
            },
            "Payment Certificate": {
                "color": "#ffc107",
                "conditions": [
                    {
                        "target_field": "certified_amount",
                        "color": "#28a745"
                    }
                ]
            }
        }
    }
