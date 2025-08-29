# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.model.document import Document
from melon.utils import flt


class CostPlan(Document):
	def validate(self):
		self.validate_project()
		self.calculate_totals()
		self.calculate_budget_variance()
		self.set_status()

	def validate_project(self):
		if not self.project:
			melon.throw(_("Project is mandatory"))

	def calculate_totals(self):
		total_estimated_cost = 0
		
		for item in self.cost_plan_items:
			if item.estimated_cost:
				total_estimated_cost += flt(item.estimated_cost)
		
		self.total_estimated_cost = total_estimated_cost
		
		# Calculate contingency
		if self.contingency_percentage:
			self.contingency_amount = flt(self.total_estimated_cost) * flt(self.contingency_percentage) / 100
		
		# Calculate overhead
		if self.overhead_percentage:
			self.overhead_amount = flt(self.total_estimated_cost) * flt(self.overhead_percentage) / 100
		
		# Calculate total project cost
		self.total_project_cost = flt(self.total_estimated_cost) + flt(self.contingency_amount) + flt(self.overhead_amount)

	def calculate_budget_variance(self):
		if self.approved_budget and self.total_project_cost:
			self.budget_variance = flt(self.total_project_cost) - flt(self.approved_budget)

	def set_status(self):
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			self.status = "Submitted"
		elif self.docstatus == 2:
			self.status = "Cancelled"

	def on_submit(self):
		self.status = "Submitted"

	def on_cancel(self):
		self.status = "Cancelled"

	def before_insert(self):
		if not self.company:
			self.company = melon.defaults.get_user_default("Company")

@melon.whitelist()
def create_boq_from_cost_plan(cost_plan):
	"""Create BoQ from approved Cost Plan"""
	cost_plan_doc = melon.get_doc("Cost Plan", cost_plan)
	
	if cost_plan_doc.docstatus != 1:
		melon.throw(_("Only submitted cost plans can be used to create BoQ"))
	
	# Create new BoQ
	boq = melon.new_doc("BoQ")
	boq.title = f"BoQ from {cost_plan_doc.cost_plan_title}"
	boq.project = cost_plan_doc.project
	boq.company = cost_plan_doc.company
	boq.description = f"BoQ created from Cost Plan: {cost_plan_doc.name}"
	
	# Add items from cost plan
	for item in cost_plan_doc.cost_plan_items:
		boq_item = boq.append("boq_items")
		boq_item.item_code = item.item_code
		boq_item.item_name = item.item_name
		boq_item.description = item.description
		boq_item.uom = item.uom
		boq_item.quantity = item.estimated_quantity
		boq_item.rate = item.unit_rate
		boq_item.amount = item.estimated_cost
	
	boq.save()
	return boq

@melon.whitelist()
def get_cost_analysis(project):
	"""Get cost analysis for a project"""
	data = melon.db.sql("""
		SELECT 
			cp.name,
			cp.cost_plan_title,
			cp.total_project_cost,
			COALESCE(SUM(boq.total_amount), 0) as boq_total,
			COALESCE(SUM(val.current_valuation), 0) as certified_total
		FROM `tabCost Plan` cp
		LEFT JOIN `tabBoQ` boq ON boq.project = cp.project AND boq.docstatus = 1
		LEFT JOIN `tabValuation` val ON val.project = cp.project AND val.docstatus = 1
		WHERE cp.project = %s AND cp.docstatus = 1
		GROUP BY cp.name
		ORDER BY cp.creation DESC
	""", project, as_dict=1)
	
	return data
