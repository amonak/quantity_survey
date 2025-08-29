# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.utils import flt

def execute(filters=None):
	"""Execute the Cost Control Analysis report."""
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	summary = get_summary(data)
	
	return columns, data, None, chart, summary

def get_columns():
	"""Get report columns."""
	return [
		{
			"label": _("Cost Plan"),
			"fieldname": "cost_plan",
			"fieldtype": "Link",
			"options": "Cost Plan",
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
			"label": _("Category"),
			"fieldname": "cost_category",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Planned Cost"),
			"fieldname": "planned_cost",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Actual Cost"),
			"fieldname": "actual_cost",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Variance"),
			"fieldname": "variance",
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
		}
	]

def get_data(filters):
	"""Get report data."""
	conditions = get_conditions(filters)
	
	# Get cost plan data with actual costs from payment certificates
	data = melon.db.sql("""
		SELECT 
			cp.name as cost_plan,
			cp.project,
			cp.cost_category,
			cp.total_cost as planned_cost,
			COALESCE(actual_costs.actual_cost, 0) as actual_cost,
			(COALESCE(actual_costs.actual_cost, 0) - cp.total_cost) as variance,
			CASE 
				WHEN cp.total_cost > 0 
				THEN ((COALESCE(actual_costs.actual_cost, 0) - cp.total_cost) / cp.total_cost * 100)
				ELSE 0 
			END as variance_percentage,
			CASE 
				WHEN COALESCE(actual_costs.actual_cost, 0) > cp.total_cost * 1.1 THEN 'Over Budget'
				WHEN COALESCE(actual_costs.actual_cost, 0) < cp.total_cost * 0.9 THEN 'Under Budget'
				ELSE 'On Track'
			END as status
		FROM `tabCost Plan` cp
		LEFT JOIN (
			SELECT 
				pc.project,
				'Material' as cost_category,
				SUM(pc.total_amount) as actual_cost
			FROM `tabPayment Certificate` pc
			WHERE pc.docstatus = 1
			GROUP BY pc.project
			UNION ALL
			SELECT 
				vo.project,
				'Labor' as cost_category,
				SUM(vo.total_amount) as actual_cost
			FROM `tabVariation Order` vo
			WHERE vo.docstatus = 1 AND vo.variation_type = 'Addition'
			GROUP BY vo.project
		) actual_costs ON actual_costs.project = cp.project 
			AND actual_costs.cost_category = cp.cost_category
		WHERE cp.docstatus = 1 {conditions}
		ORDER BY cp.project, cp.cost_category
	""".format(conditions=conditions), filters, as_dict=1)
	
	return data

def get_conditions(filters):
	"""Get query conditions based on filters."""
	conditions = ""
	
	if filters.get("project"):
		conditions += " AND cp.project = %(project)s"
	
	if filters.get("cost_category"):
		conditions += " AND cp.cost_category = %(cost_category)s"
		
	if filters.get("from_date"):
		conditions += " AND DATE(cp.creation) >= %(from_date)s"
		
	if filters.get("to_date"):
		conditions += " AND DATE(cp.creation) <= %(to_date)s"
	
	return conditions

def get_chart_data(data):
	"""Get chart data for the report."""
	# Group by status
	status_data = {"Over Budget": 0, "Under Budget": 0, "On Track": 0}
	for row in data:
		if row.status in status_data:
			status_data[row.status] += 1
	
	return {
		"data": {
			"labels": list(status_data.keys()),
			"datasets": [{
				"name": "Budget Status",
				"values": list(status_data.values())
			}]
		},
		"type": "donut",
		"height": 300
	}

def get_summary(data):
	"""Get report summary."""
	total_plans = len(data)
	total_planned = sum([d.planned_cost for d in data])
	total_actual = sum([d.actual_cost for d in data])
	total_variance = total_actual - total_planned
	over_budget_count = len([d for d in data if d.status == "Over Budget"])
	
	return [
		{
			"value": total_plans,
			"label": "Total Cost Plans",
			"datatype": "Int"
		},
		{
			"value": total_planned,
			"label": "Total Planned Cost",
			"datatype": "Currency"
		},
		{
			"value": total_actual,
			"label": "Total Actual Cost",
			"datatype": "Currency"
		},
		{
			"value": total_variance,
			"label": "Total Variance",
			"datatype": "Currency"
		},
		{
			"value": over_budget_count,
			"label": "Over Budget Plans",
			"datatype": "Int"
		}
	]
