# Copyright (c) 2025, Alphamonak Solutions


from melon.model.document import Document
from melon.utils import flt


class ValuationItem(Document):
	def validate(self):
		self.calculate_cumulative_quantity()
		self.calculate_amounts()

	def calculate_cumulative_quantity(self):
		if self.previous_quantity and self.current_quantity:
			self.cumulative_quantity = flt(self.previous_quantity) + flt(self.current_quantity)
		elif self.current_quantity:
			self.cumulative_quantity = flt(self.current_quantity)

	def calculate_amounts(self):
		if self.current_quantity and self.rate:
			self.current_amount = flt(self.current_quantity) * flt(self.rate)
		
		if self.cumulative_quantity and self.rate:
			self.cumulative_amount = flt(self.cumulative_quantity) * flt(self.rate)
