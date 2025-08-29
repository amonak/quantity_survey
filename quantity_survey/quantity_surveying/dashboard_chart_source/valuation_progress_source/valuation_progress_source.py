# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon.utils import formatdate

def get_data(chart_name=None, filters=None):
    """Get valuation progress data for timeline chart."""
    
    data = melon.db.sql("""
        SELECT 
            v.valuation_date,
            SUM(v.total_valuation) as total_valuation,
            COUNT(*) as valuation_count
        FROM `tabValuation` v
        WHERE v.docstatus = 1
        GROUP BY v.valuation_date
        ORDER BY v.valuation_date
    """, as_dict=True)
    
    labels = [formatdate(d.valuation_date) for d in data]
    values = [d.total_valuation for d in data]
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Cumulative Valuation",
            "values": values
        }]
    }
