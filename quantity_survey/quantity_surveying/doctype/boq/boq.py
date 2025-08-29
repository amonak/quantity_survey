# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.model.document import Document
from melon.utils import flt


class BoQ(Document):
	"""Bill of Quantities for construction projects."""
	
	def validate(self):
		"""Validate BoQ document."""
		self.validate_project()
		self.calculate_totals()
		self.set_status()

	def validate_project(self):
		"""Validate that project is selected and valid."""
		if not self.project:
			melon.throw(_("Project is mandatory"))

	def calculate_totals(self):
		"""Calculate total quantities and amounts from BoQ items."""
		total_quantity = 0
		total_amount = 0
		
		for item in self.boq_items:
			if item.quantity and item.rate:
				item.amount = flt(item.quantity) * flt(item.rate)
				total_quantity += flt(item.quantity)
				total_amount += flt(item.amount)
		
		self.total_quantity = total_quantity
		self.total_amount = total_amount

	def set_status(self):
		"""Set status based on document status."""
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			self.status = "Submitted"
		elif self.docstatus == 2:
			self.status = "Cancelled"

	def on_submit(self):
		"""Actions to perform on document submission."""
		self.status = "Submitted"

	def on_cancel(self):
		"""Actions to perform on document cancellation."""
		self.status = "Cancelled"

	def before_insert(self):
		"""Set default values before inserting document."""
		if not self.company:
			self.company = melon.defaults.get_user_default("Company")

@melon.whitelist()
def get_boq_items(boq):
	"""Get BoQ items for a specific BoQ"""
	if not boq:
		melon.throw(_("BoQ is required"))
	
	items = melon.get_all("BoQ Item", 
		filters={"parent": boq}, 
		fields=["item_code", "item_name", "description", "uom", "quantity", "rate", "amount", "idx"]
	)
	return items

@melon.whitelist()
def duplicate_boq(source_name, target_doc=None):
	"""Duplicate BoQ with items"""
	from melon.model.mapper import get_mapped_doc
	
	def update_item(source_doc, target_doc, source_parent):
		target_doc.quantity = 0  # Reset quantities in duplicated BoQ
		target_doc.amount = 0
	
	doclist = get_mapped_doc("BoQ", source_name, {
		"BoQ": {
			"doctype": "BoQ",
			"field_map": {
				"name": "reference_boq"
			},
			"field_no_map": ["naming_series"]
		},
		"BoQ Item": {
			"doctype": "BoQ Item",
			"postprocess": update_item
		}
	}, target_doc)
	
	return doclist
