# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon.model.document import Document
from melon.utils import flt


class TenderQuote(Document):
	def validate(self):
		"""Validate Tender Quote"""
		self.validate_tender_deadline()
		self.calculate_totals()
		self.calculate_overall_score()
	
	def on_submit(self):
		"""Actions on submit"""
		self.quote_status = "Submitted"
		self.update_tender_package_summary()
	
	def validate_tender_deadline(self):
		"""Check if quote is submitted before deadline"""
		tender_package = melon.get_doc("Tender Package", self.tender_package)
		if tender_package.bid_submission_deadline:
			if melon.utils.now_datetime() > tender_package.bid_submission_deadline:
				melon.throw("Quote submission deadline has passed")
	
	def calculate_totals(self):
		"""Calculate quote totals"""
		total_base = 0
		
		for item in self.quote_items:
			if item.quantity and item.unit_rate:
				item.amount = flt(item.quantity * item.unit_rate, 2)
				total_base += item.amount
		
		self.total_base_amount = total_base
		
		# Calculate discount
		if self.discount_percentage:
			self.discount_amount = flt(total_base * self.discount_percentage / 100, 2)
		else:
			self.discount_amount = 0
		
		# Calculate tax
		net_amount = total_base - self.discount_amount
		if self.tax_percentage:
			self.tax_amount = flt(net_amount * self.tax_percentage / 100, 2)
		else:
			self.tax_amount = 0
		
		# Final total
		self.total_quote_amount = net_amount + self.tax_amount
	
	def calculate_overall_score(self):
		"""Calculate overall evaluation score"""
		if self.technical_compliance and self.commercial_compliance:
			# Weighted scoring: 60% technical, 40% commercial
			technical_weight = 0.6
			commercial_weight = 0.4
			
			self.overall_score = flt(
				(self.technical_compliance * technical_weight) + 
				(self.commercial_compliance * commercial_weight), 2
			)
	
	def update_tender_package_summary(self):
		"""Update tender package with quote summary"""
		tender_package = melon.get_doc("Tender Package", self.tender_package)
		tender_package.update_quote_summary()
	
	@melon.whitelist()
	def get_boq_items(self):
		"""Get BoQ items from tender package project"""
		tender_package = melon.get_doc("Tender Package", self.tender_package)
		
		# Get BoQ from project
		boq_list = melon.get_all("BoQ", 
			filters={"project": tender_package.project, "docstatus": 1},
			fields=["name"],
			limit=1
		)
		
		if not boq_list:
			melon.throw("No approved BoQ found for this project")
		
		boq = melon.get_doc("BoQ", boq_list[0].name)
		
		# Clear existing items
		self.quote_items = []
		
		# Add BoQ items to quote
		for item in boq.boq_items:
			self.append("quote_items", {
				"item_code": item.item_code,
				"item_name": item.item_name,
				"description": item.description,
				"uom": item.uom,
				"quantity": item.quantity,
				"unit_rate": 0  # Contractor to fill
			})
		
		self.save()
		melon.msgprint("BoQ items loaded successfully. Please update unit rates.")
	
	@melon.whitelist()
	def compare_with_estimate(self):
		"""Compare quote with project estimate"""
		tender_package = melon.get_doc("Tender Package", self.tender_package)
		
		comparison = {
			"estimated_value": tender_package.estimated_value,
			"quote_amount": self.total_quote_amount,
			"variance_amount": self.total_quote_amount - tender_package.estimated_value,
			"variance_percentage": ((self.total_quote_amount - tender_package.estimated_value) / tender_package.estimated_value * 100) if tender_package.estimated_value else 0
		}
		
		return comparison
