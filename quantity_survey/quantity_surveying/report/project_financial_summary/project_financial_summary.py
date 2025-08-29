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
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 150,
		},
		{
			"label": _("BOQ Amount"),
			"fieldname": "boq_amount",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Total Valuation"),
			"fieldname": "total_valuation",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Payment Amount"),
			"fieldname": "payment_amount",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Variation Amount"),
			"fieldname": "variation_amount",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Completion %"),
			"fieldname": "completion_percentage",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("Profit/Loss"),
			"fieldname": "profit_loss",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Project Status"),
			"fieldname": "project_status",
			"fieldtype": "Data",
			"width": 100,
		},
	]


def get_data(filters):
	project = melon.qb.DocType("Project")
	boq = melon.qb.DocType("BoQ")
	valuation = melon.qb.DocType("Valuation")
	payment = melon.qb.DocType("Payment Certificate")
	variation = melon.qb.DocType("Variation Order")

	query = (
		melon.qb.from_(project)
		.left_join(boq)
		.on(boq.project == project.name)
		.left_join(valuation)
		.on(valuation.project == project.name)
		.left_join(payment)
		.on(payment.project == project.name)
		.left_join(variation)
		.on(variation.project == project.name)
		.select(
			project.name.as_("project"),
			project.status.as_("project_status"),
			melon.qb.functions.Sum(boq.total_amount).as_("boq_amount"),
			melon.qb.functions.Sum(valuation.total_valuation).as_("total_valuation"),
			melon.qb.functions.Sum(payment.total_amount).as_("payment_amount"),
			melon.qb.functions.Sum(variation.total_amount).as_("variation_amount"),
		)
		.where(project.status != "Cancelled")
		.groupby(project.name)
		.orderby(project.name, order=Order.asc)
	)

	query = get_conditions(filters, query, project)
	result = query.run(as_dict=True)

	# Calculate derived fields
	for row in result:
		row.boq_amount = flt(row.boq_amount)
		row.total_valuation = flt(row.total_valuation)
		row.payment_amount = flt(row.payment_amount)
		row.variation_amount = flt(row.variation_amount)
		
		if row.boq_amount > 0:
			row.completion_percentage = (row.total_valuation / row.boq_amount) * 100
		else:
			row.completion_percentage = 0
			
		row.profit_loss = row.total_valuation - row.payment_amount

	return result


def get_conditions(filters, query, project):
	if filters.get("company"):
		query = query.where(project.company == filters.get("company"))

	if filters.get("from_date") and filters.get("to_date"):
		query = query.where(
			project.creation[getdate(filters.get("from_date")) : getdate(filters.get("to_date"))]
		)
	elif filters.get("from_date"):
		query = query.where(project.creation >= filters.get("from_date"))
	elif filters.get("to_date"):
		query = query.where(project.creation <= filters.get("to_date"))

	if filters.get("project"):
		query = query.where(project.name == filters.get("project"))

	if filters.get("project_status"):
		query = query.where(project.status == filters.get("project_status"))

	return query


def get_chart_data(data):
	if not data:
		return None

	labels = [d.project for d in data[:10]]  # Top 10 projects
	boq_amounts = [d.boq_amount for d in data[:10]]
	valuation_amounts = [d.total_valuation for d in data[:10]]

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("BOQ Amount"), "values": boq_amounts},
				{"name": _("Valuation Amount"), "values": valuation_amounts}
			]
		},
		"type": "bar",
		"height": 300,
	}


def get_report_summary(data):
	if not data:
		return None

	total_projects = len(data)
	total_boq_value = sum([d.boq_amount for d in data])
	total_valuation = sum([d.total_valuation for d in data])
	total_profit_loss = sum([d.profit_loss for d in data])

	return [
		{
			"value": total_projects,
			"label": _("Total Projects"),
			"indicator": "Blue",
			"datatype": "Int",
		},
		{
			"value": total_boq_value,
			"label": _("Total BOQ Value"),
			"indicator": "Green" if total_boq_value > 0 else "Red",
			"datatype": "Currency",
		},
		{
			"value": total_valuation,
			"label": _("Total Valuation"),
			"indicator": "Green" if total_valuation > 0 else "Red",
			"datatype": "Currency",
		},
		{
			"value": total_profit_loss,
			"label": _("Total Profit/Loss"),
			"indicator": "Green" if total_profit_loss > 0 else "Red",
			"datatype": "Currency",
		},
	]
