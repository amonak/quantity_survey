# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon.model.document import Document


class CostPlanItem(Document):
	def validate(self):
		"""Validate Cost Plan Item"""
		self.calculate_estimated_cost()
		self.calculate_variance_percentage()
	
	def calculate_estimated_cost(self):
		"""Calculate estimated cost based on quantity and unit rate"""
		if self.estimated_quantity and self.unit_rate:
			self.estimated_cost = self.estimated_quantity * self.unit_rate
	
	def calculate_variance_percentage(self):
		"""Calculate variance percentage between unit rate and market rate"""
		if self.unit_rate and self.market_rate:
			variance = (self.unit_rate - self.market_rate) / self.market_rate * 100
			self.variance_percentage = variance
