# Copyright (c) 2025, Alphamonak Solutions

from melon import _


def get_data():
	return {
		"fieldname": "quantity_survey",
		"transactions": [
			{
				"label": _("BoQ and Valuation"),
				"items": ["BoQ", "Valuation", "BoQ Item", "Valuation Item"]
			},
			{
				"label": _("Variations and Changes"),
				"items": ["Variation Order", "Variation Order Item"]
			},
			{
				"label": _("Certificates and Payments"),
				"items": ["Payment Certificate", "Final Account"]
			},
			{
				"label": _("Planning and Tendering"),
				"items": ["Cost Plan", "Tender Package", "Tender Quote"]
			},
			{
				"label": _("Settings"),
				"items": ["Quantity Survey Settings"]
			},
			{
				"label": _("Reports"),
				"items": ["BoQ Summary", "Valuation Sheet", "Variation Log", "Cost vs Actual", "Progress Summary", "Retention Report", "Payment Summary"]
			}
		]
	}
