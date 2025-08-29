# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.model.document import Document
from melon.utils import flt


class FinalAccount(Document):
	"""Final Account document for project closure and cost reconciliation."""
	
	def validate(self):
		"""Validate Final Account document."""
		self.calculate_contract_adjustments()
		self.calculate_payment_summary()
		self.calculate_final_amounts()
	
	def on_submit(self):
		"""Actions to perform on document submission."""
		self.status = "Under Review"
		self.update_project_status()
	
	def calculate_contract_adjustments(self):
		"""Calculate adjusted contract value including variations and claims."""
		self.get_approved_variations()
		
		adjusted_value = flt(self.original_contract_value, 2)
		adjusted_value += flt(self.approved_variations_total, 2)
		adjusted_value += flt(self.claims_amount, 2)
		adjusted_value -= flt(self.contra_charges, 2)
		
		self.adjusted_contract_value = adjusted_value
	
	def get_approved_variations(self):
		"""Get total approved variations from project"""
		try:
			variations = melon.db.get_all("Variation Order",
				filters={
					"project": self.project,
					"status": "Approved",
					"docstatus": 1
				},
				fields=["sum(total_variation_amount) as total"]
			)
			
			if variations and variations[0] and variations[0].total:
				self.approved_variations_total = flt(variations[0].total, 2)
			else:
				self.approved_variations_total = 0
		except Exception as e:
			melon.log_error(f"Error getting approved variations: {str(e)}")
			self.approved_variations_total = 0
	
	def calculate_payment_summary(self):
		"""Calculate payment summary from payment certificates"""
		certificates = melon.get_all("Payment Certificate",
			filters={
				"project": self.project,
				"contractor": self.contractor,
				"docstatus": 1
			},
			fields=["sum(net_payment_amount) as total"]
		)
		
		if certificates and certificates[0].total:
			self.previous_payments = certificates[0].total
		else:
			self.previous_payments = 0
		
		# Calculate current payment due
		total_work_value = flt(self.work_done_to_date, 2) + flt(self.materials_on_site, 2)
		self.current_payment_due = total_work_value - flt(self.previous_payments, 2)
	
	def calculate_final_amounts(self):
		"""Calculate final payment amounts"""
		# Calculate total from items
		total_certified = 0
		for item in self.final_account_items:
			if item.final_amount:
				total_certified += item.final_amount
		
		self.total_certified_value = total_certified
		
		# Calculate retention
		if self.less_retention_percentage:
			self.retention_amount = flt(total_certified * self.less_retention_percentage / 100, 2)
		else:
			self.retention_amount = 0
		
		# Net amount
		self.net_amount_due = total_certified - self.retention_amount
		
		# VAT calculation
		if self.vat_percentage:
			self.vat_amount = flt(self.net_amount_due * self.vat_percentage / 100, 2)
		else:
			self.vat_amount = 0
		
		# Gross amount
		self.gross_amount_payable = self.net_amount_due + self.vat_amount
		
		# Final payment calculation
		self.final_payment_amount = self.gross_amount_payable - flt(self.previous_payments, 2)
	
	def update_project_status(self):
		"""Update project status on final account submission"""
		project = melon.get_doc("Project", self.project)
		if project.status != "Completed":
			project.status = "Completed"
			project.percent_complete = 100
			project.save()
	
	@melon.whitelist()
	def load_project_data(self):
		"""Load project data for final account"""
		if not self.project:
			melon.throw("Please select a project first")
		
		project = melon.get_doc("Project", self.project)
		
		# Get BoQ items
		boq_list = melon.get_all("BoQ",
			filters={"project": self.project, "docstatus": 1},
			fields=["name"],
			limit=1
		)
		
		if boq_list:
			boq = melon.get_doc("BoQ", boq_list[0].name)
			
			# Clear existing items
			self.final_account_items = []
			
			# Add BoQ items
			for item in boq.boq_items:
				self.append("final_account_items", {
					"item_code": item.item_code,
					"item_name": item.item_name,
					"description": item.description,
					"uom": item.uom,
					"original_quantity": item.quantity,
					"original_rate": item.rate,
					"original_amount": item.amount,
					"final_quantity": item.quantity,  # To be adjusted
					"final_rate": item.rate,  # To be adjusted
					"final_amount": item.amount  # To be calculated
				})
		
		# Load variations
		self.get_approved_variations()
		
		# Load payment history
		self.calculate_payment_summary()
		
		self.save()
		melon.msgprint("Project data loaded successfully")
	
	@melon.whitelist()
	def generate_cost_analysis(self):
		"""Generate comprehensive cost variance analysis"""
		if not self.project:
			return {}
		
		# Original contract vs final account
		analysis = {
			"original_contract": self.original_contract_value,
			"final_account": self.adjusted_contract_value,
			"total_variance": self.adjusted_contract_value - self.original_contract_value,
			"variance_percentage": ((self.adjusted_contract_value - self.original_contract_value) / self.original_contract_value * 100) if self.original_contract_value else 0
		}
		
		# Breakdown by category
		breakdown = {}
		for item in self.final_account_items:
			category = item.item_category or "Other"
			if category not in breakdown:
				breakdown[category] = {
					"original_amount": 0,
					"final_amount": 0,
					"variance": 0
				}
			
			breakdown[category]["original_amount"] += flt(item.original_amount, 2)
			breakdown[category]["final_amount"] += flt(item.final_amount, 2)
			breakdown[category]["variance"] = breakdown[category]["final_amount"] - breakdown[category]["original_amount"]
		
		analysis["category_breakdown"] = breakdown
		
		return analysis
	
	@melon.whitelist()
	def create_final_payment(self):
		"""Create final payment certificate"""
		if self.status != "Agreed":
			melon.throw("Final account must be agreed before creating payment")
		
		if self.final_payment_amount <= 0:
			melon.throw("No payment amount due")
		
		# Create Payment Certificate
		payment_cert = melon.new_doc("Payment Certificate")
		payment_cert.project = self.project
		payment_cert.contractor = self.contractor
		payment_cert.certificate_type = "Final"
		payment_cert.valuation_date = self.final_account_date
		payment_cert.work_completed_value = self.total_certified_value
		payment_cert.retention_percentage = self.less_retention_percentage
		payment_cert.retention_amount = self.retention_amount
		payment_cert.net_payment_amount = self.final_payment_amount
		payment_cert.remarks = f"Final payment based on Final Account {self.name}"
		
		payment_cert.insert()
		melon.msgprint(f"Payment Certificate {payment_cert.name} created successfully")
		
		return payment_cert.name
