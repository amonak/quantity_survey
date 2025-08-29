# Copyright (c) 2025, Alphamonak Solutions


import melon

def get_data(chart_name=None, filters=None):
    """Get tender status distribution data."""
    
    data = melon.db.sql("""
        SELECT 
            tp.status,
            COUNT(*) as count
        FROM `tabTender Package` tp
        GROUP BY tp.status
        ORDER BY count DESC
    """, as_dict=True)
    
    labels = [d.status for d in data]
    values = [d.count for d in data]
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Tender Status",
            "values": values
        }]
    }
