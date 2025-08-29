// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Final Account Item', {
	refresh: function(frm, cdt, cdn) {
		// Set item code filter to construction items only
		frm.set_query('item_code', 'final_account_items', function() {
			return {
				filters: {
					'is_construction_item': 1,
					'disabled': 0
				}
			};
		});
		
		// Add visual indicators for variance
		add_variance_indicators(frm, cdt, cdn);
	},
	
	item_code: function(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.item_code) {
			// Show loading indicator
			melon.show_progress(__('Loading item details...'), 50);
			
			// Get item details with error handling
			melon.db.get_doc('Item', row.item_code)
				.then(item => {
					melon.model.set_value(cdt, cdn, {
						'item_name': item.item_name,
						'description': item.description,
						'uom': item.stock_uom,
						'standard_rate': item.standard_rate || 0
					});
					
					// Auto-populate from BoQ if available
					get_boq_item_details(frm, cdt, cdn, row.item_code);
					melon.hide_progress();
				})
				.catch(error => {
					melon.hide_progress();
					melon.msgprint({
						title: __('Error'),
						message: __('Could not fetch item details: {0}', [error.message]),
						indicator: 'red'
					});
				});
		}
	},
	
	boq_quantity: function(frm, cdt, cdn) {
		calculate_variance(frm, cdt, cdn);
		validate_quantity_limits(frm, cdt, cdn);
	},
	
	actual_quantity: function(frm, cdt, cdn) {
		calculate_variance(frm, cdt, cdn);
		calculate_actual_amount(frm, cdt, cdn);
		validate_quantity_limits(frm, cdt, cdn);
		update_progress_indicator(frm, cdt, cdn);
	},
	
	actual_rate: function(frm, cdt, cdn) {
		calculate_actual_amount(frm, cdt, cdn);
		validate_rate_variance(frm, cdt, cdn);
	},
	
	final_account_items_remove: function(frm, cdt, cdn) {
		// Recalculate totals when item is removed
		setTimeout(() => calculate_form_totals(frm), 100);
	}
});

function calculate_variance(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.boq_quantity && row.actual_quantity) {
		const variance = flt(row.actual_quantity) - flt(row.boq_quantity);
		melon.model.set_value(cdt, cdn, 'quantity_variance', variance);
		
		// Calculate percentage variance
		if (row.boq_quantity > 0) {
			const variance_percentage = (variance / flt(row.boq_quantity)) * 100;
			melon.model.set_value(cdt, cdn, 'variance_percentage', variance_percentage);
		}
	}
}

function calculate_actual_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.actual_quantity && row.actual_rate) {
		const amount = flt(row.actual_quantity) * flt(row.actual_rate);
		melon.model.set_value(cdt, cdn, 'actual_amount', amount);
		
		// Calculate amount variance
		if (row.boq_amount) {
			const amount_variance = amount - flt(row.boq_amount);
			melon.model.set_value(cdt, cdn, 'amount_variance', amount_variance);
		}
		
		// Update form totals
		calculate_form_totals(frm);
	}
}

// Enhanced helper functions
function get_boq_item_details(frm, cdt, cdn, item_code) {
	if (frm.doc.boq_reference) {
		melon.call({
			method: 'quantity_survey.quantity_surveying.doctype.final_account.final_account.get_boq_item_details',
			args: {
				'boq': frm.doc.boq_reference,
				'item_code': item_code
			},
			callback: function(r) {
				if (r.message) {
					melon.model.set_value(cdt, cdn, {
						'boq_quantity': r.message.quantity,
						'boq_rate': r.message.rate,
						'boq_amount': r.message.amount
					});
					calculate_variance(frm, cdt, cdn);
				}
			}
		});
	}
}

function validate_quantity_limits(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	const settings = melon.boot.quantity_survey_settings || {};
	const max_variance_percentage = settings.max_quantity_variance_percentage || 20;
	
	if (row.variance_percentage && Math.abs(row.variance_percentage) > max_variance_percentage) {
		melon.msgprint({
			title: __('High Variance Alert'),
			message: __('Quantity variance of {0}% exceeds the maximum allowed variance of {1}%', 
				[row.variance_percentage.toFixed(2), max_variance_percentage]),
			indicator: 'orange'
		});
	}
}

function validate_rate_variance(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	const settings = melon.boot.quantity_survey_settings || {};
	const max_rate_variance = settings.max_rate_variance_percentage || 15;
	
	if (row.boq_rate && row.actual_rate) {
		const rate_variance_percentage = ((flt(row.actual_rate) - flt(row.boq_rate)) / flt(row.boq_rate)) * 100;
		
		if (Math.abs(rate_variance_percentage) > max_rate_variance) {
			melon.msgprint({
				title: __('Rate Variance Alert'),
				message: __('Rate variance of {0}% exceeds the maximum allowed variance of {1}%', 
					[rate_variance_percentage.toFixed(2), max_rate_variance]),
				indicator: 'orange'
			});
		}
	}
}

function add_variance_indicators(frm, cdt, cdn) {
	// Add color coding for variance columns
	setTimeout(() => {
		$('[data-fieldname="variance_percentage"]').each(function() {
			const value = parseFloat($(this).text());
			if (!isNaN(value)) {
				if (Math.abs(value) > 10) {
					$(this).addClass('text-danger font-weight-bold');
				} else if (Math.abs(value) > 5) {
					$(this).addClass('text-warning font-weight-bold');
				} else {
					$(this).addClass('text-success');
				}
			}
		});
	}, 500);
}

function update_progress_indicator(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.boq_quantity && row.actual_quantity) {
		const completion_percentage = (flt(row.actual_quantity) / flt(row.boq_quantity)) * 100;
		melon.model.set_value(cdt, cdn, 'completion_percentage', completion_percentage);
	}
}

function calculate_form_totals(frm) {
	// This would trigger parent form recalculation
	if (frm.doc.__islocal) return;
	
	melon.call({
		method: 'quantity_survey.quantity_surveying.doctype.final_account.final_account.recalculate_totals',
		args: {
			'final_account': frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				frm.refresh();
			}
		}
	});
}

// Advanced Analytics Functions
function predictive_cost_analysis(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row.item_code) return;
	
	melon.call({
		method: 'quantity_survey.analytics.cost_predictor.analyze_cost_trends',
		args: {
			'item_code': row.item_code,
			'project_location': frm.doc.project_location,
			'historical_months': 12
		},
		callback: function(r) {
			if (r.message && r.message.prediction) {
				// Show predictive insights
				const prediction = r.message.prediction;
				melon.msgprint({
					title: __('Cost Analysis Insights'),
					message: `
						<div class="cost-prediction-card">
							<h5>${__('Predictive Analysis for')} ${row.item_name}</h5>
							<p><strong>${__('Predicted Cost')}:</strong> ${format_currency(prediction.predicted_cost)}</p>
							<p><strong>${__('Confidence Level')}:</strong> ${prediction.confidence}%</p>
							<p><strong>${__('Market Trend')}:</strong> <span class="trend-${prediction.trend.toLowerCase()}">${prediction.trend}</span></p>
							<p><strong>${__('Recommendation')}:</strong> ${prediction.recommendation}</p>
						</div>
					`,
					indicator: prediction.trend === 'Rising' ? 'orange' : 'green'
				});
				
				// Auto-suggest optimal rate
				if (prediction.suggested_rate && !row.actual_rate) {
					melon.model.set_value(cdt, cdn, 'suggested_rate', prediction.suggested_rate);
				}
			}
		}
	});
}

// Keyboard Shortcuts Implementation
function setup_keyboard_shortcuts(frm) {
	// Ctrl+S for quick save
	$(document).on('keydown', function(e) {
		if (e.ctrlKey && e.keyCode === 83) {
			e.preventDefault();
			if (frm.doc.__unsaved) {
				frm.save();
			}
		}
		
		// Ctrl+D for duplicate item
		if (e.ctrlKey && e.keyCode === 68) {
			e.preventDefault();
			duplicate_selected_row(frm);
		}
		
		// Ctrl+B for bulk operations
		if (e.ctrlKey && e.keyCode === 66) {
			e.preventDefault();
			show_bulk_operations_dialog(frm);
		}
		
		// F2 for quick edit mode
		if (e.keyCode === 113) {
			e.preventDefault();
			enable_quick_edit_mode(frm);
		}
	});
}

// Bulk Operations
function show_bulk_operations_dialog(frm) {
	let d = new melon.ui.Dialog({
		title: __('Bulk Operations'),
		fields: [
			{
				label: __('Operation'),
				fieldname: 'operation',
				fieldtype: 'Select',
				options: [
					'Update Rate',
					'Apply Variance %',
					'Update UOM',
					'Bulk Delete',
					'Export to Excel',
					'Import from Template'
				],
				reqd: 1
			},
			{
				label: __('Filter Items'),
				fieldname: 'filter_section',
				fieldtype: 'Section Break'
			},
			{
				label: __('Item Category'),
				fieldname: 'item_category',
				fieldtype: 'Link',
				options: 'Item Group'
			},
			{
				label: __('Variance Above %'),
				fieldname: 'variance_threshold',
				fieldtype: 'Percent'
			},
			{
				label: __('Action Parameters'),
				fieldname: 'action_section',
				fieldtype: 'Section Break'
			},
			{
				label: __('New Rate / Value'),
				fieldname: 'new_value',
				fieldtype: 'Currency'
			},
			{
				label: __('Percentage Adjustment'),
				fieldname: 'percentage_adjustment',
				fieldtype: 'Percent'
			}
		],
		primary_action_label: __('Execute'),
		primary_action: function() {
			execute_bulk_operation(frm, d.get_values());
			d.hide();
		}
	});
	
	d.show();
}

function execute_bulk_operation(frm, values) {
	melon.call({
		method: 'quantity_survey.utils.bulk_operations.execute_bulk_operation',
		args: {
			'final_account': frm.doc.name,
			'operation': values.operation,
			'filters': {
				'item_category': values.item_category,
				'variance_threshold': values.variance_threshold
			},
			'parameters': {
				'new_value': values.new_value,
				'percentage_adjustment': values.percentage_adjustment
			}
		},
		callback: function(r) {
			if (r.message) {
				melon.msgprint(__('Bulk operation completed successfully'));
				frm.refresh();
			}
		}
	});
}

// Smart Defaults Implementation
function apply_smart_defaults(frm, cdt, cdn, item_code) {
	melon.call({
		method: 'quantity_survey.ai.smart_defaults.get_intelligent_defaults',
		args: {
			'item_code': item_code,
			'project': frm.doc.project,
			'location': frm.doc.project_location,
			'project_type': frm.doc.project_type
		},
		callback: function(r) {
			if (r.message) {
				const defaults = r.message;
				
				// Apply smart defaults with user confirmation
				melon.confirm(
					__('Apply AI-suggested defaults?<br><br>' +
					   'Suggested Rate: {0}<br>' +
					   'Typical Quantity: {1}<br>' +
					   'Based on: {2} similar projects', 
					   [format_currency(defaults.suggested_rate), 
					    defaults.typical_quantity, 
					    defaults.confidence_samples]),
					function() {
						melon.model.set_value(cdt, cdn, {
							'suggested_rate': defaults.suggested_rate,
							'market_rate': defaults.market_rate,
							'confidence_level': defaults.confidence_level
						});
					}
				);
			}
		}
	});
}

// Mobile Optimization Functions
function setup_mobile_enhancements(frm) {
	if (melon.utils.is_mobile()) {
		// Enable touch-friendly interactions
		$('.grid-row').addClass('mobile-touch-row');
		
		// Add swipe gestures for mobile
		add_swipe_gestures(frm);
		
		// Setup offline capability
		setup_offline_sync(frm);
		
		// GPS integration for location-based data
		setup_gps_integration(frm);
	}
}

function setup_offline_sync(frm) {
	// Service Worker for offline functionality
	if ('serviceWorker' in navigator) {
		navigator.serviceWorker.register('/quantity-survey-sw.js')
			.then(function(registration) {
				console.log('Offline sync enabled');
				
				// Queue data for sync when online
				window.addEventListener('online', function() {
					sync_offline_data(frm);
				});
			});
	}
}

function setup_gps_integration(frm) {
	if (navigator.geolocation && frm.is_new()) {
		navigator.geolocation.getCurrentPosition(function(position) {
			melon.model.set_value(frm.doctype, frm.docname, {
				'gps_latitude': position.coords.latitude,
				'gps_longitude': position.coords.longitude,
				'location_accuracy': position.coords.accuracy
			});
		});
	}
}

// Real-time Collaboration Setup
function setup_realtime_collaboration(frm) {
	if (frm.doc.name && !frm.is_new()) {
		// WebSocket connection for real-time updates
		melon.realtime.on('final_account_update', function(data) {
			if (data.docname === frm.doc.name && data.user !== melon.session.user) {
				show_collaboration_notification(data);
				if (data.auto_refresh) {
					frm.refresh();
				}
			}
		});
		
		// Broadcast changes to other users
		frm.doc.__onchange = function() {
			melon.realtime.publish('final_account_update', {
				'docname': frm.doc.name,
				'user': melon.session.user,
				'user_fullname': melon.user.full_name(),
				'timestamp': melon.datetime.now_datetime(),
				'action': 'modified'
			});
		};
	}
}

function show_collaboration_notification(data) {
	melon.show_alert({
		message: __('User {0} is also editing this document', [data.user_fullname]),
		indicator: 'blue'
	});
}
