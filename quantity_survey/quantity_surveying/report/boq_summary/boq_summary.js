// Copyright (c) 2025, Alphamonak Solutions

melon.query_reports["BoQ Summary"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: melon.datetime.add_months(melon.datetime.nowdate(), -12),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: melon.datetime.nowdate(),
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Draft", "Submitted", "Approved", "Cancelled"],
		}
	],
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		if (column.fieldname == "status") {
			if (value == "Approved") {
				value = `<span class="indicator-pill green">${value}</span>`;
			} else if (value == "Draft") {
				value = `<span class="indicator-pill orange">${value}</span>`;
			} else if (value == "Cancelled") {
				value = `<span class="indicator-pill red">${value}</span>`;
			}
		}
		
		return value;
	}
};
