# -*- coding: utf-8 -*-
# Copyright (c) 2024, [Your Company] 


import melon
from melon import _
from melon.model.document import Document


class CollaborationSession(Document):
	def before_insert(self):
		"""Set created_at timestamp"""
		if not self.created_at:
			self.created_at = melon.utils.now_datetime()
		
		if not self.created_by:
			self.created_by = melon.session.user
	
	def before_save(self):
		"""Update last_activity timestamp"""
		self.last_activity = melon.utils.now_datetime()
	
	def validate(self):
		"""Validate collaboration session"""
		# Ensure reference document exists
		if not melon.db.exists(self.reference_doctype, self.reference_name):
			melon.throw(_("Reference document {0} {1} does not exist").format(
				self.reference_doctype, self.reference_name
			))
		
		# Ensure user has permission to the reference document
		if not melon.has_permission(self.reference_doctype, "read", self.reference_name):
			melon.throw(_("Insufficient permissions for collaboration session"))
