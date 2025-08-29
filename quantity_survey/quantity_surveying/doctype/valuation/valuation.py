# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.model.document import Document
from melon.utils import flt


class Valuation(Document):
	"""Valuation document for tracking work progress and payments."""
	
	def validate(self):
		"""Validate valuation document."""
		self.validate_boq()
		self.calculate_totals()
		self.calculate_retention()
		self.set_status()

	def validate_boq(self):
		"""Validate that BoQ is selected and valid."""
		if not self.boq:
			melon.throw(_("BoQ is mandatory"))

	def calculate_totals(self):
		"""Calculate total work done and current valuation amounts."""
		total_work_done = 0
		current_valuation = 0
		
		for item in self.valuation_items:
			if item.current_quantity and item.rate:
				item.current_amount = flt(item.current_quantity) * flt(item.rate)
				current_valuation += flt(item.current_amount)
			
			if item.cumulative_quantity and item.rate:
				item.cumulative_amount = flt(item.cumulative_quantity) * flt(item.rate)
				total_work_done += flt(item.cumulative_amount)
		
		self.total_work_done = total_work_done
		self.current_valuation = current_valuation
		self.cumulative_total = total_work_done

	def calculate_retention(self):
		"""Calculate retention amount and net payable."""
		if self.retention_percentage and self.current_valuation:
			self.retention_amount = flt(self.current_valuation) * flt(self.retention_percentage) / 100
			self.net_payable = flt(self.current_valuation) - flt(self.retention_amount)
		else:
			self.retention_amount = 0
			self.net_payable = flt(self.current_valuation)

	def set_status(self):
		"""Set status based on document status."""
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			self.status = "Submitted"
		elif self.docstatus == 2:
			self.status = "Cancelled"

	def on_submit(self):
		self.status = "Submitted"
		self.update_previous_valuations()

	def on_cancel(self):
		self.status = "Cancelled"

	def update_previous_valuations(self):
		"""Update previous total for next valuation"""
		previous_total = melon.db.sql("""
			SELECT SUM(current_valuation) 
			FROM `tabValuation` 
			WHERE boq = %s AND docstatus = 1 AND name != %s
		""", (self.boq, self.name))[0][0] or 0
		
		self.previous_total = previous_total

	def before_insert(self):
		if not self.company:
			self.company = melon.defaults.get_user_default("Company")

@melon.whitelist()
def get_boq_items_for_valuation(boq):
	"""Get BoQ items for valuation with proper error handling"""
	if not boq:
		melon.throw(_("BoQ is required"))
	
	if not melon.has_permission("BoQ", "read", boq):
		melon.throw(_("Insufficient permission to access BoQ"))
	
	items = melon.db.get_all("BoQ Item",
		filters={"parent": boq},
		fields=[
			"item_code", "item_name", "description", "uom",
			"quantity as boq_quantity", "rate", "amount as boq_amount"
		],
		order_by="idx"
	)
	
	return items

@melon.whitelist()
def get_previous_valuation_data(boq, current_valuation=None):
	"""Get previous valuation data for the same BoQ with proper validation"""
	if not boq:
		melon.throw(_("BoQ is required"))
	
	conditions = []
	values = {"boq": boq}
	
	if current_valuation:
		conditions.append("v.name != %(current_valuation)s")
		values["current_valuation"] = current_valuation
	
	condition_str = f" AND {' AND '.join(conditions)}" if conditions else ""
	
	data = melon.db.sql(f"""
		SELECT 
			vi.item_code,
			SUM(vi.cumulative_quantity) as previous_cumulative_quantity,
			SUM(vi.cumulative_amount) as previous_cumulative_amount
		FROM `tabValuation Item` vi
		INNER JOIN `tabValuation` v ON v.name = vi.parent
		WHERE v.boq = %(boq)s AND v.docstatus = 1{condition_str}
		GROUP BY vi.item_code
	""", values, as_dict=True)
	
	return {d.item_code: d for d in data}
