// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Payment Certificate', {
	onload: function(frm) {
		// Set default certificate date
		if (!frm.doc.certificate_date) {
			frm.set_value('certificate_date', melon.datetime.get_today());
		}
		
		// Set filters for project
		frm.set_query('project', function() {
			return {
				filters: {
					'status': ['not in', ['Completed', 'Cancelled']],
					'is_active': 'Yes'
				}
			};
		});
		
		// Set filters for valuation reference
		frm.set_query('valuation_reference', function() {
			return {
				filters: {
					'docstatus': 1,
					'project': frm.doc.project || ''
				}
			};
		});
	},
	
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.docstatus === 1) {
			// Add Print button with custom format
			frm.add_custom_button(__('Print Certificate'), function() {
				melon.ui.get_print_format('Payment Certificate', frm.doc.name, 'Payment Certificate');
			}, __('Print'));
			
			// Add Email button
			frm.add_custom_button(__('Email Certificate'), function() {
				melon.ui.form.email_document(frm, 'Payment Certificate', frm.doc.name);
			}, __('Email'));
			
			// Add Create Payment Entry button
			frm.add_custom_button(__('Create Payment Entry'), function() {
				frm.trigger('create_payment_entry');
			}, __('Create'));
			
			// Add View Project button
			if (frm.doc.project) {
				frm.add_custom_button(__('View Project'), function() {
					melon.set_route('Form', 'Project', frm.doc.project);
				}, __('View'));
			}
		}
		
		// Set form indicator based on status
		if (frm.doc.docstatus === 1) {
			if (frm.doc.payment_status === 'Paid') {
				frm.dashboard.add_indicator(__('Paid'), 'green');
			} else if (frm.doc.payment_status === 'Partially Paid') {
				frm.dashboard.add_indicator(__('Partially Paid'), 'orange');
			} else {
				frm.dashboard.add_indicator(__('Pending Payment'), 'red');
			}
		}
		
		// Add payment due date warning
		if (frm.doc.payment_due_date && frm.doc.docstatus === 1 && frm.doc.payment_status !== 'Paid') {
			let due_date = melon.datetime.get_diff(frm.doc.payment_due_date, melon.datetime.get_today());
			if (due_date < 0) {
				frm.dashboard.add_indicator(__('Payment Overdue'), 'red');
			} else if (due_date <= 7) {
				frm.dashboard.add_indicator(__('Payment Due Soon'), 'orange');
			}
		}
	},
	
	project: function(frm) {
		if (frm.doc.project) {
			// Get project details and set defaults
			melon.call({
				method: 'quantity_survey.quantity_surveying.doctype.payment_certificate.payment_certificate.get_project_retention_rate',
				args: {
					project: frm.doc.project
				},
				callback: function(r) {
					if (r.message && !frm.doc.retention_percentage) {
						frm.set_value('retention_percentage', r.message);
					}
				}
			});
			
			// Get previous payments
			melon.call({
				method: 'quantity_survey.quantity_surveying.doctype.payment_certificate.payment_certificate.get_previous_payments',
				args: {
					project: frm.doc.project
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value('previous_payments', r.message);
						frm.trigger('calculate_net_amount');
					}
				}
			});
		}
	},
	
	valuation_reference: function(frm) {
		if (frm.doc.valuation_reference) {
			// Get valuation details
			melon.call({
				method: 'quantity_survey.quantity_surveying.doctype.payment_certificate.payment_certificate.get_valuation_details',
				args: {
					valuation: frm.doc.valuation_reference
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value('project', r.message.project);
						frm.set_value('gross_amount', r.message.gross_amount);
						frm.set_value('valuation_date', r.message.valuation_date);
						frm.set_value('valuation_period', r.message.valuation_period);
						frm.trigger('calculate_net_amount');
					}
				}
			});
		}
	},
	
	certificate_date: function(frm) {
		// Auto-set payment due date (30 days from certificate date)
		if (frm.doc.certificate_date && !frm.doc.payment_due_date) {
			let due_date = melon.datetime.add_days(frm.doc.certificate_date, 30);
			frm.set_value('payment_due_date', due_date);
		}
	},
	
	gross_amount: function(frm) {
		frm.trigger('calculate_retention');
		frm.trigger('calculate_net_amount');
	},
	
	retention_percentage: function(frm) {
		frm.trigger('calculate_retention');
		frm.trigger('calculate_net_amount');
	},
	
	retention_amount: function(frm) {
		frm.trigger('calculate_net_amount');
	},
	
	advance_recovery: function(frm) {
		frm.trigger('calculate_net_amount');
	},
	
	other_deductions: function(frm) {
		frm.trigger('calculate_net_amount');
	},
	
	previous_payments: function(frm) {
		frm.trigger('calculate_net_amount');
	},
	
	calculate_retention: function(frm) {
		// Calculate retention amount
		if (frm.doc.gross_amount && frm.doc.retention_percentage) {
			let retention_amount = (frm.doc.gross_amount * frm.doc.retention_percentage) / 100;
			frm.set_value('retention_amount', retention_amount);
		}
	},
	
	calculate_net_amount: function(frm) {
		// Calculate net payment amount
		let gross_amount = frm.doc.gross_amount || 0;
		let retention_amount = frm.doc.retention_amount || 0;
		let advance_recovery = frm.doc.advance_recovery || 0;
		let other_deductions = frm.doc.other_deductions || 0;
		let previous_payments = frm.doc.previous_payments || 0;
		
		let net_amount = gross_amount - retention_amount - advance_recovery - other_deductions;
		
		frm.set_value('net_payment_amount', net_amount);
		
		// Calculate cumulative amounts
		let cumulative_gross = previous_payments + gross_amount;
		frm.set_value('cumulative_gross_amount', cumulative_gross);
	},
	
	create_payment_entry: function(frm) {
		// Create Payment Entry from Payment Certificate
		if (frm.doc.docstatus !== 1) {
			melon.msgprint(__('Please submit the Payment Certificate first'));
			return;
		}
		
		melon.call({
			method: 'quantity_survey.quantity_surveying.doctype.payment_certificate.payment_certificate.create_payment_entry',
			args: {
				payment_certificate: frm.doc.name
			},
			callback: function(r) {
				if (r.message) {
					// Open new Payment Entry form with pre-filled data
					melon.model.with_doctype('Payment Entry', function() {
						let payment_entry = melon.model.get_new_doc('Payment Entry');
						$.extend(payment_entry, r.message);
						melon.set_route('Form', 'Payment Entry', payment_entry.name);
					});
				}
			}
		});
	},
	
	validate: function(frm) {
		// Custom validation
		if (frm.doc.payment_due_date && frm.doc.certificate_date) {
			if (melon.datetime.get_diff(frm.doc.payment_due_date, frm.doc.certificate_date) < 0) {
				melon.msgprint(__('Payment Due Date cannot be before Certificate Date'));
				melon.validated = false;
			}
		}
		
		if (frm.doc.net_payment_amount < 0) {
			melon.msgprint(__('Net Payment Amount cannot be negative'));
			melon.validated = false;
		}
		
		if (frm.doc.retention_percentage && (frm.doc.retention_percentage < 0 || frm.doc.retention_percentage > 50)) {
			melon.msgprint(__('Retention Percentage should be between 0 and 50'));
			melon.validated = false;
		}
	}
});

// Auto-refresh form when certain fields change
melon.ui.form.on('Payment Certificate', {
	setup: function(frm) {
		// Add custom CSS for better visual appearance
		frm.$wrapper.find('.layout-main-section').first().prepend(
			'<div class="payment-certificate-header" style="background: #f8f9fa; padding: 15px; margin: 0 -15px 20px -15px; border-left: 4px solid #007bff;">' +
			'<h4 style="margin: 0; color: #007bff;"><i class="fa fa-file-text"></i> Payment Certificate</h4>' +
			'<p style="margin: 5px 0 0 0; color: #6c757d;">Certify completed work and authorize payments</p>' +
			'</div>'
		);
		
		// Format currency fields
		frm.refresh_field('gross_amount');
		frm.refresh_field('retention_amount');
		frm.refresh_field('net_payment_amount');
		frm.refresh_field('cumulative_gross_amount');
	}
});

// Utility functions
melon.ui.form.PaymentCertificateUtils = {
	show_payment_summary: function(frm) {
		// Show payment summary dialog
		let d = new melon.ui.Dialog({
			title: __('Payment Summary'),
			fields: [
				{
					fieldtype: 'Currency',
					fieldname: 'gross_amount',
					label: __('Gross Amount'),
					read_only: 1,
					default: frm.doc.gross_amount
				},
				{
					fieldtype: 'Currency',
					fieldname: 'retention_amount',
					label: __('Retention Amount'),
					read_only: 1,
					default: frm.doc.retention_amount
				},
				{
					fieldtype: 'Currency',
					fieldname: 'advance_recovery',
					label: __('Advance Recovery'),
					read_only: 1,
					default: frm.doc.advance_recovery
				},
				{
					fieldtype: 'Currency',
					fieldname: 'other_deductions',
					label: __('Other Deductions'),
					read_only: 1,
					default: frm.doc.other_deductions
				},
				{
					fieldtype: 'Currency',
					fieldname: 'net_payment_amount',
					label: __('Net Payment Amount'),
					read_only: 1,
					default: frm.doc.net_payment_amount
				}
			]
		});
		
		d.show();
	},
	
	format_currency: function(amount) {
		return format_currency(amount, melon.defaults.get_default('currency'));
	}
};
