# Copyright (c) 2025, Golive-Solutions and contributors
# For license information, please see license.txt

# import frappe
from salla_client.utils import get_last_subscription
from frappe.model.document import Document


class SallaMerchant(Document):
	def before_save(self):
		last_subscription = get_last_subscription(self.salla_requests)
		if last_subscription and self.subscription_valid_to != last_subscription.valid_to:
			self.subscription_valid_to = last_subscription.valid_to
