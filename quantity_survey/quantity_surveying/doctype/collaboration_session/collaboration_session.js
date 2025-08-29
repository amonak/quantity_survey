/* eslint-disable */
// Copyright (c) 2024, [Your Company] 

melon.ui.form.on('Collaboration Session', {
	refresh: function(frm) {
		// Add custom buttons for collaboration
		if (frm.doc.active_users_count > 1) {
			frm.add_custom_button(__('View Active Users'), function() {
				melon.msgprint({
					title: __('Active Collaborators'),
					message: __('This session has {0} active users', [frm.doc.active_users_count]),
					indicator: 'blue'
				});
			});
		}
		
		// Add cleanup button for system managers
		if (melon.user.has_role('System Manager')) {
			frm.add_custom_button(__('Force Cleanup'), function() {
				melon.confirm(
					__('This will cleanup inactive users from this session. Continue?'),
					function() {
						melon.call({
							method: 'quantity_survey.collaboration.cleanup_session_users',
							args: {
								session_id: frm.doc.name
							},
							callback: function(r) {
								if (r.message && r.message.success) {
									melon.show_alert(__('Session cleaned up successfully'));
									frm.reload_doc();
								}
							}
						});
					}
				);
			});
		}
	}
});
