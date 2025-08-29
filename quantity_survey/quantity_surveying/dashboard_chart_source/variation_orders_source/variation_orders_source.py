# Copyright (c) 2025, Alphamonak Solutions


import melon

def get_data(chart_name=None, filters=None):
    """Get variation orders impact data."""
    
    data = melon.db.sql("""
        SELECT 
            vo.variation_type,
            SUM(CASE WHEN vo.variation_type = 'Addition' THEN vo.total_amount ELSE 0 END) as additions,
            SUM(CASE WHEN vo.variation_type = 'Omission' THEN vo.total_amount ELSE 0 END) as omissions,
            SUM(vo.total_amount) as total_amount,
            COUNT(*) as count
        FROM `tabVariation Order` vo
        WHERE vo.docstatus = 1
        GROUP BY vo.variation_type
        ORDER BY total_amount DESC
    """, as_dict=True)
    
    labels = [d.variation_type for d in data]
    values = [d.total_amount for d in data]
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Variation Amount",
            "values": values
        }]
    }
