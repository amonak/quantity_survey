# Copyright (c) 2025, Alphamonak Solutions


import melon

def get_data(chart_name=None, filters=None):
    """Get project cost overview data for dashboard chart."""
    
    data = melon.db.sql("""
        SELECT 
            CASE 
                WHEN cp.cost_category = 'Material' THEN 'Materials'
                WHEN cp.cost_category = 'Labor' THEN 'Labour'
                WHEN cp.cost_category = 'Equipment' THEN 'Equipment'
                WHEN cp.cost_category = 'Subcontract' THEN 'Subcontracts'
                ELSE 'Other'
            END as cost_category,
            SUM(cp.total_cost) as total_cost
        FROM `tabCost Plan` cp
        WHERE cp.docstatus = 1
        GROUP BY cp.cost_category
        ORDER BY total_cost DESC
    """, as_dict=True)
    
    labels = [d.cost_category for d in data]
    values = [d.total_cost for d in data]
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Cost Distribution",
            "values": values
        }]
    }
