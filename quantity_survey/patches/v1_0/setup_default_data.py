# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _


def execute():
	"""Setup default data for quantity survey app."""
	melon.reload_doc("quantity_surveying", "doctype", "boq")
	melon.reload_doc("quantity_surveying", "doctype", "valuation")
	melon.reload_doc("quantity_surveying", "doctype", "variation_order")
	melon.reload_doc("quantity_surveying", "doctype", "payment_certificate")
	
	# Create default BoQ templates
	create_default_boq_templates()
	
	# Setup default permissions
	setup_default_permissions()


def create_default_boq_templates():
	"""Create default BoQ templates."""
	templates = [
		{
			"title": "Standard Building Construction",
			"is_template": 1,
			"description": "Standard template for building construction projects"
		},
		{
			"title": "Road Construction",
			"is_template": 1, 
			"description": "Template for road and infrastructure projects"
		}
	]
	
	for template in templates:
		if not melon.db.exists("BoQ", {"title": template["title"], "is_template": 1}):
			doc = melon.get_doc(dict(doctype="BoQ", **template))
			doc.insert(ignore_permissions=True)


def setup_default_permissions():
	"""Setup default permissions for quantity surveying doctypes."""
	# This will be handled by role permission manager
	pass
