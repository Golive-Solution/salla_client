import frappe
from frappe import _
import requests
from salla_client.salla_utils import get_api_settings


def before_save(doc, method):
    update_salla_price(doc)


def update_salla_price(item_price):
    settings = get_api_settings()

    data = {
        "site": settings["site"],
        "data": str(item_price.as_dict()),
        "function": "update_salla_price",
    }
    try:

        response = requests.post(
            settings["url"], headers=settings["headers"], json=data
        )

        response.raise_for_status()

        if response.ok:
            frappe.msgprint(_("Sent to server"))

    except requests.exceptions.HTTPError as e:
        frappe.log_error(f"Failed to update Salla price: {str(e)}", "Salla API Error")
        frappe.throw(_("Failed to send data to server. Please check logs."))
