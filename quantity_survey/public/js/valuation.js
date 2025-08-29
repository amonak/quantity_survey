// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Valuation', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Create Payment Certificate'), function() {
				melon.new_doc('Payment Certificate', {
					valuation_reference: frm.doc.name,
					project: frm.doc.project
				});
			});
		}
	},
	
	boq: function(frm) {
		if (frm.doc.boq) {
			melon.call({
				method: 'quantity_survey.quantity_surveying.doctype.valuation.valuation.get_boq_items',
				args: {
					boq: frm.doc.boq
				},
				callback: function(r) {
					if (r.message) {
						frm.clear_table('valuation_items');
						r.message.forEach(function(item) {
							let row = frm.add_child('valuation_items');
							row.item_code = item.item_code;
							row.description = item.description;
							row.quantity = item.quantity;
							row.rate = item.rate;
							row.amount = item.amount;
						});
						frm.refresh_field('valuation_items');
					}
				}
			});
		}
	}
});

melon.ui.form.on('Valuation Item', {
	completed_quantity: function(frm, cdt, cdn) {
		calculate_valuation_amount(frm, cdt, cdn);
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_valuation_amount(frm, cdt, cdn);
	}
});

function calculate_valuation_amount(frm, cdt, cdn) {
	let item = locals[cdt][cdn];
	let amount = (item.completed_quantity || 0) * (item.rate || 0);
	melon.model.set_value(cdt, cdn, 'amount', amount);
}
