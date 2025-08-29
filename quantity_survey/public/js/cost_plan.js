// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Cost Plan', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Compare with Actual'), function() {
				melon.set_route('query-report', 'Cost vs Actual', {
					cost_plan: frm.doc.name
				});
			});
		}
	}
});

melon.ui.form.on('Cost Plan Item', {
	quantity: function(frm, cdt, cdn) {
		calculate_cost_amount(frm, cdt, cdn);
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_cost_amount(frm, cdt, cdn);
	}
});

function calculate_cost_amount(frm, cdt, cdn) {
	let item = locals[cdt][cdn];
	let amount = (item.quantity || 0) * (item.rate || 0);
	melon.model.set_value(cdt, cdn, 'amount', amount);
}
