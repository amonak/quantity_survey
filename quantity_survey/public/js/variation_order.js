// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Variation Order', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Update BoQ'), function() {
				melon.confirm(
					__('This will update the original BoQ with variation items. Continue?'),
					function() {
						melon.call({
							method: 'quantity_survey.quantity_surveying.doctype.variation_order.variation_order.update_boq',
							args: {
								variation_order: frm.doc.name
							},
							callback: function(r) {
								if (r.message) {
									melon.msgprint(__('BoQ updated successfully'));
								}
							}
						});
					}
				);
			});
		}
	}
});

melon.ui.form.on('Variation Order Item', {
	quantity: function(frm, cdt, cdn) {
		calculate_variation_amount(frm, cdt, cdn);
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_variation_amount(frm, cdt, cdn);
	}
});

function calculate_variation_amount(frm, cdt, cdn) {
	let item = locals[cdt][cdn];
	let amount = (item.quantity || 0) * (item.rate || 0);
	melon.model.set_value(cdt, cdn, 'amount', amount);
}
