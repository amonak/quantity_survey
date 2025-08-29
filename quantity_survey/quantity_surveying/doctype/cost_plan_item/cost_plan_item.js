// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Cost Plan Item', {
	refresh: function(frm) {
		// Set focus on item_code field for new records
		if (frm.is_new()) {
			melon.run_serially([
				() => frm.fields_dict.item_code.set_focus()
			]);
		}
	},
	
	item_code: function(frm, cdt, cdn) {
		// Auto-fetch item details when item is selected
		if (frm.doc.item_code) {
			melon.db.get_doc('Item', frm.doc.item_code).then(item => {
				frm.set_value('item_name', item.item_name);
				frm.set_value('uom', item.stock_uom);
				frm.refresh();
			});
		}
	},
	
	estimated_quantity: function(frm) {
		calculate_estimated_cost(frm);
	},
	
	unit_rate: function(frm) {
		calculate_estimated_cost(frm);
		calculate_variance_percentage(frm);
	},
	
	market_rate: function(frm) {
		calculate_variance_percentage(frm);
	},
	
	risk_factor: function(frm) {
		// Auto-set risk percentage based on risk factor
		if (frm.doc.risk_factor) {
			let risk_percentages = {
				'Low': 2,
				'Medium': 5,
				'High': 10,
				'Critical': 20
			};
			frm.set_value('risk_percentage', risk_percentages[frm.doc.risk_factor]);
		}
	}
});

function calculate_estimated_cost(frm) {
	if (frm.doc.estimated_quantity && frm.doc.unit_rate) {
		let estimated_cost = frm.doc.estimated_quantity * frm.doc.unit_rate;
		frm.set_value('estimated_cost', estimated_cost);
	}
}

function calculate_variance_percentage(frm) {
	if (frm.doc.unit_rate && frm.doc.market_rate) {
		let variance = (frm.doc.unit_rate - frm.doc.market_rate) / frm.doc.market_rate * 100;
		frm.set_value('variance_percentage', variance);
	}
}
