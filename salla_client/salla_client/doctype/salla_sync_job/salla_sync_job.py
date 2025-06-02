# Copyright (c) 2025, Golive Solutions and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class SallaSyncJob(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		merchant: DF.Link | None
		merchant_name: DF.Data | None
		product_balance_products_limit_per_request: DF.Int
		product_balance_sending_interval: DF.Int
		url: DF.Data | None
		warehouse: DF.Link
	# end: auto-generated types
	pass
