# Copyright (c) 2025, Golive Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SallaDefaults(Document):
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


