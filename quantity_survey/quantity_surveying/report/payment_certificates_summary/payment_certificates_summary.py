# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.utils import flt, getdate

def execute(filters=None):
	"""Execute the Payment Certificates Summary report."""
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	summary = get_summary(data)
	
	return columns, data, None, chart, summary

def get_columns():
	"""Get report columns."""
	return [
		{
			"label": _("Payment Certificate"),
			"fieldname": "payment_certificate",
			"fieldtype": "Link",
			"options": "Payment Certificate",
			"width": 150
		},
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 120
		},
		{
			"label": _("Certificate Date"),
			"fieldname": "certificate_date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Period Amount"),
			"fieldname": "period_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Cumulative Amount"),
			"fieldname": "cumulative_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Retention"),
			"fieldname": "retention_amount",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Net Amount"),
			"fieldname": "net_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Payment Status"),
			"fieldname": "payment_status",
			"fieldtype": "Data",
			"width": 120
		}
	]

def get_data(filters):
	"""Get report data."""
	conditions = get_conditions(filters)
	
	# Get payment certificate data with cumulative calculations
	data = melon.db.sql("""
		SELECT 
			pc.name as payment_certificate,
			pc.project,
			pc.certificate_date,
			pc.total_amount as period_amount,
			SUM(pc2.total_amount) as cumulative_amount,
			(pc.total_amount * 0.05) as retention_amount,
			(pc.total_amount * 0.95) as net_amount,
			CASE 
				WHEN pc.status = 'Paid' THEN 'Fully Paid'
				WHEN pc.status = 'Partially Paid' THEN 'Partially Paid'
				ELSE 'Pending'
			END as payment_status
		FROM `tabPayment Certificate` pc
		LEFT JOIN `tabPayment Certificate` pc2 ON pc2.project = pc.project 
			AND pc2.certificate_date <= pc.certificate_date 
			AND pc2.docstatus = 1
		WHERE pc.docstatus = 1 {conditions}
		GROUP BY pc.name, pc.project, pc.certificate_date, pc.total_amount, pc.status
		ORDER BY pc.project, pc.certificate_date
	""".format(conditions=conditions), filters, as_dict=1)
	
	return data

def get_conditions(filters):
	"""Get query conditions based on filters."""
	conditions = ""
	
	if filters.get("project"):
		conditions += " AND pc.project = %(project)s"
		
	if filters.get("from_date"):
		conditions += " AND pc.certificate_date >= %(from_date)s"
		
	if filters.get("to_date"):
		conditions += " AND pc.certificate_date <= %(to_date)s"
		
	if filters.get("payment_status"):
		if filters.get("payment_status") == "Fully Paid":
			conditions += " AND pc.status = 'Paid'"
		elif filters.get("payment_status") == "Partially Paid":
			conditions += " AND pc.status = 'Partially Paid'"
		elif filters.get("payment_status") == "Pending":
			conditions += " AND pc.status != 'Paid' AND pc.status != 'Partially Paid'"
	
	return conditions

def get_chart_data(data):
	"""Get chart data for the report."""
	# Monthly payment trends
	monthly_data = {}
	for row in data:
		month_key = row.certificate_date.strftime("%Y-%m")
		if month_key not in monthly_data:
			monthly_data[month_key] = 0
		monthly_data[month_key] += row.period_amount
	
	# Sort by month
	sorted_months = sorted(monthly_data.keys())
	
	return {
		"data": {
			"labels": sorted_months,
			"datasets": [{
				"name": "Monthly Payments",
				"values": [monthly_data[month] for month in sorted_months]
			}]
		},
		"type": "bar",
		"height": 300
	}

def get_summary(data):
	"""Get report summary."""
	total_certificates = len(data)
	total_amount = sum([d.period_amount for d in data])
	total_retention = sum([d.retention_amount for d in data])
	total_net = sum([d.net_amount for d in data])
	pending_count = len([d for d in data if d.payment_status == "Pending"])
	paid_count = len([d for d in data if d.payment_status == "Fully Paid"])
	
	return [
		{
			"value": total_certificates,
			"label": "Total Certificates",
			"datatype": "Int"
		},
		{
			"value": total_amount,
			"label": "Total Amount",
			"datatype": "Currency"
		},
		{
			"value": total_retention,
			"label": "Total Retention",
			"datatype": "Currency"
		},
		{
			"value": total_net,
			"label": "Total Net Amount",
			"datatype": "Currency"
		},
		{
			"value": pending_count,
			"label": "Pending Payments",
			"datatype": "Int"
		},
		{
			"value": paid_count,
			"label": "Paid Certificates",
			"datatype": "Int"
		}
	]
