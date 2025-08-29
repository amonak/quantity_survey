# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.model.document import Document


class QuantitySurveySettings(Document):
	"""Settings for Quantity Survey module"""
	
	def validate(self):
		"""Validate settings"""
		self.validate_accounts()
		self.validate_percentage_values()
	
	def validate_accounts(self):
		"""Validate account settings"""
		if self.create_accounting_entries:
			required_accounts = [
				('default_wip_account', 'Work in Progress Account'),
				('default_creditors_account', 'Creditors Account'),
				('default_retention_account', 'Retention Account')
			]
			
			for field, label in required_accounts:
				if not self.get(field):
					melon.throw(_("{0} is mandatory when accounting entries are enabled").format(label))
	
	def validate_percentage_values(self):
		"""Validate percentage fields"""
		if self.default_retention_percentage and (
			self.default_retention_percentage < 0 or 
			self.default_retention_percentage > 50
		):
			melon.throw(_("Default Retention Percentage should be between 0 and 50"))
		
		if self.budget_alert_threshold and (
			self.budget_alert_threshold < 0 or 
			self.budget_alert_threshold > 100
		):
			melon.throw(_("Budget Alert Threshold should be between 0 and 100"))
	
	def on_update(self):
		"""Clear cache on settings update"""
		melon.clear_cache()
