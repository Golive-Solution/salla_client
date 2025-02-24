import frappe
from frappe import _
import requests


def get_api_settings():
    settings = frappe.get_single("Salla Client Settings")
    api_headers = {
        "Authorization": f"token {settings.api_key}:{settings.api_secret}",
        "Content-Type": "application/json",
    }
    return {"url": settings.server_url, "headers": api_headers, "site": settings.site}


# The server will process the data and update client data
@frappe.whitelist()
def update_product_balance_warehouse(merchant_name=None, item=None):
    settings = get_api_settings()
    data = {
        "site": settings["site"],
        "function": "update_product_balance_warehouse",
        "data": str({"merchant_name": merchant_name, "item": item}),
    }
    try:

        response = requests.post(
            settings["url"], headers=settings["headers"], json=data
        )

        response.raise_for_status()

        if response.ok:
            frappe.msgprint(_("Sent to server"))

    except requests.exceptions.HTTPError as e:
        frappe.log_error(
            f"Failed to update product balance warehouse: {str(e)}", "Salla API Error"
        )
        frappe.throw(_("Failed to send data to server. Please check logs."))


## Will be optimized later
def create_or_update_salla_item(doc, merchant_name):
    settings = get_api_settings()
    data = {
        "site": settings["site"],
        "function": "create_or_update_salla_item",
        "data": str({"merchant_name": merchant_name, "doc": doc.as_dict()}),
    }

    try:

        response = requests.post(
            settings["url"], headers=settings["headers"], json=data
        )

        response.raise_for_status()

        if response.ok:
            frappe.msgprint(_("Sent to server"))

    except requests.exceptions.HTTPError as e:
        frappe.log_error(
            f"Failed to create or update salla item: {str(e)}", "Salla API Error"
        )
        frappe.throw(_("Failed to send data to server. Please check logs."))


# We need a way to inform the client that the qty is updated on Salla
@frappe.whitelist()
def update_variant_qty(item_variant, merchant_name, salla_item_info_name):
    settings = get_api_settings()
    data = {
        "site": settings["site"],
        "function": "update_variant_qty",
        "data": str(
            {
                "item_variant": item_variant,
                "merchant_name": merchant_name,
                "salla_item_info_name": salla_item_info_name,
            }
        ),
    }

    try:

        response = requests.post(
            settings["url"], headers=settings["headers"], json=data
        )

        response.raise_for_status()

        if response.ok:
            frappe.msgprint(_("Sent to server"))

    except requests.exceptions.HTTPError as e:
        frappe.log_error(f"Failed to update variant qty: {str(e)}", "Salla API Error")
        frappe.throw(_("Failed to send data to server. Please check logs."))
