// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('BoQ Item', {
	refresh: function(frm, cdt, cdn) {
		// Set item code filter to construction items only
		frm.set_query('item_code', 'boq_items', function() {
			return {
				filters: {
					'is_construction_item': 1,
					'disabled': 0
				}
			};
		});
	},
	
	item_code: function(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.item_code) {
			// Get item details
			melon.db.get_doc('Item', row.item_code)
				.then(item => {
					melon.model.set_value(cdt, cdn, {
						'item_name': item.item_name,
						'description': item.description,
						'uom': item.stock_uom,
						'rate': item.standard_rate || 0
					});
					
					// Calculate amount
					calculate_amount(frm, cdt, cdn);
				});
		}
	},
	
	quantity: function(frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
	}
});

function calculate_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.quantity && row.rate) {
		const amount = flt(row.quantity) * flt(row.rate);
		melon.model.set_value(cdt, cdn, 'amount', amount);
	}
}
