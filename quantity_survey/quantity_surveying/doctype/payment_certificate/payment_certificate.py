# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.model.document import Document
from melon.utils import flt, nowdate, add_days, getdate


class PaymentCertificate(Document):
	def before_insert(self):
		"""Set default values before inserting the document"""
		if not self.certificate_date:
			self.certificate_date = nowdate()
		
		if not self.payment_due_date and self.certificate_date:
			# Set payment due date to 30 days from certificate date by default
			self.payment_due_date = add_days(self.certificate_date, 30)
	
	def validate(self):
		"""Validate the payment certificate data"""
		self.validate_dates()
		self.validate_project()
		self.validate_valuation_reference()
		self.calculate_payment_amounts()
		self.validate_payment_amounts()
	
	def validate_dates(self):
		"""Validate certificate and payment due dates"""
		if self.certificate_date and self.payment_due_date:
			if getdate(self.payment_due_date) < getdate(self.certificate_date):
				melon.throw(_("Payment Due Date cannot be before Certificate Date"))
	
	def validate_project(self):
		"""Validate project reference"""
		if not self.project:
			melon.throw(_("Project is mandatory"))
		
		# Check if project exists and is active
		project = melon.get_doc("Project", self.project)
		if project.status == "Cancelled":
			melon.throw(_("Cannot create Payment Certificate for cancelled project"))
	
	def validate_valuation_reference(self):
		"""Validate valuation reference"""
		if self.valuation_reference:
			valuation = melon.get_doc("Valuation", self.valuation_reference)
			if valuation.docstatus != 1:
				melon.throw(_("Referenced Valuation must be submitted"))
			
			if valuation.project != self.project:
				melon.throw(_("Valuation project must match Payment Certificate project"))
	
	def calculate_payment_amounts(self):
		"""Calculate payment amounts based on valuation and deductions"""
		if not self.gross_amount:
			return
		
		# Calculate retention amount
		if self.retention_percentage and self.gross_amount:
			self.retention_amount = flt(self.gross_amount * self.retention_percentage / 100, 2)
		
		# Calculate net payment amount
		gross_amount = flt(self.gross_amount)
		retention_amount = flt(self.retention_amount)
		advance_recovery = flt(self.advance_recovery)
		other_deductions = flt(self.other_deductions)
		previous_payments = flt(self.previous_payments)
		
		self.net_payment_amount = flt(
			gross_amount - retention_amount - advance_recovery - 
			other_deductions - previous_payments, 2
		)
		
		# Update cumulative amounts
		self.cumulative_gross_amount = flt(previous_payments + gross_amount, 2)
		self.cumulative_retention = flt(self.cumulative_retention + retention_amount, 2)
	
	def validate_payment_amounts(self):
		"""Validate calculated amounts"""
		if flt(self.net_payment_amount) < 0:
			melon.throw(_("Net Payment Amount cannot be negative"))
		
		if self.retention_percentage and (flt(self.retention_percentage) < 0 or flt(self.retention_percentage) > 50):
			melon.throw(_("Retention Percentage should be between 0 and 50"))
	
	def on_submit(self):
		"""Actions to perform when payment certificate is submitted"""
		self.update_project_progress()
		self.create_accounting_entries()
		self.send_notifications()
	
	def on_cancel(self):
		"""Actions to perform when payment certificate is cancelled"""
		self.cancel_accounting_entries()
		self.update_project_progress()
	
	def update_project_progress(self):
		"""Update project progress based on payment certificate"""
		if not self.project:
			return
		
		try:
			# Calculate total certified amount for the project
			total_certified = melon.db.sql("""
				SELECT SUM(gross_amount)
				FROM `tabPayment Certificate`
				WHERE project = %s AND docstatus = 1
			""", self.project)[0][0] or 0
			
			# Get project contract value
			project = melon.get_doc("Project", self.project)
			if hasattr(project, 'contract_value') and project.contract_value:
				progress_percentage = min((total_certified / project.contract_value) * 100, 100)
				
				# Update project progress
				melon.db.set_value("Project", self.project, {
					"percent_complete": progress_percentage,
					"total_certified_amount": total_certified
				})
				
		except Exception as e:
			melon.log_error(f"Error updating project progress: {str(e)}")
	
	def create_accounting_entries(self):
		"""Create accounting entries for the payment certificate"""
		if not melon.db.get_single_value("Quantity Survey Settings", "create_accounting_entries"):
			return
		
		try:
			from monak.accounts.general_ledger import make_gl_entries
			
			gl_entries = self._prepare_gl_entries()
			
			if gl_entries:
				make_gl_entries(gl_entries, cancel=False, adv_adj=False)
				
		except Exception as e:
			melon.log_error(f"Error creating accounting entries: {str(e)}")
	
	def _prepare_gl_entries(self):
		"""Prepare GL entries for the payment certificate"""
		gl_entries = []
		
		# Work in Progress Dr.
		if self.gross_amount:
			gl_entries.append(self._get_gl_entry(
				account=self.get_account("work_in_progress_account"),
				debit=flt(self.gross_amount),
				credit=0,
				against=self.get_account("creditors_account"),
				remarks=f"Work in Progress for {self.project}"
			))
		
		# Creditors/Contractor Cr.
		if self.net_payment_amount:
			gl_entries.append(self._get_gl_entry(
				account=self.get_account("creditors_account"),
				debit=0,
				credit=flt(self.net_payment_amount),
				against=self.get_account("work_in_progress_account"),
				remarks=f"Payment due to contractor for {self.project}"
			))
		
		# Retention Payable Cr.
		if self.retention_amount:
			gl_entries.append(self._get_gl_entry(
				account=self.get_account("retention_payable_account"),
				debit=0,
				credit=flt(self.retention_amount),
				against=self.get_account("work_in_progress_account"),
				remarks=f"Retention payable for {self.project}"
			))
		
		return gl_entries
	
	def _get_gl_entry(self, account, debit, credit, against, remarks):
		"""Get formatted GL entry"""
		return {
			"account": account,
			"debit": debit,
			"credit": credit,
			"against": against,
			"project": self.project,
			"voucher_type": "Payment Certificate",
			"voucher_no": self.name,
			"posting_date": self.certificate_date,
			"remarks": remarks
		}
	
	def cancel_accounting_entries(self):
		"""Cancel accounting entries when payment certificate is cancelled"""
		try:
			from monak.accounts.general_ledger import make_gl_entries
			
			# Get existing GL entries
			existing_entries = melon.get_all("GL Entry", 
				filters={
					"voucher_type": "Payment Certificate",
					"voucher_no": self.name
				},
				fields=["*"]
			)
			
			if existing_entries:
				# Cancel the entries by creating reverse entries
				make_gl_entries(existing_entries, cancel=True, adv_adj=False)
				
		except Exception as e:
			melon.log_error(f"Error cancelling accounting entries: {str(e)}")
	
	def get_account(self, account_type):
		"""Get account based on account type"""
		settings = melon.get_single("Quantity Survey Settings")
		
		account_map = {
			"work_in_progress_account": settings.get("default_wip_account"),
			"creditors_account": settings.get("default_creditors_account"),
			"retention_payable_account": settings.get("default_retention_account")
		}
		
		account = account_map.get(account_type)
		if not account:
			melon.throw(_("Please set up default accounts in Quantity Survey Settings"))
		
		return account
	
	def send_notifications(self):
		"""Send email notifications to stakeholders"""
		try:
			# Get notification recipients
			recipients = []
			
			# Project Manager
			if self.project:
				project = melon.get_doc("Project", self.project)
				if hasattr(project, 'project_manager') and project.project_manager:
					user_email = melon.db.get_value("User", project.project_manager, "email")
					if user_email:
						recipients.append(user_email)
			
			# Certificate approvers
			if self.approved_by:
				user_email = melon.db.get_value("User", self.approved_by, "email")
				if user_email:
					recipients.append(user_email)
			
			if recipients:
				melon.sendmail(
					recipients=list(set(recipients)),  # Remove duplicates
					subject=f"Payment Certificate {self.name} - {self.project}",
					template="payment_certificate_notification",
					args={
						"doc": self,
						"certificate_url": melon.utils.get_url_to_form("Payment Certificate", self.name)
					}
				)
				
		except Exception as e:
			melon.log_error(f"Error sending notifications: {str(e)}")


@melon.whitelist()
def get_valuation_details(valuation):
	"""Get valuation details for payment certificate"""
	if not valuation:
		return {}
	
	valuation_doc = melon.get_doc("Valuation", valuation)
	
	return {
		"project": valuation_doc.project,
		"gross_amount": valuation_doc.total_amount,
		"valuation_date": valuation_doc.valuation_date,
		"valuation_period": valuation_doc.valuation_period
	}


@melon.whitelist()
def get_previous_payments(project):
	"""Get total of previous payments for the project"""
	if not project:
		return 0
	
	total_previous = melon.db.sql("""
		SELECT SUM(net_payment_amount)
		FROM `tabPayment Certificate`
		WHERE project = %s AND docstatus = 1
	""", project)[0][0] or 0
	
	return flt(total_previous, 2)


@melon.whitelist()
def get_project_retention_rate(project):
	"""Get retention rate from project settings"""
	if not project:
		return 0
	
	project_doc = melon.get_doc("Project", project)
	if hasattr(project_doc, 'retention_percentage'):
		return project_doc.retention_percentage
	
	# Fallback to system default
	return melon.db.get_single_value("Quantity Survey Settings", "default_retention_percentage") or 5


@melon.whitelist()
def create_payment_entry(payment_certificate):
	"""Create payment entry from payment certificate"""
	if not payment_certificate:
		melon.throw(_("Payment Certificate is required"))
	
	pc_doc = melon.get_doc("Payment Certificate", payment_certificate)
	
	if pc_doc.docstatus != 1:
		melon.throw(_("Payment Certificate must be submitted"))
	
	# Check if payment entry already exists
	existing_payment = melon.db.exists("Payment Entry", {
		"reference_no": payment_certificate,
		"docstatus": ["!=", 2]
	})
	
	if existing_payment:
		melon.throw(_("Payment Entry already exists for this certificate"))
	
	try:
		# Create Payment Entry
		payment_entry = melon.new_doc("Payment Entry")
		payment_entry.payment_type = "Pay"
		payment_entry.posting_date = nowdate()
		payment_entry.reference_no = payment_certificate
		payment_entry.reference_date = pc_doc.certificate_date
		payment_entry.paid_amount = pc_doc.net_payment_amount
		payment_entry.received_amount = pc_doc.net_payment_amount
		payment_entry.project = pc_doc.project
		payment_entry.remarks = f"Payment for Certificate {payment_certificate} - {pc_doc.project}"
		
		return payment_entry.as_dict()
		
	except Exception as e:
		melon.throw(_("Error creating payment entry: {0}").format(str(e)))
