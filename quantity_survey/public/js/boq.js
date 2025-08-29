// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('BoQ', {
	refresh: function(frm) {
		// Custom refresh logic for BoQ
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Create Valuation'), function() {
				melon.new_doc('Valuation', {
					boq: frm.doc.name,
					project: frm.doc.project
				});
			});
		}
	},
	
	project: function(frm) {
		// Auto-set project name when project is selected
		if (frm.doc.project) {
			melon.db.get_value('Project', frm.doc.project, 'project_name')
				.then(r => {
					if (r.message) {
						frm.set_value('project_name', r.message.project_name);
					}
				});
		}
	},
	
	validate: function(frm) {
		// Calculate totals before saving
		frm.trigger('calculate_totals');
	},
	
	calculate_totals: function(frm) {
		let total_quantity = 0;
		let total_amount = 0;
		
		frm.doc.boq_items.forEach(function(item) {
			total_quantity += item.quantity || 0;
			total_amount += item.amount || 0;
		});
		
		frm.set_value('total_quantity', total_quantity);
		frm.set_value('total_amount', total_amount);
	}
});

melon.ui.form.on('BoQ Item', {
	quantity: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
	}
});

function calculate_item_amount(frm, cdt, cdn) {
	let item = locals[cdt][cdn];
	let amount = (item.quantity || 0) * (item.rate || 0);
	melon.model.set_value(cdt, cdn, 'amount', amount);
	frm.trigger('calculate_totals');
}
