// Copyright (c) 2025, Alphamonak Solutions

melon.listview_settings['Payment Certificate'] = {
	add_fields: ['status', 'project', 'certificate_date', 'net_payment_amount'],
	get_indicator: function(doc) {
		const status_colors = {
			'Draft': 'red',
			'Submitted': 'green',
			'Paid': 'blue',
			'Cancelled': 'red'
		};
		return [__(doc.status), status_colors[doc.status], 'status,=,' + doc.status];
	}
};
