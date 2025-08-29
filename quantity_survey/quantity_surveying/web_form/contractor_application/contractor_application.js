melon.ready(function() {
	// Set default supplier group for contractors
	if (!melon.web_form.get_value('supplier_group')) {
		melon.web_form.set_value('supplier_group', 'Construction');
	}
	
	// Validate website URL
	melon.web_form.on('website', function(field, value) {
		if (value && !melon.utils.is_url(value)) {
			melon.msgprint(__('Please enter a valid website URL'));
			melon.web_form.set_value('website', '');
		}
	});
	
	// Auto-format tax ID
	melon.web_form.on('tax_id', function(field, value) {
		if (value) {
			// Remove any non-alphanumeric characters
			var cleaned = value.replace(/[^a-zA-Z0-9]/g, '');
			if (cleaned !== value) {
				melon.web_form.set_value('tax_id', cleaned);
			}
		}
	});
});
