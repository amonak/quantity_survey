// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Valuation Item', {
	refresh: function(frm, cdt, cdn) {
		// Add custom styling for valuation items
		if (frm.is_new()) {
			frm.get_field('valuation_items').grid.cannot_add_rows = false;
		}
	},
	
	item_code: function(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.item_code) {
			// Get item details and BoQ quantity
			get_boq_item_details(frm, cdt, cdn);
		}
	},
	
	current_quantity: function(frm, cdt, cdn) {
		calculate_current_amount(frm, cdt, cdn);
		calculate_cumulative_quantity(frm, cdt, cdn);
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_current_amount(frm, cdt, cdn);
		calculate_cumulative_amount(frm, cdt, cdn);
	}
});

function get_boq_item_details(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	
	if (frm.doc.boq && row.item_code) {
		melon.call({
			method: 'quantity_survey.quantity_surveying.doctype.valuation.valuation.get_boq_item_details',
			args: {
				'boq': frm.doc.boq,
				'item_code': row.item_code
			},
			callback: function(r) {
				if (r.message) {
					melon.model.set_value(cdt, cdn, {
						'item_name': r.message.item_name,
						'description': r.message.description,
						'uom': r.message.uom,
						'boq_quantity': r.message.quantity,
						'rate': r.message.rate
					});
				}
			}
		});
	}
}

function calculate_current_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.current_quantity && row.rate) {
		const amount = flt(row.current_quantity) * flt(row.rate);
		melon.model.set_value(cdt, cdn, 'current_amount', amount);
	}
}

function calculate_cumulative_quantity(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.previous_quantity && row.current_quantity) {
		const cumulative = flt(row.previous_quantity) + flt(row.current_quantity);
		melon.model.set_value(cdt, cdn, 'cumulative_quantity', cumulative);
	}
}

function calculate_cumulative_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.cumulative_quantity && row.rate) {
		const amount = flt(row.cumulative_quantity) * flt(row.rate);
		melon.model.set_value(cdt, cdn, 'cumulative_amount', amount);
	}
}
