// Copyright (c) 2025, Alphamonak Solutions

melon.query_reports["Variation Orders Analysis"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: melon.defaults.get_user_default("Company"),
			reqd: 0,
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
			reqd: 0,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: melon.datetime.add_months(melon.datetime.get_today(), -1),
			reqd: 0,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: melon.datetime.get_today(),
			reqd: 0,
		},
		{
			fieldname: "variation_type",
			label: __("Variation Type"),
			fieldtype: "Select",
			options: "\nAddition\nOmission\nSubstitution",
			reqd: 0,
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nDraft\nSubmitted\nApproved\nRejected",
			reqd: 0,
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "status") {
			if (value == "Approved") {
				value = `<span style="color:green">${value}</span>`;
			} else if (value == "Rejected") {
				value = `<span style="color:red">${value}</span>`;
			} else if (value == "Draft") {
				value = `<span style="color:orange">${value}</span>`;
			}
		}

		return value;
	},
};
