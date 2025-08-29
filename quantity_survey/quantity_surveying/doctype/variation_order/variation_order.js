// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Variation Order', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.approval_status === "Pending") {
			frm.add_custom_button(__('Approve'), function() {
				approve_variation_order(frm);
			}, __('Actions'));
			
			frm.add_custom_button(__('Reject'), function() {
				reject_variation_order(frm);
			}, __('Actions'));
		}
		
		frm.set_query('boq', function() {
			return {
				filters: {
					'docstatus': 1
				}
			};
		});
	},
	
	boq: function(frm) {
		if (frm.doc.boq) {
			melon.db.get_value('BoQ', frm.doc.boq, 'project')
				.then(r => {
					if (r.message) {
						frm.set_value('project', r.message.project);
					}
				});
		}
	},
	
	variation_type: function(frm) {
		calculate_totals(frm);
	},
	
	validate: function(frm) {
		calculate_totals(frm);
	}
});

melon.ui.form.on('Variation Order Item', {
	quantity: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
		calculate_totals(frm);
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
		calculate_totals(frm);
	},
	
	variation_items_remove: function(frm) {
		calculate_totals(frm);
	}
});

function calculate_item_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.quantity && row.rate) {
		let amount = flt(row.quantity) * flt(row.rate);
		
		// Handle variation type
		if (frm.doc.variation_type === "Omission") {
			amount = -Math.abs(amount);
		} else if (frm.doc.variation_type === "Addition") {
			amount = Math.abs(amount);
		}
		
		melon.model.set_value(cdt, cdn, 'amount', amount);
	}
}

function calculate_totals(frm) {
	let total_amount = 0;
	
	frm.doc.variation_items.forEach(function(item) {
		if (item.amount) {
			total_amount += flt(item.amount);
		}
	});
	
	frm.set_value('total_variation_amount', total_amount);
}

function approve_variation_order(frm) {
	melon.call({
		method: 'quantity_survey.quantity_surveying.doctype.variation_order.variation_order.approve_variation_order',
		args: {
			variation_order: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				frm.reload_doc();
				melon.show_alert({
					message: __('Variation Order Approved'),
					indicator: 'green'
				});
			}
		}
	});
}

function reject_variation_order(frm) {
	melon.prompt([
		{
			label: 'Reason for Rejection',
			fieldname: 'reason',
			fieldtype: 'Text',
			reqd: 1
		}
	], function(data) {
		melon.call({
			method: 'quantity_survey.quantity_surveying.doctype.variation_order.variation_order.reject_variation_order',
			args: {
				variation_order: frm.doc.name,
				reason: data.reason
			},
			callback: function(r) {
				if (r.message) {
					frm.reload_doc();
					melon.show_alert({
						message: __('Variation Order Rejected'),
						indicator: 'red'
					});
				}
			}
		});
	}, __('Reject Variation Order'));
}
