// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Final Account', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Load Project Data'), function() {
				frm.call('load_project_data');
			}, __('Actions'));
		}
		
		if (frm.doc.docstatus === 1) {
			if (frm.doc.status === "Agreed") {
				frm.add_custom_button(__('Create Final Payment'), function() {
					frm.call('create_final_payment');
				}, __('Actions'));
			}
			
			frm.add_custom_button(__('Cost Analysis'), function() {
				show_cost_analysis(frm);
			}, __('Reports'));
		}
		
		// Set indicators
		if (frm.doc.status) {
			frm.dashboard.add_indicator(__('Status: {0}', [frm.doc.status]), 
				get_status_color(frm.doc.status));
		}
		
		if (frm.doc.final_payment_amount) {
			let color = frm.doc.final_payment_amount > 0 ? 'green' : 'red';
			frm.dashboard.add_indicator(__('Final Payment: {0}', 
				[format_currency(frm.doc.final_payment_amount)]), color);
		}
	},
	
	project: function(frm) {
		if (frm.doc.project) {
			// Auto-fetch project details
			melon.db.get_doc('Project', frm.doc.project).then(project => {
				frm.set_value('original_contract_value', project.total_sales_amount || 0);
			});
		}
	},
	
	original_contract_value: function(frm) {
		calculate_adjustments(frm);
	},
	
	approved_variations_total: function(frm) {
		calculate_adjustments(frm);
	},
	
	claims_amount: function(frm) {
		calculate_adjustments(frm);
	},
	
	contra_charges: function(frm) {
		calculate_adjustments(frm);
	},
	
	work_done_to_date: function(frm) {
		calculate_payment_summary(frm);
	},
	
	materials_on_site: function(frm) {
		calculate_payment_summary(frm);
	},
	
	less_retention_percentage: function(frm) {
		calculate_final_amounts(frm);
	},
	
	vat_percentage: function(frm) {
		calculate_final_amounts(frm);
	}
});

melon.ui.form.on('Final Account Item', {
	final_quantity: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
		calculate_final_amounts(frm);
	},
	
	final_rate: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
		calculate_final_amounts(frm);
	},
	
	final_account_items_remove: function(frm) {
		calculate_final_amounts(frm);
	}
});

function calculate_item_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	if (row.final_quantity && row.final_rate) {
		row.final_amount = row.final_quantity * row.final_rate;
		refresh_field('final_amount', cdn, 'final_account_items');
	}
}

function calculate_adjustments(frm) {
	let adjusted_value = flt(frm.doc.original_contract_value, 2);
	adjusted_value += flt(frm.doc.approved_variations_total, 2);
	adjusted_value += flt(frm.doc.claims_amount, 2);
	adjusted_value -= flt(frm.doc.contra_charges, 2);
	
	frm.set_value('adjusted_contract_value', adjusted_value);
}

function calculate_payment_summary(frm) {
	let total_work_value = flt(frm.doc.work_done_to_date, 2) + flt(frm.doc.materials_on_site, 2);
	let current_due = total_work_value - flt(frm.doc.previous_payments, 2);
	frm.set_value('current_payment_due', current_due);
}

function calculate_final_amounts(frm) {
	// Calculate total from items
	let total_certified = 0;
	frm.doc.final_account_items.forEach(item => {
		if (item.final_amount) {
			total_certified += item.final_amount;
		}
	});
	
	frm.set_value('total_certified_value', total_certified);
	
	// Calculate retention
	let retention_amount = 0;
	if (frm.doc.less_retention_percentage) {
		retention_amount = total_certified * frm.doc.less_retention_percentage / 100;
	}
	frm.set_value('retention_amount', retention_amount);
	
	// Net amount
	let net_amount = total_certified - retention_amount;
	frm.set_value('net_amount_due', net_amount);
	
	// VAT calculation
	let vat_amount = 0;
	if (frm.doc.vat_percentage) {
		vat_amount = net_amount * frm.doc.vat_percentage / 100;
	}
	frm.set_value('vat_amount', vat_amount);
	
	// Gross amount
	let gross_amount = net_amount + vat_amount;
	frm.set_value('gross_amount_payable', gross_amount);
	
	// Final payment
	let final_payment = gross_amount - flt(frm.doc.previous_payments, 2);
	frm.set_value('final_payment_amount', final_payment);
}

function show_cost_analysis(frm) {
	frm.call('generate_cost_analysis').then(r => {
		if (r.message) {
			let analysis = r.message;
			let html = `
				<div class="row">
					<div class="col-md-6">
						<h5>Overall Variance</h5>
						<table class="table table-bordered">
							<tr>
								<td>Original Contract:</td>
								<td>${format_currency(analysis.original_contract)}</td>
							</tr>
							<tr>
								<td>Final Account:</td>
								<td>${format_currency(analysis.final_account)}</td>
							</tr>
							<tr class="${analysis.total_variance >= 0 ? 'text-danger' : 'text-success'}">
								<td><strong>Variance:</strong></td>
								<td><strong>${format_currency(analysis.total_variance)} (${analysis.variance_percentage.toFixed(2)}%)</strong></td>
							</tr>
						</table>
					</div>
					<div class="col-md-6">
						<h5>Category Breakdown</h5>
						<table class="table table-bordered">
							<thead>
								<tr>
									<th>Category</th>
									<th>Variance</th>
								</tr>
							</thead>
							<tbody>
			`;
			
			Object.keys(analysis.category_breakdown).forEach(category => {
				let breakdown = analysis.category_breakdown[category];
				html += `
					<tr>
						<td>${category}</td>
						<td class="${breakdown.variance >= 0 ? 'text-danger' : 'text-success'}">${format_currency(breakdown.variance)}</td>
					</tr>
				`;
			});
			
			html += `
							</tbody>
						</table>
					</div>
				</div>
			`;
			
			melon.msgprint({
				title: __('Cost Variance Analysis'),
				message: html,
				wide: true
			});
		}
	});
}

function get_status_color(status) {
	const status_colors = {
		'Draft': 'grey',
		'Under Review': 'blue',
		'Disputed': 'red',
		'Agreed': 'green',
		'Closed': 'dark-grey'
	};
	return status_colors[status] || 'grey';
}
