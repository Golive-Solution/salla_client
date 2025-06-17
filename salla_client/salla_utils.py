import frappe
from frappe import _
import requests
from frappe.utils import getdate, nowdate
from salla_client.utils import serialize_dates, validate_cron_format


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

    return {"url": url, "headers": api_headers, "site": settings.site, "settings": settings}


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
def update_product_balance_warehouse(payload):
    print("update_product_balance_warehouse ....")
    settings = get_api_settings("update_product_balance_warehouse")
    print(settings)
    print(payload)
    if not settings:
        return
    
    if payload.get("is_bulk") and not settings.update_bulk_warehouse_balance:
        return
    
    data = {
        "site": settings["site"],
        "function": "update_product_balance_warehouse",
        "data": str(payload),
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

    doc_data = serialize_dates(doc)

    data = {
        "site": settings["site"],
        "function": "create_or_update_salla_item",
        "data": str({"merchant_name": merchant_name, "doc": doc_data}),
    }

    try:

        response = requests.post(
            settings["url"], headers=settings["headers"], json=data
        )

        response.raise_for_status()

        if response.ok:
            frappe.msgprint(_("Sent to server"))
            frappe.db.set_value("Item", doc_data["name"], "custom_is_synced", 1)
            frappe.db.commit()

    except requests.exceptions.HTTPError as e:
        frappe.log_error(
            f"Failed to create or update salla item: {response.text}", "Salla API Error"
        )
        frappe.throw(_("Failed to send data to server. Please check logs."))


# We need a way to inform the client that the qty is updated on Salla
@frappe.whitelist()
def update_variant_qty(payload):
    settings = get_api_settings("update_variant_qty")

    if not settings:
        return

    serialized_payload = serialize_dates(payload)

    data = {
        "site": settings["site"],
        "function": "update_variant_qty",
        "data": str(serialized_payload),
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

    today = getdate(nowdate())
    valid_from = getdate(args_dict.valid_from)
    valid_to = getdate(args_dict.valid_to)

    last_row = merchant.salla_requests[-1] if merchant.salla_requests else None

    should_add_new_row = True

    if last_row:
        # Convert dates from string to date object if needed
        last_valid_from = getdate(last_row.valid_from)
        last_valid_to = getdate(last_row.valid_to)

        # Check if last row is not expired and has same validity period
        if (
            last_valid_to >= today
            and last_valid_from == valid_from
            and last_valid_to == valid_to
        ):
            should_add_new_row = False

    if should_add_new_row:
        merchant.subscribtion_valid_to = valid_to
        merchant.append(
            "salla_requests",
            {
                "plan_type": args_dict.plan_type,
                "created_on": args_dict.created_on,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "number_of_requests": args_dict.number_of_requests,
                "consumed_requests": args_dict.consumed_requests,
                "salla_orders": args_dict.salla_orders,
                "create_update_items": args_dict.create_update_items,
                "update_balance": args_dict.update_balance,
                "update_item_price": args_dict.update_item_price,
                "bulk_item_balance_update": args_dict.bulk_item_balance_update,
                "remaining_requests": args_dict.remaining_requests,
            },
        )
    else:
        last_row.number_of_requests = args_dict.number_of_requests
        last_row.consumed_requests = args_dict.consumed_requests
        last_row.salla_orders = args_dict.salla_orders
        last_row.create_update_items = args_dict.create_update_items
        last_row.update_balance = args_dict.update_balance
        last_row.update_item_price = args_dict.update_item_price
        last_row.bulk_item_balance_update = args_dict.bulk_item_balance_update
        last_row.remaining_requests = args_dict.remaining_requests

    merchant.save()


def update_salla_price(item_price):
    settings = get_api_settings("update_salla_price")

    if not settings:
        return

    serialized_data = serialize_dates(item_price)

    data = {
        "site": settings["site"],
        "data": str(serialized_data),
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
        update_online_qty(salla_item_info, doc)


def update_online_qty(doc, parent_doc):
    if frappe.db.exists("Salla Defaults", doc.merchant):
        salla_default = frappe.get_doc("Salla Defaults", doc.merchant)
    else:
        frappe.throw(f"Merchant {doc.merchant} Defaults Not Exist.")
    total_online_qty = 0
    if not parent_doc.custom_is_bundle:
        doc.update_online_qty = 0
        # Check for normal Items
        salla_order_items = frappe.get_all(
            "Salla Order Item",
            filters=[
                ["is_document_submitted", "=", 0],
                ["merchant", "=", doc.merchant],
                ["order_status", "!=", "ملغي"],
                ["item_code", "=", parent_doc.item_code],
            ],
            fields=["qty"],
        )
        print(f"salla_order_items: {len(salla_order_items) }")
        if len(salla_order_items) > 0:
            total_online_qty = sum(
                salla_order_item.qty for salla_order_item in salla_order_items
            )
            print(f"Total online qty for normal items: {total_online_qty}")

        # Check for Item in bundles
        bundel_items = frappe.get_all(
            "Salla Order Item",
            filters=[
                ["is_document_submitted", "=", 0],
                ["merchant", "=", doc.merchant],
                ["order_status", "!=", "ملغي"],
                ["is_bundle", "=", 1],
            ],
            fields=["qty", "barcode", "merchant"],
        )
        if len(bundel_items) > 0:
            for bundel_item in bundel_items:
                barcodeList = bundel_item.barcode.split(
                    salla_default.bundle_barcode_separator
                )
                for barcode in barcodeList:
                    if "#" + barcode + "#" in parent_doc.custom_concatenated_barcode:
                        total_online_qty = total_online_qty + bundel_item.qty
        doc.pending_online_quantity = total_online_qty


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


@frappe.whitelist()
def get_update_bulk_data_setting():
    bulk_update_enabled = frappe.get_value(
        "Salla Client Settings", None, "update_product_balance_warehouse"
    )
    salla_items = frappe.get_all(
        "Item",
        filters={"custom_is_salla_item": 1},
        fields=["count(*) as count"],
    )
    cron_format = frappe.get_value(
        "Scheduled Job Type",
        {
            "method": "salla_client.tasks.bulk_update_warehouse_balance.update_warehouse_balance"
        },
        "cron_format",
    )
    return {
        "bulk_update_enabled": bulk_update_enabled,
        "salla_items": salla_items[0].count,
        "cron_format": cron_format,
    }


@frappe.whitelist()
def update_warehouse_balance_cron_format(cron_format):
    """
    Update the cron format for warehouse balance scheduled job with validation
    """
    try:
        # Validate cron format
        validate_cron_format(cron_format)

        # Update the cron format if validation passes
        frappe.db.set_value(
            "Scheduled Job Type",
            "bulk_update_warehouse_balance.update_warehouse_balance",
            "cron_format",
            cron_format,
        )

        frappe.db.commit()

        return {
            "success": True,
            "message": f"Cron format updated successfully to: {cron_format}",
        }

    except Exception as e:
        frappe.log_error(f"Error updating cron format: {str(e)}")
        frappe.throw(f"Failed to update cron format: {str(e)}")
