import frappe
from frappe import _
import requests


def get_api_settings(feature):
    """
    Get API settings if feature is enabled and validate all required fields exist.
    Returns settings dict if successful or None if feature is disabled.
    Raises ValidationError if required settings are missing.
    """
    # Early return if feature is not enabled
    settings = frappe.get_single("Salla Client Settings")
    feature_is_enabled = getattr(settings, feature, 0)
    print(feature_is_enabled)
    if not feature_is_enabled:
        return None

    # Check all required fields
    required_fields = {
        "api_key": "Server API key is required.",
        "api_secret": "Server API secret is required.",
        "server_url": "Server URL is required.",
        "site": "Site name is required.",
    }

    # Validate all required fields exist
    missing_fields = []
    for field, error_msg in required_fields.items():
        if not getattr(settings, field, None):
            missing_fields.append(error_msg)

    # If any required fields are missing, raise a combined validation error
    if missing_fields:
        raise frappe.ValidationError("\n".join(missing_fields))

    # All required fields are present, return settings
    api_headers = {
        "Authorization": f"token {settings.api_key}:{settings.api_secret}",
        "Content-Type": "application/json",
    }
    return {"url": settings.server_url, "headers": api_headers, "site": settings.site}


# Allow Salla Monitor to set Merchants into salla client
@frappe.whitelist()
def set_merchant_data(merchant_data):
    merchant_data = frappe._dict(merchant_data)
    merchant_exists = frappe.db.exists("Salla Merchant", merchant_data.merchant)
    if not merchant_exists:
        merchant = frappe.get_doc({"doctype": "Salla Merchant"})
        merchant.merchant = merchant_data.merchant
        merchant.merchant_name = merchant_data.merchant_name
        merchant.save()

    response = frappe._dict({})
    response.status_code = 200
    response.ok = 1
    response.message = "Set merchant data in salla client"
    return response


# The server will process the data and update client data
@frappe.whitelist()
def update_product_balance_warehouse(merchant_name=None, item=None):
    print("update_product_balance_warehouse ....")
    settings = get_api_settings("update_product_balance_warehouse")
    print(settings)
    if not settings:
        return

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
    print("create salla Item ...")
    settings = get_api_settings("create_or_update_salla_item")

    if not settings:
        return

    minimal_data = {
        "name": doc.name,
        "item_name": doc.item_name,
        "standard_rate": doc.standard_rate,
        "custom_product_type": doc.custom_product_type,
        "description": doc.description,
        "custom_send_item_to_salla": doc.custom_send_item_to_salla,
        "custom_product_image": doc.custom_product_image,
        "variant_of": doc.variant_of,
        "weight_per_unit": doc.weight_per_unit,
        "attributes": (
            [
                {"attribute": attr.attribute, "attribute_value": attr.attribute_value}
                for attr in doc.attributes
            ]
            if hasattr(doc, "attributes")
            else []
        ),
    }

    data = {
        "site": settings["site"],
        "function": "create_or_update_salla_item",
        "data": str({"merchant_name": merchant_name, "doc": minimal_data}),
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
    settings = get_api_settings("update_variant_qty")
    if not settings:
        return
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


# Allows Salla Server to update merchant requests balance
@frappe.whitelist()
def update_merchant_requests(**args):
    args_dict = frappe._dict(args)
    merchant = frappe.get_doc("Salla Merchant", args_dict.merchant)
    last_row = merchant.salla_requests[-1]
    last_row.number_of_requests = args_dict.number_of_requests
    last_row.consumed_requests = args_dict.consumed_requests
    last_row.remaining_requests = args_dict.remaining_requests
    merchant.save()
