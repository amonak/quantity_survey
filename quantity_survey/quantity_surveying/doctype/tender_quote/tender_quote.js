// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Tender Quote', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Load BoQ Items'), function() {
				frm.call('get_boq_items');
			}, __('Actions'));
		}
		
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Compare with Estimate'), function() {
				show_comparison_dialog(frm);
			}, __('Reports'));
		}
		
		// Set indicators
		if (frm.doc.quote_status) {
			frm.dashboard.add_indicator(__('Status: {0}', [frm.doc.quote_status]), 
				get_quote_status_color(frm.doc.quote_status));
		}
		
		if (frm.doc.overall_score) {
			frm.dashboard.add_indicator(__('Score: {0}%', [frm.doc.overall_score]), 
				get_score_color(frm.doc.overall_score));
		}
	},
	
	tender_package: function(frm) {
		// Fetch tender package details
		if (frm.doc.tender_package) {
			melon.db.get_doc('Tender Package', frm.doc.tender_package).then(tender => {
				// Auto-fill bid security amount if required
				if (tender.bid_security_percentage && tender.estimated_value) {
					let security_amount = tender.estimated_value * tender.bid_security_percentage / 100;
					frm.set_value('bid_security_amount', security_amount);
				}
			});
		}
	},
	
	discount_percentage: function(frm) {
		calculate_totals(frm);
	},
	
	tax_percentage: function(frm) {
		calculate_totals(frm);
	},
	
	technical_compliance: function(frm) {
		calculate_overall_score(frm);
	},
	
	commercial_compliance: function(frm) {
		calculate_overall_score(frm);
	}
});

melon.ui.form.on('Tender Quote Item', {
	quantity: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
		calculate_totals(frm);
	},
	
	unit_rate: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
		calculate_totals(frm);
	},
	
	quote_items_remove: function(frm) {
		calculate_totals(frm);
	}
});

function calculate_item_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	if (row.quantity && row.unit_rate) {
		row.amount = row.quantity * row.unit_rate;
		refresh_field('amount', cdn, 'quote_items');
	}
}

function calculate_totals(frm) {
	let total_base = 0;
	
	// Calculate base total
	frm.doc.quote_items.forEach(item => {
		if (item.amount) {
			total_base += item.amount;
		}
	});
	
	frm.set_value('total_base_amount', total_base);
	
	// Calculate discount
	let discount_amount = 0;
	if (frm.doc.discount_percentage) {
		discount_amount = total_base * frm.doc.discount_percentage / 100;
	}
	frm.set_value('discount_amount', discount_amount);
	
	// Calculate tax
	let net_amount = total_base - discount_amount;
	let tax_amount = 0;
	if (frm.doc.tax_percentage) {
		tax_amount = net_amount * frm.doc.tax_percentage / 100;
	}
	frm.set_value('tax_amount', tax_amount);
	
	// Final total
	frm.set_value('total_quote_amount', net_amount + tax_amount);
}

function calculate_overall_score(frm) {
	if (frm.doc.technical_compliance && frm.doc.commercial_compliance) {
		// Weighted scoring: 60% technical, 40% commercial
		let technical_weight = 0.6;
		let commercial_weight = 0.4;
		
		let overall_score = (frm.doc.technical_compliance * technical_weight) + 
						   (frm.doc.commercial_compliance * commercial_weight);
		
		frm.set_value('overall_score', overall_score);
	}
}

function show_comparison_dialog(frm) {
	frm.call('compare_with_estimate').then(r => {
		if (r.message) {
			let data = r.message;
			let variance_class = data.variance_amount >= 0 ? 'text-danger' : 'text-success';
			
			let html = `
				<table class="table table-bordered">
					<tr>
						<td><strong>Estimated Value:</strong></td>
						<td>${format_currency(data.estimated_value)}</td>
					</tr>
					<tr>
						<td><strong>Quote Amount:</strong></td>
						<td>${format_currency(data.quote_amount)}</td>
					</tr>
					<tr class="${variance_class}">
						<td><strong>Variance:</strong></td>
						<td>${format_currency(data.variance_amount)} (${data.variance_percentage.toFixed(2)}%)</td>
					</tr>
				</table>
			`;
			
			melon.msgprint({
				title: __('Quote vs Estimate Comparison'),
				message: html,
				wide: true
			});
		}
	});
}

function get_quote_status_color(status) {
	const status_colors = {
		'Draft': 'grey',
		'Submitted': 'blue',
		'Under Evaluation': 'orange',
		'Accepted': 'green',
		'Rejected': 'red',
		'Withdrawn': 'dark-grey'
	};
	return status_colors[status] || 'grey';
}

function get_score_color(score) {
	if (score >= 80) return 'green';
	if (score >= 60) return 'orange';
	return 'red';
}
