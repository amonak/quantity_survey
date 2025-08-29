// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Tender Package', {
	refresh: function(frm) {
		// Add custom buttons based on status
		if (frm.doc.docstatus === 1) {
			if (frm.doc.status === "Published") {
				frm.add_custom_button(__('Close Tender'), function() {
					frm.set_value('status', 'Bid Collection');
					frm.save();
				}, __('Actions'));
			}
			
			if (frm.doc.status === "Bid Evaluation") {
				frm.add_custom_button(__('Award Tender'), function() {
					frm.call('award_tender');
				}, __('Actions'));
				
				frm.add_custom_button(__('Comparison Report'), function() {
					generate_comparison_report(frm);
				}, __('Reports'));
			}
			
			if (frm.doc.total_quotes_received > 0) {
				frm.add_custom_button(__('View Quotes'), function() {
					melon.route_options = {
						"tender_package": frm.doc.name
					};
					melon.set_route("List", "Tender Quote");
				}, __('View'));
			}
		}
		
		// Add dashboard indicators
		if (frm.doc.docstatus === 1) {
			frm.dashboard.add_indicator(__('Status: {0}', [frm.doc.status]), 
				get_status_color(frm.doc.status));
			
			if (frm.doc.total_quotes_received) {
				frm.dashboard.add_indicator(__('Quotes: {0}', [frm.doc.total_quotes_received]), 
					'blue');
			}
		}
	},
	
	estimated_value: function(frm) {
		calculate_bid_security_amount(frm);
	},
	
	bid_security_percentage: function(frm) {
		calculate_bid_security_amount(frm);
	},
	
	winning_quote_amount: function(frm) {
		calculate_savings_percentage(frm);
	},
	
	tender_publication_date: function(frm) {
		// Auto-set bid submission deadline (default 21 days from publication)
		if (frm.doc.tender_publication_date && !frm.doc.bid_submission_deadline) {
			let deadline = melon.datetime.add_days(frm.doc.tender_publication_date, 21);
			frm.set_value('bid_submission_deadline', deadline);
		}
	},
	
	bid_submission_deadline: function(frm) {
		// Auto-set bid opening date (next working day)
		if (frm.doc.bid_submission_deadline && !frm.doc.bid_opening_date) {
			let opening_date = melon.datetime.add_days(frm.doc.bid_submission_deadline, 1);
			frm.set_value('bid_opening_date', opening_date);
		}
	}
});

function calculate_bid_security_amount(frm) {
	if (frm.doc.estimated_value && frm.doc.bid_security_percentage) {
		let security_amount = frm.doc.estimated_value * frm.doc.bid_security_percentage / 100;
		frm.set_value('bid_security_amount', security_amount);
	}
}

function calculate_savings_percentage(frm) {
	if (frm.doc.estimated_value && frm.doc.winning_quote_amount) {
		let savings = (frm.doc.estimated_value - frm.doc.winning_quote_amount) / frm.doc.estimated_value * 100;
		frm.set_value('savings_percentage', savings);
	}
}

function generate_comparison_report(frm) {
	frm.call('generate_tender_comparison').then(r => {
		if (r.message && r.message.length > 0) {
			let quotes = r.message;
			let html = `
				<table class="table table-bordered">
					<thead>
						<tr>
							<th>${__('Rank')}</th>
							<th>${__('Supplier')}</th>
							<th>${__('Quote Amount')}</th>
							<th>${__('Validity')}</th>
							<th>${__('Delivery Period')}</th>
						</tr>
					</thead>
					<tbody>
			`;
			
			quotes.forEach((quote, index) => {
				html += `
					<tr>
						<td>${index + 1}</td>
						<td>${melon.utils.escape_html(quote.supplier)}</td>
						<td>${format_currency(quote.total_quote_amount)}</td>
						<td>${melon.utils.escape_html(quote.quote_validity || '-')}</td>
						<td>${melon.utils.escape_html(quote.delivery_period || '-')}</td>
					</tr>
				`;
			});
			
			html += '</tbody></table>';
			
			melon.msgprint({
				title: __('Tender Comparison'),
				message: html,
				wide: true
			});
		} else {
			melon.msgprint(__('No quotes available for comparison'));
		}
	}).catch(err => {
		melon.msgprint(__('Error generating comparison report'));
		console.error(err);
	});
}

function get_status_color(status) {
	const status_colors = {
		'Draft': 'grey',
		'Published': 'blue',
		'Bid Collection': 'orange',
		'Bid Evaluation': 'yellow',
		'Awarded': 'green',
		'Contracted': 'purple',
		'Cancelled': 'red'
	};
	return status_colors[status] || 'grey';
}
