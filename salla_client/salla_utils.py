import frappe
from frappe import _
import requests


def get_api_settings(feature=None):
    """
    Get API settings if feature is enabled and validate all required fields exist.
    Returns settings dict if successful or None if feature is disabled.
    Raises ValidationError if required settings are missing.
    """
    # Early return if feature is not enabled
    settings = frappe.get_single("Salla Client Settings")
    if feature:
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

    url = f"{settings.server_url}/api/resource/Received Salla Event To Salla"

    return {"url": url, "headers": api_headers, "site": settings.site}


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
            f"Failed to update product balance warehouse: {response.text}",
            "Salla API Error",
        )
        frappe.throw(_("Failed to send data to server. Please check logs."))


## Will be optimized later
def create_or_update_salla_item(doc, merchant_name):
    print("create salla Item ...")
    settings = get_api_settings("create_or_update_salla_item")

    if not settings:
        return

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
            f"Failed to create or update salla item: {response.text}", "Salla API Error"
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
        frappe.log_error(
            f"Failed to update variant qty: {response.text}", "Salla API Error"
        )
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


def update_salla_price(item_price):
    settings = get_api_settings("update_salla_price")

    if not settings:
        return

    data = {
        "site": settings["site"],
        "data": str(item_price),
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
        frappe.log_error(
            f"Failed to update Salla price: {response.text}", "Salla API Error"
        )
        frappe.throw(_("Failed to send data to server. Please check logs."))


def update_item_barcode(doc):
    old_doc = doc.get_doc_before_save()
    if not old_doc or len(doc.barcodes) != len(old_doc.barcodes):
        barcodes_list = [row.barcode for row in doc.barcodes]
        if len(barcodes_list) > 0:
            doc.custom_concatenated_barcode = "#"
            doc.custom_concatenated_barcode += "#".join(barcodes_list)
            doc.custom_concatenated_barcode += "#"


def Update_salla_online_qty(doc):
    for salla_item_info in doc.custom_salla_item:
        update_online_qty(salla_item_info)


def update_online_qty(doc):
    total_online_qty = 0

    if doc.update_online_qty and not doc.parent.is_bundle:
        doc.update_online_qty = 0
        # Check for normal Items
        items = frappe.get_list(
            "Salla Order Item",
            filters=[
                ["is_document_submitted", "=", 0],
                ["merchant", "=", doc.merchant],
                ["order_status", "!=", "ملغي"],
                ["item_code", "=", doc.parent.item_code],
            ],
            fields=["qty"],
        )
        # frappe.msgprint('Non Bunsle items length is : ' + str(len(items)));
        if len(items) > 0:
            for item in items:
                total_online_qty = total_online_qty + item.qty

        # Check for Item in bundles
        bundel_items = frappe.get_list(
            "Salla Order Item",
            filters=[
                ["is_document_submitted", "=", 0],
                ["merchant", "=", doc.merchant],
                ["order_status", "!=", "ملغي"],
                ["is_bundle", "=", 1],
            ],
            fields=["qty", "barcode", "merchant"],
        )
        # frappe.msgprint('bundel_items length is : ' + str(len(bundel_items)));
        if len(bundel_items) > 0:
            for bundel_item in bundel_items:
                # frappe.msgprint('bundle barcode is : '+ bundel_item.barcode);
                # frappe.msgprint('bundle qty is : '+ str(bundel_item.qty));
                # frappe.msgprint('total_online_qty is ' + str(total_online_qty));
                barcodeList = bundel_item.barcode.split("-")
                for barcode in barcodeList:
                    # frappe.msgprint('item barcode is : '+ barcode);
                    # frappe.msgprint('Item to be updated barcode is : '+ doc.barcode);
                    if "#" + barcode + "#" in doc.parent.barcode:
                        # frappe.msgprint('barcode is in doc item');
                        total_online_qty = total_online_qty + bundel_item.qty
                        # frappe.msgprint('total_online_qty is ' + str(total_online_qty));
        doc.pending_online_quantity = total_online_qty
        # frappe.msgprint('total_online_qty is ' + str(total_online_qty));
        # frappe.msgprint('pending_online_quantity is ' + str(doc.pending_online_quantity));


def setup_variant_data(doc, send_to_salla, merchant_name):
    frappe.msgprint("Setting up default data for the variant")
    doc.custom_is_salla_item = 1
    if send_to_salla:
        doc.custom_send_item_to_salla = 1
        add_merchant(doc, merchant_name)
        frappe.msgprint("Merchant and Salla settings applied")

    add_barcode(doc)


def add_merchant(doc, merchant_name):
    if not any(row.merchant == merchant_name for row in doc.custom_salla_item):
        doc.append("custom_salla_item", {"merchant": merchant_name})
        frappe.msgprint(f"Merchant {merchant_name} added to variant.")


def add_barcode(doc):
    barcode_value = doc.item_code
    if not any(barcode.barcode == barcode_value for barcode in doc.barcodes):
        doc.append("barcodes", {"barcode": barcode_value, "custom_is_salla_barcode": 1})
        frappe.msgprint(f"Barcode {barcode_value} added to variant.")


def has_barcode(doc):
    """Checks if a barcode already exists in the item variant."""
    return any(barcode_entry.barcode for barcode_entry in doc.barcodes)
