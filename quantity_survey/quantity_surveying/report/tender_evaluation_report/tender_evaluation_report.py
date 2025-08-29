# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.utils import flt, getdate

def execute(filters=None):
	"""Execute the Tender Evaluation Report."""
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	summary = get_summary(data)
	
	return columns, data, None, chart, summary

def get_columns():
	"""Get report columns."""
	return [
		{
			"label": _("Tender Package"),
			"fieldname": "tender_package",
			"fieldtype": "Link",
			"options": "Tender Package",
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
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 150
		},
		{
			"label": _("Quote Amount"),
			"fieldname": "quote_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Lowest Quote"),
			"fieldname": "lowest_quote",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Variance %"),
			"fieldname": "variance_percentage",
			"fieldtype": "Percent",
			"width": 100
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Quote Date"),
			"fieldname": "quote_date",
			"fieldtype": "Date",
			"width": 100
		}
	]

def get_data(filters):
	"""Get report data."""
	conditions = get_conditions(filters)
	
	# First get all quotes with lowest quote for each tender package
	data = melon.db.sql("""
		SELECT 
			tq.tender_package,
			tp.project,
			tq.supplier,
			tq.total_amount as quote_amount,
			min_quotes.lowest_quote,
			CASE 
				WHEN min_quotes.lowest_quote > 0 
				THEN ((tq.total_amount - min_quotes.lowest_quote) / min_quotes.lowest_quote * 100)
				ELSE 0 
			END as variance_percentage,
			tq.status,
			DATE(tq.creation) as quote_date
		FROM `tabTender Quote` tq
		INNER JOIN `tabTender Package` tp ON tp.name = tq.tender_package
		INNER JOIN (
			SELECT 
				tender_package,
				MIN(total_amount) as lowest_quote
			FROM `tabTender Quote`
			WHERE docstatus = 1
			GROUP BY tender_package
		) min_quotes ON min_quotes.tender_package = tq.tender_package
		WHERE tq.docstatus = 1 {conditions}
		ORDER BY tq.tender_package, tq.total_amount
	""".format(conditions=conditions), filters, as_dict=1)
	
	return data

def get_conditions(filters):
	"""Get query conditions based on filters."""
	conditions = ""
	
	if filters.get("tender_package"):
		conditions += " AND tq.tender_package = %(tender_package)s"
	
	if filters.get("project"):
		conditions += " AND tp.project = %(project)s"
		
	if filters.get("supplier"):
		conditions += " AND tq.supplier = %(supplier)s"
		
	if filters.get("from_date"):
		conditions += " AND DATE(tq.creation) >= %(from_date)s"
		
	if filters.get("to_date"):
		conditions += " AND DATE(tq.creation) <= %(to_date)s"
	
	return conditions

def get_chart_data(data):
	"""Get chart data for the report."""
	# Group by supplier for comparison
	supplier_data = {}
	for row in data:
		supplier = row.supplier
		if supplier not in supplier_data:
			supplier_data[supplier] = []
		supplier_data[supplier].append(row.quote_amount)
	
	# Calculate average quote per supplier
	supplier_averages = {}
	for supplier, amounts in supplier_data.items():
		supplier_averages[supplier] = sum(amounts) / len(amounts)
	
	return {
		"data": {
			"labels": list(supplier_averages.keys()),
			"datasets": [{
				"name": "Average Quote Amount",
				"values": list(supplier_averages.values())
			}]
		},
		"type": "bar",
		"height": 300
	}

def get_summary(data):
	"""Get report summary."""
	total_quotes = len(data)
	total_packages = len(set([d.tender_package for d in data]))
	avg_quote = sum([d.quote_amount for d in data]) / total_quotes if total_quotes > 0 else 0
	lowest_variance = min([d.variance_percentage for d in data]) if data else 0
	highest_variance = max([d.variance_percentage for d in data]) if data else 0
	
	return [
		{
			"value": total_quotes,
			"label": "Total Quotes",
			"datatype": "Int"
		},
		{
			"value": total_packages,
			"label": "Tender Packages",
			"datatype": "Int"
		},
		{
			"value": avg_quote,
			"label": "Average Quote",
			"datatype": "Currency"
		},
		{
			"value": lowest_variance,
			"label": "Lowest Variance %",
			"datatype": "Percent"
		},
		{
			"value": highest_variance,
			"label": "Highest Variance %",
			"datatype": "Percent"
		}
	]
