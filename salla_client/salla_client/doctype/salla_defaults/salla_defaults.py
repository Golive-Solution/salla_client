# Copyright (c) 2025, Golive Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
#from salla_common_lib.event import field_manager

class SallaDefaults(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		bundle_barcode_separator: DF.Data | None
		cod_item: DF.Link | None
		company: DF.Link | None
		customer_group: DF.Link | None
		integration_type: DF.Literal["", "POS Invoice", "Sales Invoice", "Sales Order"]
		merchant: DF.Link
		pos_profile: DF.Link | None
		price_list: DF.Link
		tax_account: DF.Link | None
		tax_description: DF.Data | None
		tax_type: DF.Literal["Actual", "On Net Total", "On Previous Row Amount", "On Previous Row Total", "On Item Quantity"]
		taxe_included_in_basic_rate: DF.Check
		territory: DF.Link | None
	# end: auto-generated types

	def validate(self):
		if self.pos_profile and self.taxe_included_in_basic_rate:
			taxes_and_charges = frappe.get_value("POS Profile", self.pos_profile, "taxes_and_charges")
			if not taxes_and_charges:
				frappe.throw("Taxes and Charges are not set in the selected POS Profile, but 'Tax Included in Basic Rate' is enabled.")

			taxes_doc = frappe.get_doc("Sales Taxes and Charges Template", taxes_and_charges)
			if len(taxes_doc.taxes):
				first_item = taxes_doc.taxes[0]
				if not first_item.included_in_print_rate:
					frappe.throw(
						f"The first tax in the template '{taxes_and_charges}' is not marked as 'Is this Tax included in Basic Rate?', "
						"but 'Tax Included in Basic Rate' is enabled. Please update the tax template or disable the setting."
					)
	# @frappe.whitelist()
	# def manage_custom_fields(self):
	# 	return field_manager.manage_custom_fields(self)	

