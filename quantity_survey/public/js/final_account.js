// Copyright (c) 2025, Alphamonak Solutions

melon.ui.form.on('Final Account', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Generate Report'), function() {
				melon.set_route('query-report', 'Final Account Analysis', {
					final_account: frm.doc.name
				});
			});
		}
		
		// Initialize real-time collaboration
		if (!frm.is_new()) {
			frm.collaboration = new RealTimeCollaboration(frm, 'Final Account');
			frm.collaboration.init();
		}
		
		// Initialize enhanced analytics
		frm.init_predictive_analytics();
		frm.init_mobile_features();
		frm.setup_keyboard_shortcuts();
		frm.init_bulk_operations();
	},
	
	calculate_totals: function(frm) {
		let total_amount = 0;
		
		frm.doc.final_account_items.forEach(function(item) {
			total_amount += item.amount || 0;
		});
		
		frm.set_value('total_amount', total_amount);
	},
	
	// Enhanced analytics integration
	init_predictive_analytics: function(frm) {
		if (!frm.predictive_analytics) {
			frm.predictive_analytics = new PredictiveAnalytics(frm);
		}
		frm.predictive_analytics.analyze_final_account_trends();
	},
	
	// Mobile features
	init_mobile_features: function(frm) {
		if (melon.utils.is_mobile()) {
			frm.add_custom_button(__('Camera Capture'), function() {
				melon.mobile.capture_image().then(function(image_data) {
					frm.set_value('attachment', image_data);
				});
			}, __('Mobile'));
			
			frm.add_custom_button(__('GPS Location'), function() {
				melon.mobile.get_location().then(function(location) {
					frm.set_value('location_data', JSON.stringify(location));
				});
			}, __('Mobile'));
		}
	},
	
	// Keyboard shortcuts
	setup_keyboard_shortcuts: function(frm) {
		if (frm.keyboard_shortcuts_setup) return;
		
		melon.ui.keys.add_shortcut({
			shortcut: 'ctrl+s',
			action: () => frm.save(),
			description: __('Save Document'),
			ignore_inputs: true
		});
		
		melon.ui.keys.add_shortcut({
			shortcut: 'ctrl+shift+c',
			action: () => frm.trigger('calculate_totals'),
			description: __('Calculate Totals'),
			ignore_inputs: true
		});
		
		frm.keyboard_shortcuts_setup = true;
	},
	
	// Bulk operations
	init_bulk_operations: function(frm) {
		if (frm.doc.final_account_items && frm.doc.final_account_items.length > 0) {
			frm.add_custom_button(__('Bulk Update Rates'), function() {
				frm.show_bulk_rate_dialog();
			}, __('Bulk Operations'));
			
			frm.add_custom_button(__('Export to Excel'), function() {
				melon.call({
					method: 'quantity_survey.utils.bulk_operations.export_final_account_excel',
					args: {
						final_account_name: frm.doc.name
					},
					callback: function(r) {
						if (r.message) {
							window.open(r.message.file_url);
						}
					}
				});
			}, __('Bulk Operations'));
		}
	},
	
	show_bulk_rate_dialog: function(frm) {
		let dialog = new melon.ui.Dialog({
			title: __('Bulk Update Rates'),
			fields: [
				{
					fieldtype: 'Select',
					fieldname: 'update_type',
					label: __('Update Type'),
					options: 'Percentage\nFixed Amount\nMultiplier',
					reqd: 1
				},
				{
					fieldtype: 'Float',
					fieldname: 'value',
					label: __('Value'),
					reqd: 1
				},
				{
					fieldtype: 'Check',
					fieldname: 'selected_only',
					label: __('Update Selected Rows Only')
				}
			],
			primary_action_label: __('Update'),
			primary_action: function(values) {
				frm.bulk_update_rates(values);
				dialog.hide();
			}
		});
		dialog.show();
	},
	
	bulk_update_rates: function(frm, values) {
		let rows_to_update = values.selected_only ? 
			frm.get_selected_items('final_account_items') : 
			frm.doc.final_account_items;
		
		rows_to_update.forEach(function(item) {
			let new_rate = item.rate || 0;
			
			switch(values.update_type) {
				case 'Percentage':
					new_rate = new_rate * (1 + values.value / 100);
					break;
				case 'Fixed Amount':
					new_rate = new_rate + values.value;
					break;
				case 'Multiplier':
					new_rate = new_rate * values.value;
					break;
			}
			
			melon.model.set_value(item.doctype, item.name, 'rate', new_rate);
		});
		
		frm.trigger('calculate_totals');
		melon.show_alert(__('Rates updated successfully'));
	}
});

melon.ui.form.on('Final Account Item', {
	quantity: function(frm, cdt, cdn) {
		calculate_final_amount(frm, cdt, cdn);
		
		// Broadcast change to collaborators
		if (frm.collaboration) {
			let item = locals[cdt][cdn];
			frm.collaboration.broadcast_field_change('quantity', item.quantity, item.name);
		}
	},
	
	rate: function(frm, cdt, cdn) {
		calculate_final_amount(frm, cdt, cdn);
		
		// Broadcast change to collaborators
		if (frm.collaboration) {
			let item = locals[cdt][cdn];
			frm.collaboration.broadcast_field_change('rate', item.rate, item.name);
		}
	},
	
	// Enhanced validation with predictive analysis
	before_final_account_item_remove: function(frm, cdt, cdn) {
		let item = locals[cdt][cdn];
		
		// Check if item has significant impact on total
		let item_percentage = (item.amount || 0) / (frm.doc.total_amount || 1) * 100;
		
		if (item_percentage > 10) {
			melon.confirm(
				__('This item represents {0}% of the total amount. Are you sure you want to remove it?', [item_percentage.toFixed(2)]),
				function() {
					// Proceed with removal
					melon.model.clear_doc(cdt, cdn);
					frm.trigger('calculate_totals');
				}
			);
			return false;
		}
		
		return true;
	},
	
	// Smart suggestions for new items
	item_code: function(frm, cdt, cdn) {
		let item = locals[cdt][cdn];
		
		if (item.item_code && frm.predictive_analytics) {
			// Get smart rate suggestion
			melon.call({
				method: 'quantity_survey.ai_analytics.smart_defaults.get_rate_suggestion',
				args: {
					item_code: item.item_code,
					project: frm.doc.project,
					context: 'final_account'
				},
				callback: function(r) {
					if (r.message && r.message.suggested_rate) {
						melon.model.set_value(cdt, cdn, 'rate', r.message.suggested_rate);
						
						if (r.message.confidence_score < 0.7) {
							melon.show_alert({
								message: __('Rate suggestion has low confidence. Please verify.'),
								indicator: 'orange'
							});
						}
					}
				}
			});
		}
	}
});

function calculate_final_amount(frm, cdt, cdn) {
	let item = locals[cdt][cdn];
	let amount = (item.quantity || 0) * (item.rate || 0);
	melon.model.set_value(cdt, cdn, 'amount', amount);
	frm.trigger('calculate_totals');
	
	// Trigger predictive analysis
	if (frm.predictive_analytics) {
		frm.predictive_analytics.analyze_item_variance(item);
	}
}

// Real-time Collaboration Class
class RealTimeCollaboration {
	constructor(frm, doctype) {
		this.frm = frm;
		this.doctype = doctype;
		this.docname = frm.doc.name;
		this.active_users = [];
		this.socket = null;
		this.session_id = null;
		this.last_sync = new Date();
	}
	
	init() {
		this.connect_websocket();
		this.join_collaboration_session();
		this.setup_ui();
		this.setup_event_listeners();
	}
	
	connect_websocket() {
		if (!melon.socketio) {
			console.warn('Socket.IO not available for real-time collaboration');
			return;
		}
		
		this.socket = melon.socketio;
		this.setup_socket_listeners();
	}
	
	setup_socket_listeners() {
		if (!this.socket) return;
		
		// Listen for collaboration events
		this.socket.on('collaboration_user_joined', (data) => {
			if (data.doctype === this.doctype && data.docname === this.docname) {
				this.handle_user_joined(data);
			}
		});
		
		this.socket.on('collaboration_user_left', (data) => {
			if (data.doctype === this.doctype && data.docname === this.docname) {
				this.handle_user_left(data);
			}
		});
		
		this.socket.on('collaboration_field_changed', (data) => {
			if (data.doctype === this.doctype && data.docname === this.docname) {
				this.handle_field_change(data);
			}
		});
		
		this.socket.on('collaboration_cursor_moved', (data) => {
			if (data.doctype === this.doctype && data.docname === this.docname) {
				this.handle_cursor_movement(data);
			}
		});
		
		this.socket.on('collaboration_message', (data) => {
			if (data.doctype === this.doctype && data.docname === this.docname) {
				this.handle_collaboration_message(data);
			}
		});
	}
	
	join_collaboration_session() {
		melon.call({
			method: 'quantity_survey.collaboration.join_collaboration_session',
			args: {
				doctype: this.doctype,
				docname: this.docname
			},
			callback: (r) => {
				if (r.message && r.message.success) {
					this.session_id = r.message.session_id;
					this.active_users = r.message.active_users || [];
					this.update_collaboration_ui();
				}
			}
		});
	}
	
	setup_ui() {
		// Add collaboration indicator to form
		let collaboration_html = `
			<div class="collaboration-panel" style="position: fixed; top: 100px; right: 20px; 
				 background: white; border: 1px solid #ddd; padding: 10px; border-radius: 8px; 
				 min-width: 250px; max-height: 400px; overflow-y: auto; z-index: 1000; display: none;">
				<div class="collaboration-header">
					<h6>${__('Active Collaborators')}</h6>
					<button class="btn btn-xs btn-default pull-right" onclick="$(this).closest('.collaboration-panel').hide()">×</button>
				</div>
				<div class="active-users-list"></div>
				<div class="collaboration-messages" style="max-height: 150px; overflow-y: auto; margin-top: 10px;">
					<div class="messages-list"></div>
					<input type="text" class="form-control input-sm" placeholder="${__('Type a message...')}" 
						   style="margin-top: 5px;" onkeypress="if(event.keyCode==13) this.sendMessage(this.value)">
				</div>
			</div>
		`;
		
		$(document.body).append(collaboration_html);
		
		// Add collaboration button to form toolbar
		this.frm.add_custom_button(__('Collaboration'), () => {
			$('.collaboration-panel').toggle();
		}, __('Tools'));
	}
	
	setup_event_listeners() {
		// Listen for field changes
		$(document).on('change input', '.melon-control input, .melon-control textarea, .melon-control select', (e) => {
			let field = $(e.target).attr('data-fieldname');
			if (field && this.session_id) {
				clearTimeout(this.broadcast_timeout);
				this.broadcast_timeout = setTimeout(() => {
					this.broadcast_field_change(field, e.target.value);
				}, 500); // Debounce
			}
		});
		
		// Listen for cursor movement
		$(document).on('focus', '.melon-control input, .melon-control textarea', (e) => {
			let field = $(e.target).attr('data-fieldname');
			if (field && this.session_id) {
				this.broadcast_cursor_position(field, e.target.selectionStart || 0);
			}
		});
	}
	
	broadcast_field_change(fieldname, value, row_name = null) {
		if (!this.session_id) return;
		
		melon.call({
			method: 'quantity_survey.collaboration.broadcast_field_change',
			args: {
				doctype: this.doctype,
				docname: this.docname,
				fieldname: fieldname,
				value: value,
				field_type: 'text'
			},
			callback: (r) => {
				if (r.message && !r.message.success) {
					console.warn('Failed to broadcast field change:', r.message.message);
				}
			}
		});
	}
	
	broadcast_cursor_position(fieldname, position) {
		if (!this.session_id) return;
		
		melon.call({
			method: 'quantity_survey.collaboration.broadcast_cursor_position',
			args: {
				doctype: this.doctype,
				docname: this.docname,
				fieldname: fieldname,
				position: position
			}
		});
	}
	
	handle_user_joined(data) {
		this.active_users = data.active_users || [];
		this.update_collaboration_ui();
		
		melon.show_alert({
			message: __(`{0} joined the collaboration session`, [data.user_info.full_name]),
			indicator: 'green'
		});
	}
	
	handle_user_left(data) {
		this.active_users = data.active_users || [];
		this.update_collaboration_ui();
		
		melon.show_alert({
			message: __(`User left the collaboration session`),
			indicator: 'orange'
		});
	}
	
	handle_field_change(data) {
		let change = data.change_info;
		
		// Don't apply changes from current user
		if (change.user === melon.session.user) return;
		
		// Find and update the field
		let field_element = $(`[data-fieldname="${change.fieldname}"]`);
		
		if (field_element.length && field_element.val() !== change.value) {
			// Show conflict indicator
			this.show_field_conflict(change.fieldname, field_element.val(), change.value, change.full_name);
		}
	}
	
	handle_cursor_movement(data) {
		if (data.user === melon.session.user) return;
		
		// Show cursor indicator for other users
		let field_element = $(`[data-fieldname="${data.fieldname}"]`);
		if (field_element.length) {
			this.show_cursor_indicator(field_element, data.user, data.position);
		}
	}
	
	handle_collaboration_message(data) {
		let message = data.message_info;
		let messages_list = $('.messages-list');
		
		let message_html = `
			<div class="collaboration-message" style="margin: 5px 0; padding: 5px; border-left: 3px solid #007bff;">
				<div class="message-header" style="font-size: 11px; color: #666;">
					<strong>${message.full_name}</strong> - ${melon.datetime.str_to_user(message.timestamp)}
				</div>
				<div class="message-body" style="margin-top: 2px;">${message.message}</div>
			</div>
		`;
		
		messages_list.append(message_html);
		messages_list.scrollTop(messages_list[0].scrollHeight);
	}
	
	show_field_conflict(fieldname, local_value, remote_value, remote_user) {
		let dialog = new melon.ui.Dialog({
			title: __('Field Conflict Detected'),
			fields: [
				{
					fieldtype: 'HTML',
					options: `
						<p>${__('Field {0} has been modified by {1}:', [fieldname, remote_user])}</p>
						<div class="row">
							<div class="col-sm-6">
								<label>${__('Your Value:')}</label>
								<div class="well well-sm">${local_value}</div>
							</div>
							<div class="col-sm-6">
								<label>${__('Their Value:')}</label>
								<div class="well well-sm">${remote_value}</div>
							</div>
						</div>
					`
				},
				{
					fieldtype: 'Select',
					fieldname: 'resolution',
					label: __('Resolution'),
					options: `Keep Mine\nAccept Theirs\nMerge Values`,
					reqd: 1
				}
			],
			primary_action_label: __('Resolve'),
			primary_action: (values) => {
				this.resolve_field_conflict(fieldname, local_value, remote_value, values.resolution);
				dialog.hide();
			}
		});
		
		dialog.show();
	}
	
	resolve_field_conflict(fieldname, local_value, remote_value, resolution) {
		let winning_value = local_value;
		
		switch(resolution) {
			case 'Accept Theirs':
				winning_value = remote_value;
				break;
			case 'Merge Values':
				winning_value = local_value + ' | ' + remote_value;
				break;
		}
		
		// Update field
		this.frm.set_value(fieldname, winning_value);
		
		// Notify server of resolution
		melon.call({
			method: 'quantity_survey.collaboration.resolve_conflict',
			args: {
				doctype: this.doctype,
				docname: this.docname,
				fieldname: fieldname,
				resolution: resolution,
				winning_value: winning_value
			}
		});
	}
	
	show_cursor_indicator(field_element, user, position) {
		// Remove existing cursor indicators for this user
		$(`.cursor-indicator-${user}`).remove();
		
		// Create cursor indicator
		let indicator = $(`<span class="cursor-indicator-${user}" 
			style="position: absolute; width: 2px; height: 20px; background: #007bff; z-index: 1001;">
			<span style="position: absolute; top: -20px; font-size: 10px; background: #007bff; 
				 color: white; padding: 2px 4px; border-radius: 3px; white-space: nowrap;">${user}</span>
		</span>`);
		
		// Position indicator
		field_element.parent().css('position', 'relative');
		field_element.parent().append(indicator);
		
		// Auto-remove after 10 seconds
		setTimeout(() => {
			indicator.remove();
		}, 10000);
	}
	
	update_collaboration_ui() {
		let users_list = $('.active-users-list');
		users_list.empty();
		
		this.active_users.forEach(user => {
			if (user.user !== melon.session.user) {
				let user_html = `
					<div class="active-user" style="display: flex; align-items: center; margin: 5px 0;">
						<img src="${user.image || '/assets/melon/images/ui/avatar.png'}" 
							 class="avatar avatar-small" style="width: 24px; height: 24px; margin-right: 8px;">
						<span style="flex: 1;">${user.full_name}</span>
						<span class="indicator ${user.status === 'active' ? 'green' : 'grey'}"></span>
					</div>
				`;
				users_list.append(user_html);
			}
		});
		
		// Update collaboration button badge
		let collaboration_btn = this.frm.custom_buttons[__('Collaboration')];
		if (collaboration_btn && this.active_users.length > 1) {
			collaboration_btn.html(__('Collaboration') + ` <span class="badge">${this.active_users.length - 1}</span>`);
		}
	}
	
	leave_session() {
		if (this.session_id) {
			melon.call({
				method: 'quantity_survey.collaboration.leave_collaboration_session',
				args: {
					doctype: this.doctype,
					docname: this.docname
				}
			});
		}
	}
}

// Enhanced Predictive Analytics Class
class PredictiveAnalytics {
	constructor(frm) {
		this.frm = frm;
		this.model_cache = {};
		this.trend_data = null;
	}
	
	analyze_final_account_trends() {
		melon.call({
			method: 'quantity_survey.ai_analytics.cost_predictor.analyze_cost_trends',
			args: {
				project: this.frm.doc.project,
				doctype: 'Final Account',
				context: 'final_account_analysis'
			},
			callback: (r) => {
				if (r.message) {
					this.trend_data = r.message;
					this.show_trend_insights();
				}
			}
		});
	}
	
	analyze_item_variance(item) {
		if (!this.trend_data || !item.item_code) return;
		
		melon.call({
			method: 'quantity_survey.ai_analytics.cost_predictor.predict_item_cost',
			args: {
				item_code: item.item_code,
				quantity: item.quantity,
				current_rate: item.rate,
				project: this.frm.doc.project
			},
			callback: (r) => {
				if (r.message && r.message.variance_alert) {
					this.show_variance_alert(item, r.message);
				}
			}
		});
	}
	
	show_trend_insights() {
		if (!this.trend_data) return;
		
		// Add insights section to form
		let insights_html = `
			<div class="predictive-insights" style="background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px;">
				<h6>${__('Predictive Insights')}</h6>
				<div class="row">
					<div class="col-sm-6">
						<div class="insight-item">
							<strong>${__('Cost Trend:')}</strong>
							<span class="indicator ${this.trend_data.trend === 'increasing' ? 'red' : 'green'}"></span>
							${__(this.trend_data.trend_description)}
						</div>
					</div>
					<div class="col-sm-6">
						<div class="insight-item">
							<strong>${__('Predicted Total:')}</strong>
							${format_currency(this.trend_data.predicted_total)}
						</div>
					</div>
				</div>
				${this.trend_data.recommendations ? `
					<div class="recommendations" style="margin-top: 10px;">
						<strong>${__('Recommendations:')}</strong>
						<ul style="margin: 5px 0 0 20px;">
							${this.trend_data.recommendations.map(rec => `<li>${rec}</li>`).join('')}
						</ul>
					</div>
				` : ''}
			</div>
		`;
		
		// Insert after form header
		$(insights_html).insertAfter(this.frm.layout.wrapper.find('.form-layout'));
	}
	
	show_variance_alert(item, prediction) {
		let variance_percent = Math.abs((item.rate - prediction.predicted_rate) / prediction.predicted_rate * 100);
		
		if (variance_percent > 15) {
			melon.show_alert({
				message: __('Item {0} rate varies {1}% from predicted value', [item.item_code, variance_percent.toFixed(1)]),
				indicator: variance_percent > 30 ? 'red' : 'orange'
			});
		}
	}
}

// Auto-cleanup collaboration when form is closed
$(document).on('page-change', function() {
	if (cur_frm && cur_frm.collaboration) {
		cur_frm.collaboration.leave_session();
	}
});

// Initialize service worker for offline capabilities
if ('serviceWorker' in navigator) {
	navigator.serviceWorker.register('/assets/quantity_survey/quantity-survey-sw.js')
		.then(registration => {
			console.log('Quantity Survey SW registered');
		})
		.catch(error => {
			console.log('SW registration failed');
		});
}
