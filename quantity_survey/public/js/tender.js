// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Tender', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === 'Open') {
			frm.add_custom_button(__('Evaluate Tenders'), function() {
				melon.set_route('Report', 'Tender Evaluation Report', {
					tender: frm.doc.name
				});
			});
		}
	}
});

melon.ui.form.on('Tender Quote', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Award Contract'), function() {
				melon.confirm(
					__('Award this contract to {0}?', [frm.doc.supplier]),
					function() {
						melon.call({
							method: 'quantity_survey.quantity_surveying.doctype.tender_quote.tender_quote.award_contract',
							args: {
								tender_quote: frm.doc.name
							},
							callback: function(r) {
								if (r.message) {
									melon.msgprint(__('Contract awarded successfully'));
									frm.reload_doc();
								}
							}
						});
					}
				);
			});
		}
	}
});
