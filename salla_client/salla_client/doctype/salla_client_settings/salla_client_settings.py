# Copyright (c) 2025, Golive-Solutions and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SallaClientSettings(Document):
    def validate(self):
        self.fix_url()

    def fix_url(self):
        if self.server_url:
            self.server_url = self.server_url.strip().rstrip("/")
