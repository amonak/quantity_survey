# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.utils import flt, getdate

def execute(filters=None):
	"""Execute the Progress Tracking Report."""
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	summary = get_summary(data)
	
	return columns, data, None, chart, summary

def get_columns():
	"""Get report columns."""
	return [
		{
			"label": _("Valuation"),
			"fieldname": "valuation",
			"fieldtype": "Link",
			"options": "Valuation",
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
			"label": _("Valuation Date"),
			"fieldname": "valuation_date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Period Valuation"),
			"fieldname": "period_valuation",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Cumulative Valuation"),
			"fieldname": "cumulative_valuation",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("BOQ Amount"),
			"fieldname": "boq_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Completion %"),
			"fieldname": "completion_percentage",
			"fieldtype": "Percent",
			"width": 100
		},
		{
			"label": _("Period Progress %"),
			"fieldname": "progress_this_period",
			"fieldtype": "Percent",
			"width": 120
		}
	]

def get_data(filters):
	"""Get report data."""
	conditions = get_conditions(filters)
	
	# Get valuation data with cumulative calculations
	data = melon.db.sql("""
		SELECT 
			v.name as valuation,
			v.project,
			v.valuation_date,
			v.total_valuation as period_valuation,
			SUM(v2.total_valuation) as cumulative_valuation,
			COALESCE(boq.total_amount, 0) as boq_amount,
			CASE 
				WHEN COALESCE(boq.total_amount, 0) > 0 
				THEN (SUM(v2.total_valuation) / boq.total_amount * 100)
				ELSE 0 
			END as completion_percentage,
			CASE 
				WHEN COALESCE(boq.total_amount, 0) > 0 
				THEN (v.total_valuation / boq.total_amount * 100)
				ELSE 0 
			END as progress_this_period
		FROM `tabValuation` v
		LEFT JOIN `tabValuation` v2 ON v2.project = v.project 
			AND v2.valuation_date <= v.valuation_date 
			AND v2.docstatus = 1
		LEFT JOIN (
			SELECT project, SUM(total_amount) as total_amount
			FROM `tabBoQ` 
			WHERE docstatus = 1
			GROUP BY project
		) boq ON boq.project = v.project
		WHERE v.docstatus = 1 {conditions}
		GROUP BY v.name, v.project, v.valuation_date, v.total_valuation, boq.total_amount
		ORDER BY v.project, v.valuation_date
	""".format(conditions=conditions), filters, as_dict=1)
	
	return data

def get_conditions(filters):
	"""Get query conditions based on filters."""
	conditions = ""
	
	if filters.get("project"):
		conditions += " AND v.project = %(project)s"
		
	if filters.get("from_date"):
		conditions += " AND v.valuation_date >= %(from_date)s"
		
	if filters.get("to_date"):
		conditions += " AND v.valuation_date <= %(to_date)s"
	
	return conditions

def get_chart_data(data):
	"""Get chart data for the report."""
	# Group by project for progress tracking
	project_data = {}
	for row in data:
		project = row.project
		if project not in project_data:
			project_data[project] = {
				"dates": [],
				"cumulative": [],
				"completion": []
			}
		project_data[project]["dates"].append(str(row.valuation_date))
		project_data[project]["cumulative"].append(row.cumulative_valuation)
		project_data[project]["completion"].append(row.completion_percentage)
	
	# Return data for the first project (or most recent project)
	if project_data:
		first_project = list(project_data.keys())[0]
		return {
			"data": {
				"labels": project_data[first_project]["dates"],
				"datasets": [
					{
						"name": "Cumulative Valuation",
						"values": project_data[first_project]["cumulative"]
					},
					{
						"name": "Completion %",
						"values": project_data[first_project]["completion"]
					}
				]
			},
			"type": "line",
			"height": 300
		}
	
	return {}

def get_summary(data):
	"""Get report summary."""
	total_valuations = len(data)
	total_projects = len(set([d.project for d in data]))
	total_value = sum([d.period_valuation for d in data])
	avg_completion = sum([d.completion_percentage for d in data]) / total_valuations if total_valuations > 0 else 0
	max_completion = max([d.completion_percentage for d in data]) if data else 0
	
	return [
		{
			"value": total_valuations,
			"label": "Total Valuations",
			"datatype": "Int"
		},
		{
			"value": total_projects,
			"label": "Projects Tracked",
			"datatype": "Int"
		},
		{
			"value": total_value,
			"label": "Total Value",
			"datatype": "Currency"
		},
		{
			"value": avg_completion,
			"label": "Avg Completion %",
			"datatype": "Percent"
		},
		{
			"value": max_completion,
			"label": "Max Completion %",
			"datatype": "Percent"
		}
	]
