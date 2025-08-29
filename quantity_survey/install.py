# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.custom.doctype.custom_field.custom_field import create_custom_fields


def before_install():
	"""Execute before app installation."""
	pass


def after_install():
	"""Execute after app installation."""
	create_custom_fields(get_custom_fields())
	setup_default_data()
	melon.db.commit()


def get_custom_fields():
	"""Define custom fields for core doctypes."""
	custom_fields = {
		"Project": [
			{
				"fieldname": "qs_details_section",
				"label": "Quantity Surveying Details",
				"fieldtype": "Section Break",
				"insert_after": "project_type"
			},
			{
				"fieldname": "boq_template",
				"label": "BoQ Template",
				"fieldtype": "Link",
				"options": "BoQ",
				"insert_after": "qs_details_section"
			},
			{
				"fieldname": "contract_value",
				"label": "Contract Value",
				"fieldtype": "Currency",
				"insert_after": "boq_template"
			},
			{
				"fieldname": "retention_percentage",
				"label": "Retention Percentage",
				"fieldtype": "Percent",
				"default": "5",
				"insert_after": "contract_value"
			}
		],
		"Item": [
			{
				"fieldname": "qs_section",
				"label": "Quantity Surveying",
				"fieldtype": "Section Break",
				"insert_after": "description"
			},
			{
				"fieldname": "is_construction_item",
				"label": "Is Construction Item",
				"fieldtype": "Check",
				"insert_after": "qs_section"
			},
		]
	}
	return custom_fields


def setup_default_data():
	"""Create default data for the app."""
	# Create default print formats
	create_default_print_formats()
	
	# Create default roles
	create_default_roles()


def create_default_print_formats():
	"""Create default print formats."""
	print_formats = [
		{
			"doctype": "Print Format",
			"name": "BoQ Standard Format",
			"doc_type": "BoQ",
			"print_format_type": "Jinja",
			"html": get_boq_print_format_html()
		},
		{
			"doctype": "Print Format", 
			"name": "Valuation Certificate",
			"doc_type": "Valuation",
			"print_format_type": "Jinja",
			"html": get_valuation_print_format_html()
		}
	]
	
	for pf in print_formats:
		if not melon.db.exists("Print Format", pf["name"]):
			doc = melon.get_doc(pf)
			doc.insert(ignore_permissions=True)


def create_default_roles():
	"""Create default roles for quantity surveying."""
	roles = [
		{
			"role_name": "Quantity Surveyor",
			"role_description": "Professional quantity surveyor with full access to quantity surveying functions"
		},
		{
			"role_name": "Construction Manager",
			"role_description": "Construction manager with access to valuations and progress tracking"
		},
		{
			"role_name": "Procurement Manager",
			"role_description": "Procurement manager with access to tender management"
		}
	]
	
	for role in roles:
		if not melon.db.exists("Role", role["role_name"]):
			melon.get_doc({
				"doctype": "Role",
				"role_name": role["role_name"],
				"desk_access": 1
			}).insert(ignore_permissions=True)


def get_boq_print_format_html():
	"""Return HTML template for BoQ print format."""
	return """
	<div class="print-format">
		<h2>{{ doc.title or "Bill of Quantities" }}</h2>
		<p><strong>Project:</strong> {{ doc.project }}</p>
		<p><strong>Date:</strong> {{ doc.date }}</p>
		
		<table class="table table-bordered">
			<thead>
				<tr>
					<th>Item</th>
					<th>Description</th>
					<th>Quantity</th>
					<th>UOM</th>
					<th>Rate</th>
					<th>Amount</th>
				</tr>
			</thead>
			<tbody>
				{% for item in doc.boq_items %}
				<tr>
					<td>{{ item.item }}</td>
					<td>{{ item.description }}</td>
					<td>{{ item.quantity }}</td>
					<td>{{ item.uom }}</td>
					<td>{{ melon.utils.fmt_money(item.rate) }}</td>
					<td>{{ melon.utils.fmt_money(item.amount) }}</td>
				</tr>
				{% endfor %}
			</tbody>
		</table>
		
		<div class="text-right">
			<h4><strong>Total: {{ melon.utils.fmt_money(doc.total_amount) }}</strong></h4>
		</div>
	</div>
	"""


def get_valuation_print_format_html():
	"""Return HTML template for valuation print format."""
	return """
	<div class="print-format">
		<h2>Valuation Certificate</h2>
		<p><strong>Project:</strong> {{ doc.project }}</p>
		<p><strong>Valuation No:</strong> {{ doc.name }}</p>
		<p><strong>Date:</strong> {{ doc.valuation_date }}</p>
		
		<table class="table table-bordered">
			<thead>
				<tr>
					<th>Item</th>
					<th>Quantity</th>
					<th>Rate</th>
					<th>Amount</th>
				</tr>
			</thead>
			<tbody>
				{% for item in doc.valuation_items %}
				<tr>
					<td>{{ item.item }}</td>
					<td>{{ item.quantity }}</td>
					<td>{{ melon.utils.fmt_money(item.rate) }}</td>
					<td>{{ melon.utils.fmt_money(item.amount) }}</td>
				</tr>
				{% endfor %}
			</tbody>
		</table>
		
		<div class="text-right">
			<h4><strong>Total Valuation: {{ melon.utils.fmt_money(doc.total_valuation) }}</strong></h4>
		</div>
	</div>
	"""
