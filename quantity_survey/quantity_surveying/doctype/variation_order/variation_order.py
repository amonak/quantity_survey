# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.model.document import Document
from melon.utils import flt


class VariationOrder(Document):
	def validate(self):
		"""Validate variation order document"""
		self.validate_mandatory_fields()
		self.validate_boq()
		self.validate_project()
		self.calculate_total_amount()
		self.calculate_variation_percentage()
		self.set_status()

	def validate_mandatory_fields(self):
		"""Validate mandatory fields"""
		if not self.variation_type:
			melon.throw(_("Variation Type is mandatory"))
		
		if not self.description:
			melon.throw(_("Description is mandatory"))

	def validate_boq(self):
		"""Validate BoQ reference"""
		if not self.boq:
			melon.throw(_("BoQ is mandatory"))
		
		# Check if BoQ exists and is submitted
		boq_doc = melon.get_doc("BoQ", self.boq)
		if boq_doc.docstatus != 1:
			melon.throw(_("Referenced BoQ must be submitted"))

	def validate_project(self):
		"""Validate project reference"""
		if not self.project:
			melon.throw(_("Project is mandatory"))
		
		# Ensure project matches BoQ project
		if self.boq:
			boq_project = melon.db.get_value("BoQ", self.boq, "project")
			if boq_project != self.project:
				melon.throw(_("Project must match the BoQ project"))

	def calculate_total_amount(self):
		"""Calculate total variation amount from items"""
		total_amount = 0
		
		for item in self.variation_items:
			if item.quantity and item.rate:
				item_amount = flt(item.quantity) * flt(item.rate)
				
				# Handle variation type at item level
				if item.variation_type == "Omission":
					item_amount = -abs(item_amount)
				elif item.variation_type == "Addition":
					item_amount = abs(item_amount)
				
				item.amount = item_amount
				total_amount += item_amount
		
		self.total_variation_amount = total_amount

	def calculate_variation_percentage(self):
		"""Calculate variation percentage against original contract"""
		if self.original_contract_value and self.total_variation_amount:
			self.variation_percentage = (
				flt(self.total_variation_amount) / flt(self.original_contract_value)
			) * 100
		else:
			self.variation_percentage = 0

	def set_status(self):
		"""Set document status"""
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			if self.approval_status == "Approved":
				self.status = "Approved"
			elif self.approval_status == "Rejected":
				self.status = "Rejected"
			else:
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
def approve_variation_order(variation_order):
	"""Approve a variation order with proper validation"""
	if not variation_order:
		melon.throw(_("Variation Order is required"))
	
	if not melon.has_permission("Variation Order", "write", variation_order):
		melon.throw(_("Insufficient permissions to approve variation order"))
	
	doc = melon.get_doc("Variation Order", variation_order)
	if doc.docstatus != 1:
		melon.throw(_("Only submitted variation orders can be approved"))
	
	if doc.approval_status == "Approved":
		melon.throw(_("Variation order is already approved"))
	
	doc.approval_status = "Approved"
	doc.approved_by = melon.session.user
	doc.approved_date = melon.utils.today()
	doc.status = "Approved"
	doc.save(ignore_permissions=True)
	
	# Send notification
	_send_approval_notification(doc)
	
	return {
		"status": "success",
		"message": _("Variation order approved successfully"),
		"doc": doc.as_dict()
	}

@melon.whitelist()
def reject_variation_order(variation_order, reason=None):
	"""Reject a variation order with proper validation"""
	if not variation_order:
		melon.throw(_("Variation Order is required"))
	
	if not melon.has_permission("Variation Order", "write", variation_order):
		melon.throw(_("Insufficient permissions to reject variation order"))
	
	doc = melon.get_doc("Variation Order", variation_order)
	if doc.docstatus != 1:
		melon.throw(_("Only submitted variation orders can be rejected"))
	
	if doc.approval_status == "Rejected":
		melon.throw(_("Variation order is already rejected"))
	
	doc.approval_status = "Rejected"
	doc.approved_by = melon.session.user
	doc.approved_date = melon.utils.today()
	doc.status = "Rejected"
	if reason:
		doc.rejection_reason = reason
	doc.save(ignore_permissions=True)
	
	# Send notification
	_send_rejection_notification(doc, reason)
	
	return {
		"status": "success",
		"message": _("Variation order rejected"),
		"doc": doc.as_dict()
	}

@melon.whitelist()
def get_boq_items_for_variation(boq):
	"""Get BoQ items for creating variation order"""
	if not boq:
		melon.throw(_("BoQ is required"))
	
	if not melon.has_permission("BoQ", "read", boq):
		melon.throw(_("Insufficient permissions to access BoQ"))
	
	items = melon.db.get_all("BoQ Item",
		filters={"parent": boq},
		fields=[
			"item_code", "item_name", "description", "uom",
			"quantity", "rate", "amount"
		],
		order_by="idx"
	)
	
	return items

def _send_approval_notification(doc):
	"""Send approval notification"""
	try:
		recipients = []
		if doc.owner:
			recipients.append(doc.owner)
		
		if recipients:
			melon.sendmail(
				recipients=recipients,
				subject=_("Variation Order {0} Approved").format(doc.name),
				message=_("Your variation order {0} for project {1} has been approved.").format(
					doc.name, doc.project
				)
			)
	except Exception as e:
		melon.log_error(f"Error sending approval notification: {str(e)}")

def _send_rejection_notification(doc, reason):
	"""Send rejection notification"""
	try:
		recipients = []
		if doc.owner:
			recipients.append(doc.owner)
		
		if recipients:
			message = _("Your variation order {0} for project {1} has been rejected.").format(
				doc.name, doc.project
			)
			if reason:
				message += f"\n\nReason: {reason}"
			
			melon.sendmail(
				recipients=recipients,
				subject=_("Variation Order {0} Rejected").format(doc.name),
				message=message
			)
	except Exception as e:
		melon.log_error(f"Error sending rejection notification: {str(e)}")
