// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Cost Plan', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Create BoQ'), function() {
				create_boq_from_cost_plan(frm);
			});
			
			frm.add_custom_button(__('Cost Analysis'), function() {
				show_cost_analysis(frm);
			});
		}
		
		frm.set_query('project', function() {
			return {
				filters: {
					'status': 'Open'
				}
			};
		});
	},
	
	project: function(frm) {
		if (frm.doc.project) {
			melon.db.get_value('Project', frm.doc.project, 'project_name')
				.then(r => {
					if (r.message) {
						frm.set_value('project_name', r.message.project_name);
					}
				});
		}
	},
	
	contingency_percentage: function(frm) {
		calculate_totals(frm);
	},
	
	overhead_percentage: function(frm) {
		calculate_totals(frm);
	},
	
	approved_budget: function(frm) {
		calculate_budget_variance(frm);
	},
	
	validate: function(frm) {
		calculate_totals(frm);
		calculate_budget_variance(frm);
	}
});

melon.ui.form.on('Cost Plan Item', {
	estimated_cost: function(frm, cdt, cdn) {
		calculate_totals(frm);
		calculate_budget_variance(frm);
	},
	
	cost_plan_items_remove: function(frm) {
		calculate_totals(frm);
		calculate_budget_variance(frm);
	}
});

function calculate_totals(frm) {
	let total_estimated_cost = 0;
	
	frm.doc.cost_plan_items.forEach(function(item) {
		if (item.estimated_cost) {
			total_estimated_cost += flt(item.estimated_cost);
		}
	});
	
	frm.set_value('total_estimated_cost', total_estimated_cost);
	
	// Calculate contingency
	if (frm.doc.contingency_percentage) {
		const contingency_amount = total_estimated_cost * flt(frm.doc.contingency_percentage) / 100;
		frm.set_value('contingency_amount', contingency_amount);
	}
	
	// Calculate overhead
	if (frm.doc.overhead_percentage) {
		const overhead_amount = total_estimated_cost * flt(frm.doc.overhead_percentage) / 100;
		frm.set_value('overhead_amount', overhead_amount);
	}
	
	// Calculate total project cost
	const total_project_cost = total_estimated_cost + 
		flt(frm.doc.contingency_amount) + 
		flt(frm.doc.overhead_amount);
	frm.set_value('total_project_cost', total_project_cost);
}

function calculate_budget_variance(frm) {
	if (frm.doc.approved_budget && frm.doc.total_project_cost) {
		const variance = flt(frm.doc.total_project_cost) - flt(frm.doc.approved_budget);
		frm.set_value('budget_variance', variance);
		
		// Color code the variance field
		if (variance > 0) {
			frm.get_field('budget_variance').$wrapper.css('color', 'red');
		} else if (variance < 0) {
			frm.get_field('budget_variance').$wrapper.css('color', 'green');
		}
	}
}

function create_boq_from_cost_plan(frm) {
	melon.confirm(__('Create BoQ from this Cost Plan?'), function() {
		melon.call({
			method: 'quantity_survey.quantity_surveying.doctype.cost_plan.cost_plan.create_boq_from_cost_plan',
			args: {
				cost_plan: frm.doc.name
			},
			callback: function(r) {
				if (r.message) {
					melon.show_alert({
						message: __('BoQ Created Successfully'),
						indicator: 'green'
					});
					melon.set_route('Form', 'BoQ', r.message.name);
				}
			}
		});
	});
}

function show_cost_analysis(frm) {
	melon.call({
		method: 'quantity_survey.quantity_surveying.doctype.cost_plan.cost_plan.get_cost_analysis',
		args: {
			project: frm.doc.project
		},
		callback: function(r) {
			if (r.message) {
				const dialog = new melon.ui.Dialog({
					title: __('Cost Analysis for {0}', [frm.doc.project]),
					fields: [
						{
							fieldtype: 'HTML',
							fieldname: 'cost_analysis_html'
						}
					]
				});
				
				let html = '<table class="table table-bordered">';
				html += '<tr><th>Cost Plan</th><th>Estimated Cost</th><th>BoQ Total</th><th>Certified Total</th><th>Variance</th></tr>';
				
				r.message.forEach(function(row) {
					const variance = row.total_project_cost - row.boq_total;
					var variance_color = variance > 0 ? 'red' : 'green';
					html += '<tr>';
					html += '<td>' + row.cost_plan_title + '</td>';
					html += '<td>' + format_currency(row.total_project_cost) + '</td>';
					html += '<td>' + format_currency(row.boq_total) + '</td>';
					html += '<td>' + format_currency(row.certified_total) + '</td>';
					html += '<td style="color: ' + variance_color + '">' + format_currency(variance) + '</td>';
					html += '</tr>';
				});
				
				html += '</table>';
				dialog.fields_dict.cost_analysis_html.$wrapper.html(html);
				dialog.show();
			}
		}
	});
}
