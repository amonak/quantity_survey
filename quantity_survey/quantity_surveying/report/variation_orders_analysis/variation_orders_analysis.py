# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.utils import flt, getdate
from pypika import Order


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{
			"label": _("Variation Order"),
			"fieldname": "variation_order",
			"fieldtype": "Link",
			"options": "Variation Order",
			"width": 150,
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
			"fieldname": "date",
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"label": _("Type"),
			"fieldname": "variation_type",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Description"),
			"fieldname": "description",
			"fieldtype": "Text",
			"width": 200,
		},
		{
			"label": _("Total Amount"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100,
		},
	]


def get_data(filters):
	variation_order = melon.qb.DocType("Variation Order")

	query = (
		melon.qb.from_(variation_order)
		.select(
			variation_order.name.as_("variation_order"),
			variation_order.project,
			variation_order.date,
			variation_order.variation_type,
			variation_order.description,
			variation_order.total_amount,
			variation_order.status,
		)
		.where(variation_order.docstatus >= 0)
		.orderby(variation_order.date, order=Order.desc)
	)

	query = get_conditions(filters, query, variation_order)
	result = query.run(as_dict=True)

	# Process data
	for row in result:
		row.total_amount = flt(row.total_amount)

	return result


def get_conditions(filters, query, variation_order):
	if filters.get("company"):
		query = query.where(variation_order.company == filters.get("company"))

	if filters.get("project"):
		query = query.where(variation_order.project == filters.get("project"))

	if filters.get("from_date") and filters.get("to_date"):
		query = query.where(
			variation_order.date[getdate(filters.get("from_date")) : getdate(filters.get("to_date"))]
		)
	elif filters.get("from_date"):
		query = query.where(variation_order.date >= filters.get("from_date"))
	elif filters.get("to_date"):
		query = query.where(variation_order.date <= filters.get("to_date"))

	if filters.get("variation_type"):
		query = query.where(variation_order.variation_type == filters.get("variation_type"))

	if filters.get("status"):
		query = query.where(variation_order.status == filters.get("status"))

	return query


def get_chart_data(data):
	if not data:
		return None

	# Chart by variation type
	type_data = {}
	for d in data:
		variation_type = d.variation_type or "Unknown"
		if variation_type not in type_data:
			type_data[variation_type] = 0
		type_data[variation_type] += d.total_amount

	return {
		"data": {
			"labels": list(type_data.keys()),
			"datasets": [
				{
					"name": _("Amount"),
					"values": list(type_data.values())
				}
			]
		},
		"type": "pie",
		"height": 300,
	}


def get_report_summary(data):
	if not data:
		return None

	total_variations = len(data)
	total_amount = sum([d.total_amount for d in data])
	approved_amount = sum([d.total_amount for d in data if d.status == "Approved"])
	pending_amount = sum([d.total_amount for d in data if d.status in ["Draft", "Submitted"]])

	return [
		{
			"value": total_variations,
			"label": _("Total Variations"),
			"indicator": "Blue",
			"datatype": "Int",
		},
		{
			"value": total_amount,
			"label": _("Total Amount"),
			"indicator": "Green" if total_amount > 0 else "Red",
			"datatype": "Currency",
		},
		{
			"value": approved_amount,
			"label": _("Approved Amount"),
			"indicator": "Green",
			"datatype": "Currency",
		},
		{
			"value": pending_amount,
			"label": _("Pending Amount"),
			"indicator": "Orange",
			"datatype": "Currency",
		},
	]
