# Copyright (c) 2025, Alphamonak Solutions


import melon
from melon import _
from melon.model.document import Document
from melon.utils import getdate, flt


class TenderPackage(Document):
	def validate(self):
		"""Validate Tender Package"""
		self.validate_dates()
		self.calculate_bid_security_amount()
		self.calculate_savings_percentage()
	
	def on_submit(self):
		"""Actions on submit"""
		self.status = "Published"
		self.send_tender_notifications()
	
	def validate_dates(self):
		"""Validate tender dates sequence."""
		if self.tender_publication_date and self.bid_submission_deadline:
			if getdate(self.tender_publication_date) >= getdate(self.bid_submission_deadline):
				melon.throw(_("Bid submission deadline must be after tender publication date"))
		
		if self.bid_submission_deadline and self.bid_opening_date:
			if getdate(self.bid_submission_deadline) >= getdate(self.bid_opening_date):
				melon.throw(_("Bid opening date must be after bid submission deadline"))
	
	def calculate_bid_security_amount(self):
		"""Calculate bid security amount based on percentage"""
		if self.estimated_value and self.bid_security_percentage:
			self.bid_security_amount = flt(self.estimated_value * self.bid_security_percentage / 100, 2)
	
	def calculate_savings_percentage(self):
		"""Calculate savings percentage compared to estimated value"""
		if self.estimated_value and self.winning_quote_amount:
			savings = (self.estimated_value - self.winning_quote_amount) / self.estimated_value * 100
			self.savings_percentage = flt(savings, 2)
	
	def send_tender_notifications(self):
		"""Send notifications to invited contractors"""
		if self.invited_contractors:
			for contractor in self.invited_contractors:
				self.send_invitation_email(contractor.supplier)
	
	def send_invitation_email(self, supplier):
		"""Send tender invitation email to supplier"""
		try:
			supplier_doc = melon.get_doc("Supplier", supplier)
			if supplier_doc.email_id:
				subject = f"Tender Invitation: {self.tender_package_title}"
				message = f"""
				Dear {supplier_doc.supplier_name},
				
				You are invited to participate in the tender for: {self.tender_package_title}
				
				Project: {self.project}
				Estimated Value: {melon.format(self.estimated_value, {'fieldtype': 'Currency'})}
				Bid Submission Deadline: {self.bid_submission_deadline}
				
				Please contact us for tender documents and further details.
				
				Best regards,
				Tender Committee
				"""
				
				melon.sendmail(
					recipients=[supplier_doc.email_id],
					subject=subject,
					message=message,
					reference_doctype=self.doctype,
					reference_name=self.name
				)
		except Exception as e:
			melon.log_error(f"Failed to send tender invitation to {supplier}: {str(e)}")
	
	def update_quote_summary(self):
		"""Update tender quotes summary"""
		quotes = melon.get_all("Tender Quote", 
			filters={"tender_package": self.name, "docstatus": 1},
			fields=["name", "total_quote_amount", "supplier"]
		)
		
		self.total_quotes_received = len(quotes)
		
		if quotes:
			quote_amounts = [q.total_quote_amount for q in quotes]
			self.lowest_quote_amount = min(quote_amounts)
			
			# Find winning quote (lowest amount)
			lowest_quote = min(quotes, key=lambda x: x.total_quote_amount)
			self.winning_contractor = lowest_quote.supplier
			self.winning_quote_amount = lowest_quote.total_quote_amount
		
		self.calculate_savings_percentage()
		self.save()
	
	@melon.whitelist()
	def award_tender(self):
		"""Award tender to winning contractor."""
		if not self.winning_contractor:
			melon.throw(_("Please select winning contractor first"))
		
		self.status = "Awarded"
		self.contract_award_date = melon.utils.today()
		
		# Create Purchase Order if integration required
		self.create_purchase_order()
		
		self.save()
		melon.msgprint(_("Tender awarded to {0}").format(self.winning_contractor))
	
	def create_purchase_order(self):
		"""Create Purchase Order for awarded tender"""
		try:
			po = melon.new_doc("Purchase Order")
			po.supplier = self.winning_contractor
			po.project = self.project
			po.title = f"PO for {self.tender_package_title}"
			
			# Add items from winning quote
			winning_quote = melon.get_doc("Tender Quote", 
				{"tender_package": self.name, "supplier": self.winning_contractor})
			
			for item in winning_quote.quote_items:
				po.append("items", {
					"item_code": item.item_code,
					"item_name": item.item_name,
					"description": item.description,
					"qty": item.quantity,
					"rate": item.unit_rate,
					"amount": item.amount,
					"uom": item.uom
				})
			
			po.insert()
			melon.msgprint(f"Purchase Order {po.name} created successfully")
			
		except Exception as e:
			melon.log_error(f"Failed to create Purchase Order: {str(e)}")
			melon.msgprint("Purchase Order creation failed. Please create manually.")
	
	@melon.whitelist()
	def generate_tender_comparison(self):
		"""Generate tender comparison report."""
		quotes = melon.get_all("Tender Quote", 
			filters={"tender_package": self.name, "docstatus": 1},
			fields=["name", "supplier", "total_quote_amount", "quote_validity", "delivery_period"]
		)
		
		if not quotes:
			melon.throw(_("No submitted quotes found for comparison"))
		
		# Sort by quote amount
		quotes.sort(key=lambda x: x.total_quote_amount)
		
		return quotes
