// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Tender Quote Item', {
	refresh: function(frm, cdt, cdn) {
		// Set queries for item selection
		frm.set_query('item_code', 'tender_quote_items', function() {
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
			// Get item details from BoQ
			get_boq_item_details(frm, cdt, cdn);
		}
	},
	
	quantity: function(frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
	},
	
	discount_percentage: function(frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
	}
});

function get_boq_item_details(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	
	if (frm.doc.boq_reference && row.item_code) {
		melon.call({
			method: 'quantity_survey.quantity_surveying.doctype.tender_quote.tender_quote.get_boq_item_details',
			args: {
				'boq': frm.doc.boq_reference,
				'item_code': row.item_code
			},
			callback: function(r) {
				if (r.message) {
					melon.model.set_value(cdt, cdn, {
						'item_name': r.message.item_name,
						'description': r.message.description,
						'uom': r.message.uom,
						'boq_quantity': r.message.quantity,
						'boq_rate': r.message.rate
					});
				}
			}
		});
	}
}

function calculate_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.quantity && row.rate) {
		let amount = flt(row.quantity) * flt(row.rate);
		
		// Apply discount if specified
		if (row.discount_percentage) {
			const discount_amount = amount * flt(row.discount_percentage) / 100;
			amount = amount - discount_amount;
			melon.model.set_value(cdt, cdn, 'discount_amount', discount_amount);
		}
		
		melon.model.set_value(cdt, cdn, 'amount', amount);
	}
}
