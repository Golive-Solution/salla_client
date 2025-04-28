# Copyright (c) 2023, Golive Solutions and contributors
# For license information, please see license.txt

from http.client import HTTPException
import frappe
from frappe import _, msgprint
from frappe.model.document import Document


class SallaOrder(Document):
    pass