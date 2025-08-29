# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon.utils import formatdate, add_months, getdate

def get_data(chart_name=None, filters=None):
    """Get payment certificates trend data."""
    
    data = melon.db.sql("""
        SELECT 
            DATE_FORMAT(pc.certificate_date, '%Y-%m') as month_year,
            SUM(pc.total_amount) as total_amount,
            COUNT(*) as certificate_count
        FROM `tabPayment Certificate` pc
        WHERE pc.docstatus = 1
        GROUP BY DATE_FORMAT(pc.certificate_date, '%Y-%m')
        ORDER BY pc.certificate_date
    """, as_dict=True)
    
    labels = [d.month_year for d in data]
    values = [d.total_amount for d in data]
    
    return {
        "labels": labels,
        "datasets": [{
            "name": "Payment Amount",
            "values": values
        }]
    }
