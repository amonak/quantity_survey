// Copyright (c) 2025, Alphamonak Solutions

// Global Quantity Survey Module
melon.provide("quantity_survey");

quantity_survey = {
	setup: function() {
		// Initialize quantity survey module
		this.setup_global_filters();
		this.setup_custom_buttons();
		this.setup_mobile_utils();
	},

	setup_global_filters: function() {
		// Add global filters for quantity survey doctypes
		melon.route_options = melon.route_options || {};
		
		// Common project filter
		if (melon.route_options.project) {
			melon.query_reports = melon.query_reports || {};
			$.extend(melon.query_reports, {
				default_filters: {
					project: melon.route_options.project
				}
			});
		}
	},

	setup_custom_buttons: function() {
		// Setup custom buttons for list views
		melon.listview_settings = melon.listview_settings || {};
		
		// BoQ list custom buttons
		if (!melon.listview_settings['BoQ']) {
			melon.listview_settings['BoQ'] = {
				add_fields: ["project", "total_amount", "status"],
				filters: [["status", "!=", "Cancelled"]],
				onload: function(listview) {
					listview.page.add_menu_item(__("Create Template"), function() {
						melon.new_doc("BoQ", {"is_template": 1});
					});
				}
			};
		}
	},

	setup_mobile_utils: function() {
		// Mobile-specific utilities
		if (melon.utils.is_mobile()) {
			this.setup_mobile_forms();
		}
	},

	setup_mobile_forms: function() {
		// Optimize forms for mobile
		$(document).on('page-change', function() {
			if (cur_frm && cur_frm.doctype.includes('BoQ') || 
				cur_frm.doctype.includes('Valuation') ||
				cur_frm.doctype.includes('Variation Order')) {
				
				// Make forms more touch-friendly
				$('.form-control').addClass('mobile-optimized');
				$('.btn').addClass('btn-mobile');
			}
		});
	},

	// Utility functions
	utils: {
		format_currency: function(amount, currency) {
			return melon.format(amount, {fieldtype: "Currency", options: currency});
		},

		calculate_percentage: function(part, total) {
			if (!total || total === 0) return 0;
			return Math.round((part / total) * 100 * 100) / 100;
		},

		get_project_currency: function(project_name, callback) {
			if (!project_name) return;
			
			melon.db.get_value("Project", project_name, "currency", function(r) {
				if (r && callback) {
					callback(r.currency || melon.defaults.get_default("currency"));
				}
			});
		}
	}
};

// Initialize on page load
$(document).ready(function() {
	quantity_survey.setup();
});

// Export for other modules
window.quantity_survey = quantity_survey;
