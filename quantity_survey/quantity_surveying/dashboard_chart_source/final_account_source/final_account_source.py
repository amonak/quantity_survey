# Copyright (c) 2025, Alphamonak Solutions


import melon

def get_data(chart_name=None, filters=None):
    """Get final account status distribution data."""
    
    data = melon.db.sql("""
        SELECT 
            fa.status,
            COUNT(*) as count
        FROM `tabFinal Account` fa
        GROUP BY fa.status
        ORDER BY count DESC
    """, as_dict=True)
    
    labels = [d.status for d in data]
    values = [d.count for d in data]
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Final Account Status",
            "values": values
        }]
    }
