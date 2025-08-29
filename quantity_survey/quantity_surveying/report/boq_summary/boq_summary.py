# Copyright (c) 2025, Alphamonak Solutions

import melon
from melon import _
from melon.utils import getdate, flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{
			"label": _("BoQ"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "BoQ",
			"width": 120,
		},
		{
			"label": _("Title"),
			"fieldname": "title",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 120,
		},
		{
			"label": _("Date"),
			"fieldname": "boq_date",
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Total Quantity"),
			"fieldname": "total_quantity",
			"fieldtype": "Float",
			"precision": "3",
			"width": 120,
		},
		{
			"label": _("Total Amount"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": _("Valuations"),
			"fieldname": "valuations_count",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"label": _("Variations"),
			"fieldname": "variations_count",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 120,
		}
	]


def get_data(filters):
	"""Get BoQ summary data with optimized query"""
	conditions = get_conditions(filters)
	
	# Use single optimized query instead of multiple queries
	data = melon.db.sql(f"""
		SELECT 
			boq.name,
			boq.title,
			boq.project,
			boq.boq_date,
			boq.status,
			boq.total_quantity,
			boq.total_amount,
			boq.company,
			COALESCE(val_summary.valuations_count, 0) as valuations_count,
			COALESCE(var_summary.variations_count, 0) as variations_count
		FROM `tabBoQ` boq
		LEFT JOIN (
			SELECT boq, COUNT(*) as valuations_count
			FROM `tabValuation` 
			WHERE docstatus = 1
			GROUP BY boq
		) val_summary ON val_summary.boq = boq.name
		LEFT JOIN (
			SELECT boq, COUNT(*) as variations_count
			FROM `tabVariation Order`
			WHERE docstatus = 1
			GROUP BY boq
		) var_summary ON var_summary.boq = boq.name
		WHERE boq.docstatus != 2 {conditions}
		ORDER BY boq.boq_date DESC, boq.creation DESC
	""", filters, as_dict=True)
	
	return data


def get_conditions(filters):
	conditions = ""
	
	if filters.get("from_date"):
		conditions += " AND boq.boq_date >= %(from_date)s"
	
	if filters.get("to_date"):
		conditions += " AND boq.boq_date <= %(to_date)s"
	
	if filters.get("company"):
		conditions += " AND boq.company = %(company)s"
	
	if filters.get("project"):
		conditions += " AND boq.project = %(project)s"
	
	if filters.get("status"):
		conditions += " AND boq.status = %(status)s"
	
	return conditions


def get_chart_data(data):
	if not data:
		return None
	
	status_data = {}
	for row in data:
		status = row.get("status", "Unknown")
		if status not in status_data:
			status_data[status] = {"count": 0, "amount": 0}
		status_data[status]["count"] += 1
		status_data[status]["amount"] += flt(row.get("total_amount", 0))
	
	labels = list(status_data.keys())
	values = [status_data[label]["count"] for label in labels]
	
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": _("BoQ Count"),
					"values": values
				}
			]
		},
		"type": "donut",
		"colors": ["#36B37E", "#FFAB00", "#FF5630", "#6554C0"]
	}


def get_report_summary(data):
	if not data:
		return None
	
	total_boqs = len(data)
	total_amount = sum(flt(row.get("total_amount", 0)) for row in data)
	draft_count = len([row for row in data if row.get("status") == "Draft"])
	approved_count = len([row for row in data if row.get("status") == "Approved"])
	
	return [
		{
			"value": total_boqs,
			"label": _("Total BoQs"),
			"indicator": "Blue",
			"datatype": "Int",
		},
		{
			"value": total_amount,
			"label": _("Total Contract Value"),
			"indicator": "Green",
			"datatype": "Currency",
		},
		{
			"value": draft_count,
			"label": _("Draft BoQs"),
			"indicator": "Orange",
			"datatype": "Int",
		},
		{
			"value": approved_count,
			"label": _("Approved BoQs"),
			"indicator": "Green",
			"datatype": "Int",
		},
	]
