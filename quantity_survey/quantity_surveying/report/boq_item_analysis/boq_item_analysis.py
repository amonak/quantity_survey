# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.utils import flt

def execute(filters=None):
	"""Execute the BOQ Item Analysis report."""
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	summary = get_summary(data)
	
	return columns, data, None, chart, summary

def get_columns():
	"""Get report columns."""
	return [
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 150
		},
		{
			"label": _("Item"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("UOM"),
			"fieldname": "uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 80
		},
		{
			"label": _("BOQ Qty"),
			"fieldname": "boq_quantity",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Valued Qty"),
			"fieldname": "valued_quantity",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Remaining Qty"),
			"fieldname": "remaining_quantity",
			"fieldtype": "Float",
			"width": 110
		},
		{
			"label": _("Completion %"),
			"fieldname": "completion_percentage",
			"fieldtype": "Percent",
			"width": 100
		},
		{
			"label": _("BOQ Rate"),
			"fieldname": "boq_rate",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("BOQ Amount"),
			"fieldname": "boq_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Valued Amount"),
			"fieldname": "valued_amount",
			"fieldtype": "Currency",
			"width": 120
		}
	]

def get_data(filters):
	"""Get report data."""
	conditions = get_conditions(filters)
	
	data = melon.db.sql("""
		SELECT 
			bi.parent as project,
			bi.item_code,
			i.item_name,
			bi.uom,
			bi.quantity as boq_quantity,
			COALESCE(valued.valued_quantity, 0) as valued_quantity,
			(bi.quantity - COALESCE(valued.valued_quantity, 0)) as remaining_quantity,
			CASE 
				WHEN bi.quantity > 0 
				THEN (COALESCE(valued.valued_quantity, 0) / bi.quantity * 100)
				ELSE 0 
			END as completion_percentage,
			bi.rate as boq_rate,
			bi.amount as boq_amount,
			COALESCE(valued.valued_amount, 0) as valued_amount
		FROM `tabBoQ Item` bi
		INNER JOIN `tabBoQ` b ON b.name = bi.parent
		INNER JOIN `tabItem` i ON i.item_code = bi.item_code
		LEFT JOIN (
			SELECT 
				vi.item_code,
				v.project,
				SUM(vi.quantity) as valued_quantity,
				SUM(vi.amount) as valued_amount
			FROM `tabValuation Item` vi
			INNER JOIN `tabValuation` v ON v.name = vi.parent
			WHERE v.docstatus = 1
			GROUP BY vi.item_code, v.project
		) valued ON valued.item_code = bi.item_code AND valued.project = b.project
		WHERE b.docstatus = 1 {conditions}
		ORDER BY bi.parent, bi.item_code
	""".format(conditions=conditions), filters, as_dict=1)
	
	return data

def get_conditions(filters):
	"""Get query conditions based on filters."""
	conditions = ""
	
	if filters.get("project"):
		conditions += " AND b.project = %(project)s"
		
	if filters.get("item_group"):
		conditions += " AND i.item_group = %(item_group)s"
		
	if filters.get("completion_status"):
		if filters.get("completion_status") == "Not Started":
			conditions += " AND COALESCE(valued.valued_quantity, 0) = 0"
		elif filters.get("completion_status") == "In Progress":
			conditions += " AND COALESCE(valued.valued_quantity, 0) > 0 AND COALESCE(valued.valued_quantity, 0) < bi.quantity"
		elif filters.get("completion_status") == "Completed":
			conditions += " AND COALESCE(valued.valued_quantity, 0) = bi.quantity"
		elif filters.get("completion_status") == "Over Completed":
			conditions += " AND COALESCE(valued.valued_quantity, 0) > bi.quantity"
	
	return conditions

def get_chart_data(data):
	"""Get chart data for the report."""
	# Completion status distribution
	not_started = len([d for d in data if d.completion_percentage == 0])
	in_progress = len([d for d in data if 0 < d.completion_percentage < 100])
	completed = len([d for d in data if d.completion_percentage == 100])
	over_completed = len([d for d in data if d.completion_percentage > 100])
	
	return {
		"data": {
			"labels": ["Not Started", "In Progress", "Completed", "Over Completed"],
			"datasets": [{
				"name": "Item Status",
				"values": [not_started, in_progress, completed, over_completed]
			}]
		},
		"type": "donut",
		"height": 300,
		"colors": ["#e74c3c", "#f39c12", "#2ecc71", "#9b59b6"]
	}

def get_summary(data):
	"""Get report summary."""
	total_items = len(data)
	total_boq_amount = sum([d.boq_amount for d in data])
	total_valued_amount = sum([d.valued_amount for d in data])
	completed_items = len([d for d in data if d.completion_percentage >= 100])
	avg_completion = sum([d.completion_percentage for d in data]) / total_items if total_items > 0 else 0
	
	return [
		{
			"value": total_items,
			"label": "Total Items",
			"datatype": "Int"
		},
		{
			"value": total_boq_amount,
			"label": "Total BOQ Amount",
			"datatype": "Currency"
		},
		{
			"value": total_valued_amount,
			"label": "Total Valued Amount",
			"datatype": "Currency"
		},
		{
			"value": completed_items,
			"label": "Completed Items",
			"datatype": "Int"
		},
		{
			"value": avg_completion,
			"label": "Average Completion %",
			"datatype": "Percent"
		}
	]
