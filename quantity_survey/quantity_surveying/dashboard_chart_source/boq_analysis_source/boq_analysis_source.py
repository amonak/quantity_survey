# Copyright (c) 2025, Alphamonak Solutions


import melon

def get_data(chart_name=None, filters=None):
    """Get BOQ vs Actual analysis data."""
    
    data = melon.db.sql("""
        SELECT 
            b.project,
            SUM(b.total_amount) as boq_amount,
            COALESCE(SUM(v.total_valuation), 0) as actual_amount,
            (COALESCE(SUM(v.total_valuation), 0) / SUM(b.total_amount) * 100) as completion_percentage
        FROM `tabBoQ` b
        LEFT JOIN `tabValuation` v ON v.project = b.project AND v.docstatus = 1
        WHERE b.docstatus = 1
        GROUP BY b.project
        ORDER BY completion_percentage DESC
    """, as_dict=True)
    
    labels = [d.project for d in data]
    boq_values = [d.boq_amount for d in data]
    actual_values = [d.actual_amount for d in data]
    
    return {
        "labels": labels,
        "datasets": [
            {
                "name": "BOQ Amount",
                "values": boq_values
            },
            {
                "name": "Actual Amount", 
                "values": actual_values
            }
        ]
    }
