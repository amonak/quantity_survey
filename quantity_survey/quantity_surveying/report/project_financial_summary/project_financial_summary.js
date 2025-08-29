// Copyright (c) 2025, Alphamonak Solutions
/* eslint-disable */

melon.query_reports["Project Financial Summary"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: melon.defaults.get_user_default("Company"),
		},
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
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "project_status",
			label: __("Project Status"),
			fieldtype: "Select",
			options: ["", "Open", "Completed", "Cancelled"],
		},
	],
};
