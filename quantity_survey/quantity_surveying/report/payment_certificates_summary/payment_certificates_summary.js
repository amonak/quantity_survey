// Copyright (c) 2025, Alphamonak Solutions

melon.query_reports["Payment Certificates Summary"] = {
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
],
};
