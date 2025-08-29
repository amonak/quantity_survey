# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.utils import flt

def execute(filters=None):
	"""Execute the Final Account Analysis report."""
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	summary = get_summary(data)
	
	return columns, data, None, chart, summary

def get_columns():
	"""Get report columns."""
	return [
		{
			"label": _("Final Account"),
			"fieldname": "final_account",
			"fieldtype": "Link",
			"options": "Final Account",
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
			"label": _("Original Contract"),
			"fieldname": "original_contract_value",
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"label": _("Variations"),
			"fieldname": "variation_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Final Contract"),
			"fieldname": "final_contract_value",
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"label": _("Total Certified"),
			"fieldname": "total_certified",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Retention Released"),
			"fieldname": "retention_released",
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"label": _("Final Amount"),
			"fieldname": "final_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Profit/Loss"),
			"fieldname": "profit_loss",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100
		}
	]

def get_data(filters):
	"""Get report data."""
	conditions = get_conditions(filters)
	
	data = melon.db.sql("""
		SELECT 
			fa.name as final_account,
			fa.project,
			COALESCE(boq.total_amount, 0) as original_contract_value,
			COALESCE(variations.total_variations, 0) as variation_amount,
			(COALESCE(boq.total_amount, 0) + COALESCE(variations.total_variations, 0)) as final_contract_value,
			COALESCE(payments.total_certified, 0) as total_certified,
			fa.retention_released,
			fa.final_amount,
			(fa.final_amount - COALESCE(actual_costs.total_cost, 0)) as profit_loss,
			fa.status
		FROM `tabFinal Account` fa
		LEFT JOIN (
			SELECT project, SUM(total_amount) as total_amount
			FROM `tabBoQ` 
			WHERE docstatus = 1
			GROUP BY project
		) boq ON boq.project = fa.project
		LEFT JOIN (
			SELECT 
				project, 
				SUM(CASE WHEN variation_type = 'Addition' THEN total_amount 
					WHEN variation_type = 'Omission' THEN -total_amount 
					ELSE 0 END) as total_variations
			FROM `tabVariation Order` 
			WHERE docstatus = 1
			GROUP BY project
		) variations ON variations.project = fa.project
		LEFT JOIN (
			SELECT project, SUM(total_amount) as total_certified
			FROM `tabPayment Certificate` 
			WHERE docstatus = 1
			GROUP BY project
		) payments ON payments.project = fa.project
		LEFT JOIN (
			SELECT project, SUM(total_cost) as total_cost
			FROM `tabCost Plan` 
			WHERE docstatus = 1
			GROUP BY project
		) actual_costs ON actual_costs.project = fa.project
		WHERE 1=1 {conditions}
		ORDER BY fa.project
	""".format(conditions=conditions), filters, as_dict=1)
	
	return data

def get_conditions(filters):
	"""Get query conditions based on filters."""
	conditions = ""
	
	if filters.get("company"):
		conditions += " AND fa.company = %(company)s"
	
	if filters.get("project"):
		conditions += " AND fa.project = %(project)s"
		
	if filters.get("from_date"):
		conditions += " AND DATE(fa.creation) >= %(from_date)s"
		
	if filters.get("to_date"):
		conditions += " AND DATE(fa.creation) <= %(to_date)s"
		
	if filters.get("status"):
		conditions += " AND fa.status = %(status)s"
	
	return conditions

def get_chart_data(data):
	"""Get chart data for the report."""
	# Profit/Loss analysis
	profit_projects = [d for d in data if d.profit_loss > 0]
	loss_projects = [d for d in data if d.profit_loss < 0]
	
	profit_count = len(profit_projects)
	loss_count = len(loss_projects)
	breakeven_count = len(data) - profit_count - loss_count
	
	return {
		"data": {
			"labels": ["Profit", "Loss", "Break-even"],
			"datasets": [{
				"name": "Project Count",
				"values": [profit_count, loss_count, breakeven_count]
			}]
		},
		"type": "pie",
		"height": 300,
		"colors": ["#2ecc71", "#e74c3c", "#f39c12"]
	}

def get_summary(data):
	"""Get report summary."""
	total_projects = len(data)
	total_original_value = sum([d.original_contract_value for d in data])
	total_variations = sum([d.variation_amount for d in data])
	total_final_value = sum([d.final_contract_value for d in data])
	total_profit_loss = sum([d.profit_loss for d in data])
	profitable_projects = len([d for d in data if d.profit_loss > 0])
	
	return [
		{
			"value": total_projects,
			"label": "Total Projects",
			"datatype": "Int"
		},
		{
			"value": total_original_value,
			"label": "Original Contract Value",
			"datatype": "Currency"
		},
		{
			"value": total_variations,
			"label": "Total Variations",
			"datatype": "Currency"
		},
		{
			"value": total_final_value,
			"label": "Final Contract Value",
			"datatype": "Currency"
		},
		{
			"value": total_profit_loss,
			"label": "Total Profit/Loss",
			"datatype": "Currency"
		},
		{
			"value": profitable_projects,
			"label": "Profitable Projects",
			"datatype": "Int"
		}
	]
