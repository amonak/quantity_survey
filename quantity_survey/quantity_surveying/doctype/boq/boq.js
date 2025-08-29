// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('BoQ', {
	refresh: function(frm) {
		// Set custom indicators
		if (frm.doc.docstatus === 1) {
			frm.set_indicator(__('Submitted'), 'blue');
		}
		
		// Add custom buttons for submitted documents
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Create Valuation'), function() {
				melon.new_doc('Valuation', {
					'boq': frm.doc.name,
					'project': frm.doc.project
				});
			}, __('Create'));
			
			frm.add_custom_button(__('Create Variation Order'), function() {
				melon.new_doc('Variation Order', {
					'boq': frm.doc.name,
					'project': frm.doc.project
				});
			}, __('Create'));
			
			frm.add_custom_button(__('Duplicate BoQ'), function() {
				melon.call({
					method: 'quantity_survey.quantity_surveying.doctype.boq.boq.duplicate_boq',
					args: {
						'source_name': frm.doc.name
					},
					callback: function(r) {
						if (r.message) {
							melon.set_route('Form', 'BoQ', r.message.name);
						}
					}
				});
			}, __('Actions'));
		}
		
		// Add template button for draft documents
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Get Items from Template'), function() {
				get_items_from_template(frm);
			}, __('Tools'));
			
			frm.add_custom_button(__('Import from Excel'), function() {
				melon.prompt([
					{
						label: 'Excel File',
						fieldname: 'excel_file',
						fieldtype: 'Attach',
						reqd: 1
					}
				], function(data) {
					import_from_excel(frm, data.excel_file);
				}, __('Import BoQ Items from Excel'));
			}, __('Tools'));
		}
		
		// Set query filters
		set_queries(frm);
	},
	
	project: function(frm) {
		if (frm.doc.project) {
			// Set project name and get project details
			melon.db.get_doc('Project', frm.doc.project)
				.then(project => {
					frm.set_value('project_name', project.project_name);
					if (project.company) {
						frm.set_value('company', project.company);
					}
				});
		}
	},
	
	validate: function(frm) {
		calculate_totals(frm);
		validate_items(frm);
	},
	
	before_save: function(frm) {
		// Auto-generate title if not provided
		if (!frm.doc.title && frm.doc.project) {
			frm.set_value('title', `BoQ for ${frm.doc.project}`);
		}
	}
});

melon.ui.form.on('BoQ Item', {
	quantity: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
		calculate_totals(frm);
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
		calculate_totals(frm);
	},
	
	boq_items_remove: function(frm) {
		calculate_totals(frm);
	}
});

function calculate_item_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.quantity && row.rate) {
		melon.model.set_value(cdt, cdn, 'amount', flt(row.quantity) * flt(row.rate));
	}
}

function calculate_totals(frm) {
	let total_quantity = 0;
	let total_amount = 0;
	
	frm.doc.boq_items.forEach(function(item) {
		if (item.quantity) {
			total_quantity += flt(item.quantity);
		}
		if (item.amount) {
			total_amount += flt(item.amount);
		}
	});
	
	frm.set_value('total_quantity', total_quantity);
	frm.set_value('total_amount', total_amount);
}

function set_queries(frm) {
	// Project query
	frm.set_query('project', function() {
		return {
			filters: {
				'status': ['!=', 'Completed']
			}
		};
	});
	
	// Item code query for BoQ items
	frm.set_query('item_code', 'boq_items', function() {
		return {
			filters: {
				'is_construction_item': 1,
				'disabled': 0
			}
		};
	});
}

function validate_items(frm) {
	let has_error = false;
	
	frm.doc.boq_items.forEach(function(item) {
		if (!item.item_code) {
			melon.msgprint(__('Item Code is required for all BoQ items'));
			has_error = true;
		}
		if (!item.quantity || item.quantity <= 0) {
			melon.msgprint(__('Quantity must be greater than 0 for item {0}', [item.item_code]));
			has_error = true;
		}
	});
	
	if (has_error) {
		melon.validated = false;
	}
}

function import_from_excel(frm, excel_file) {
	melon.call({
		method: 'quantity_survey.quantity_surveying.doctype.boq.boq.import_from_excel',
		args: {
			'boq': frm.doc.name,
			'excel_file': excel_file
		},
		callback: function(r) {
			if (r.message) {
				frm.reload_doc();
				melon.msgprint(__('Items imported successfully'));
			}
		}
	});
}

function get_items_from_template(frm) {
	melon.prompt([
		{
			label: 'BoQ Template',
			fieldname: 'template',
			fieldtype: 'Link',
			options: 'BoQ',
			reqd: 1,
			get_query: function() {
				return {
					filters: {
						'docstatus': 1,
						'name': ['!=', frm.doc.name]
					}
				};
			}
		}
	], function(data) {
		melon.call({
			method: 'quantity_survey.quantity_surveying.doctype.boq.boq.get_boq_items',
			args: {
				boq: data.template
			},
			callback: function(r) {
				if (r.message && r.message.length > 0) {
					frm.clear_table('boq_items');
					r.message.forEach(function(item) {
						const child = frm.add_child('boq_items');
						child.item_code = item.item_code;
						child.item_name = item.item_name;
						child.description = item.description;
						child.uom = item.uom;
						child.quantity = item.quantity;
						child.rate = item.rate;
						child.amount = item.amount;
					});
					frm.refresh_field('boq_items');
					calculate_totals(frm);
					melon.msgprint(__('Items copied from template successfully'));
				} else {
					melon.msgprint(__('No items found in selected template'));
				}
			}
		});
	}, __('Get Items from Template'));
}
