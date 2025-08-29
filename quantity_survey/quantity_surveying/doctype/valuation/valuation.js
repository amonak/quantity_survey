// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Valuation', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Create Payment Certificate'), function() {
				melon.new_doc('Payment Certificate', {
					'valuation': frm.doc.name,
					'project': frm.doc.project
				});
			});
		}
		
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Get BoQ Items'), function() {
				get_boq_items(frm);
			});
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
	
	retention_percentage: function(frm) {
		calculate_retention(frm);
	},
	
	validate: function(frm) {
		calculate_totals(frm);
		calculate_retention(frm);
	}
});

melon.ui.form.on('Valuation Item', {
	current_quantity: function(frm, cdt, cdn) {
		calculate_item_amounts(frm, cdt, cdn);
		calculate_totals(frm);
		calculate_retention(frm);
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_item_amounts(frm, cdt, cdn);
		calculate_totals(frm);
		calculate_retention(frm);
	},
	
	valuation_items_remove: function(frm) {
		calculate_totals(frm);
		calculate_retention(frm);
	}
});

function calculate_item_amounts(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	
	if (row.current_quantity && row.rate) {
		melon.model.set_value(cdt, cdn, 'current_amount', flt(row.current_quantity) * flt(row.rate));
	}
	
	if (row.cumulative_quantity && row.rate) {
		melon.model.set_value(cdt, cdn, 'cumulative_amount', flt(row.cumulative_quantity) * flt(row.rate));
	}
}

function calculate_totals(frm) {
	let total_work_done = 0;
	let current_valuation = 0;
	
	frm.doc.valuation_items.forEach(function(item) {
		if (item.current_amount) {
			current_valuation += flt(item.current_amount);
		}
		if (item.cumulative_amount) {
			total_work_done += flt(item.cumulative_amount);
		}
	});
	
	frm.set_value('total_work_done', total_work_done);
	frm.set_value('current_valuation', current_valuation);
	frm.set_value('cumulative_total', total_work_done);
}

function calculate_retention(frm) {
	if (frm.doc.retention_percentage && frm.doc.current_valuation) {
		const retention_amount = flt(frm.doc.current_valuation) * flt(frm.doc.retention_percentage) / 100;
		frm.set_value('retention_amount', retention_amount);
		frm.set_value('net_payable', flt(frm.doc.current_valuation) - retention_amount);
	} else {
		frm.set_value('retention_amount', 0);
		frm.set_value('net_payable', flt(frm.doc.current_valuation));
	}
}

function get_boq_items(frm) {
	if (!frm.doc.boq) {
		melon.msgprint(__('Please select a BoQ first'));
		return;
	}
	
	melon.call({
		method: 'quantity_survey.quantity_surveying.doctype.valuation.valuation.get_boq_items_for_valuation',
		args: {
			boq: frm.doc.boq
		},
		callback: function(r) {
			if (r.message) {
				frm.clear_table('valuation_items');
				
				// Get previous valuation data
				melon.call({
					method: 'quantity_survey.quantity_surveying.doctype.valuation.valuation.get_previous_valuation_data',
					args: {
						boq: frm.doc.boq,
						current_valuation: frm.doc.name
					},
					callback: function(prev_r) {
						const previous_data = prev_r.message || {};
						
						r.message.forEach(function(item) {
							const child = frm.add_child('valuation_items');
							child.item_code = item.item_code;
							child.item_name = item.item_name;
							child.description = item.description;
							child.uom = item.uom;
							child.boq_quantity = item.boq_quantity;
							child.rate = item.rate;
							child.boq_amount = item.boq_amount;
							
							// Set previous data if available
							if (previous_data[item.item_code]) {
								child.previous_quantity = previous_data[item.item_code].previous_cumulative_quantity;
								child.previous_amount = previous_data[item.item_code].previous_cumulative_amount;
							}
						});
						
						frm.refresh_field('valuation_items');
					}
				});
			}
		}
	});
}
