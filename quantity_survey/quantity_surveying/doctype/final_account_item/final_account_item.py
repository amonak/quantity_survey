# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon.model.document import Document


class FinalAccountItem(Document):
	def validate(self):
		"""Validate Final Account Item"""
		self.calculate_final_amount()
		self.calculate_variances()
	
	def calculate_final_amount(self):
		"""Calculate final amount based on quantity and rate"""
		if self.final_quantity and self.final_rate:
			self.final_amount = self.final_quantity * self.final_rate
	
	def calculate_variances(self):
		"""Calculate variances between original and final"""
		if self.original_quantity and self.final_quantity:
			self.quantity_variance = self.final_quantity - self.original_quantity
		
		if self.original_rate and self.final_rate:
			self.rate_variance = self.final_rate - self.original_rate
		
		if self.original_amount and self.final_amount:
			self.amount_variance = self.final_amount - self.original_amount
