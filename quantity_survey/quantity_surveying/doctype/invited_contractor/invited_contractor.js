// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Invited Contractor', {
	refresh: function(frm) {
		// Add custom buttons for contractor management
		if (frm.doc.status === 'Invited') {
			frm.add_custom_button(__('Send Invitation'), function() {
				send_invitation(frm);
			}, __('Actions'));
		}
		
		if (frm.doc.status === 'Responded') {
			frm.add_custom_button(__('View Quotation'), function() {
				melon.set_route('Form', 'Tender Quote', {
					'tender_package': frm.doc.tender_package,
					'contractor': frm.doc.contractor
				});
			}, __('Actions'));
		}
		
		// Set query filters
		set_queries(frm);
	},
	
	contractor: function(frm) {
		if (frm.doc.contractor) {
			// Get contractor details
			melon.db.get_doc('Supplier', frm.doc.contractor)
				.then(supplier => {
					frm.set_value('contractor_name', supplier.supplier_name);
					frm.set_value('contact_email', supplier.email_id);
					frm.set_value('contact_phone', supplier.mobile_no);
				});
		}
	},
	
	tender_package: function(frm) {
		if (frm.doc.tender_package) {
			// Auto-populate project
			melon.db.get_value('Tender Package', frm.doc.tender_package, 'project')
				.then(r => {
					if (r.message && r.message.project) {
						frm.set_value('project', r.message.project);
					}
				});
		}
	}
});

function set_queries(frm) {
	// Contractor query - only suppliers with contractor flag
	frm.set_query('contractor', function() {
		return {
			filters: {
				'is_contractor': 1,
				'disabled': 0
			}
		};
	});
	
	// Tender Package query
	frm.set_query('tender_package', function() {
		return {
			filters: {
				'status': ['in', ['Draft', 'Open']]
			}
		};
	});
}

function send_invitation(frm) {
	melon.prompt([
		{
			label: 'Subject',
			fieldname: 'subject',
			fieldtype: 'Data',
			default: 'Tender Invitation - ' + frm.doc.tender_package,
			reqd: 1
		},
		{
			label: 'Message',
			fieldname: 'message',
			fieldtype: 'Text Editor',
			reqd: 1
		}
	], function(data) {
		melon.call({
			method: 'quantity_survey.quantity_surveying.doctype.invited_contractor.invited_contractor.send_invitation_email',
			args: {
				'invited_contractor': frm.doc.name,
				'subject': data.subject,
				'message': data.message
			},
			callback: function(r) {
				if (r.message) {
					melon.msgprint(__('Invitation sent successfully'));
					frm.set_value('invitation_sent_date', melon.datetime.now_date());
					frm.save();
				}
			}
		});
	}, __('Send Invitation'));
}
