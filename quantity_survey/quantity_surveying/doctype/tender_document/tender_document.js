// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Tender Document', {
	refresh: function(frm) {
		// Add custom buttons for document management
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Download'), function() {
				if (frm.doc.document_file) {
					window.open(frm.doc.document_file);
				} else {
					melon.msgprint(__('No document file attached'));
				}
			}, __('Actions'));
			
			frm.add_custom_button(__('Email to Contractors'), function() {
				send_to_contractors(frm);
			}, __('Actions'));
		}
		
		// Set query filters
		set_queries(frm);
	},
	
	tender_package: function(frm) {
		if (frm.doc.tender_package) {
			// Auto-populate from tender package
			melon.db.get_doc('Tender Package', frm.doc.tender_package)
				.then(package_doc => {
					frm.set_value('project', package_doc.project);
				});
		}
	},
	
	validate: function(frm) {
		validate_document(frm);
	}
});

function set_queries(frm) {
	// Tender Package query
	frm.set_query('tender_package', function() {
		return {
			filters: {
				'status': ['in', ['Draft', 'Open']]
			}
		};
	});
}

function validate_document(frm) {
	if (!frm.doc.document_file && !frm.doc.document_url) {
		melon.msgprint(__('Either document file or document URL is required'));
		melon.validated = false;
	}
}

function send_to_contractors(frm) {
	melon.prompt([
		{
			label: 'Subject',
			fieldname: 'subject',
			fieldtype: 'Data',
			default: 'Tender Document - ' + frm.doc.document_title,
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
			method: 'quantity_survey.quantity_surveying.doctype.tender_document.tender_document.send_to_contractors',
			args: {
				'tender_document': frm.doc.name,
				'subject': data.subject,
				'message': data.message
			},
			callback: function(r) {
				if (r.message) {
					melon.msgprint(__('Email sent to contractors'));
				}
			}
		});
	}, __('Send Email'));
}
