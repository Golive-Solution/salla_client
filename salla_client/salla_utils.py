from erpnext.stock.doctype.quick_stock_balance.quick_stock_balance import (
    get_stock_item_details,
)
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


salla_base_url = "https://api.salla.dev/admin/v2"
receive_event_api_path = "api/method/salla_client.salla_api.receive_event"
update_bulk_url = "/products/quantities/bulkSkus"


def get_default_headers(merchant_settings):
    headers = {
        "Authorization": f"Bearer {merchant_settings.access_token}",
        "Content-Type": "application/json",
    }
    return headers


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


def create_or_update_salla_item(doc, merchant_name):
    merchant = frappe.get_doc("Salla Settings", merchant_name)
    barcode = frappe.get_doc(
        "Item Barcode", {"parent": doc.name, "custom_is_salla_barcode": 1}
    )
    salla_base_url = "https://api.salla.dev/admin/v2"
    headers = {
        "Authorization": f"Bearer {merchant.access_token}",
        "Content-Type": "application/json",
    }
    item_data = {
        "name": doc.item_name,
        "price": doc.standard_rate,
        "sku": barcode.barcode,
        "product_type": doc.custom_product_type,
        "description": f"<strong>{doc.description}</strong>",
    }

    # Check if the item should be sent to Salla
    if not doc.custom_send_item_to_salla:
        return

    # Handle variant case
    if doc.variant_of:
        temp_doc = frappe.get_doc("Item", doc.variant_of)
        temp_barcode = frappe.get_doc(
            "Item Barcode", {"parent": temp_doc.name, "custom_is_salla_barcode": 1}
        )
        temp_product_details = get_product_details(
            headers, salla_base_url, temp_barcode
        ).json()
        temp_product_id = temp_product_details.get("data", {}).get("id")
        temp_options = temp_product_details.get("data", {}).get("options", [])

        values_id = []
        is_second_attribute = 0

        # Process attributes for option and value handling
        for attribute in doc.attributes:
            option = next(
                (opt for opt in temp_options if opt.get("name") == attribute.attribute),
                None,
            )
            if option:
                value = next(
                    (
                        val
                        for val in option.get("values")
                        if val.get("name") == attribute.attribute_value
                    ),
                    None,
                )
                if value:
                    values_id.append(value.get("id"))
                else:
                    # Create missing value
                    value_data = {"name": attribute.attribute_value}
                    response = create_product_option_value(
                        headers, salla_base_url, option.get("id"), value_data
                    )
                    if response.status_code == 201:
                        frappe.msgprint(
                            f"Value {attribute.attribute_value} added successfully"
                        )
                        values_data = response.json().get("data", {})
                        for val_data in values_data:
                            values_id.append(val_data.get("id"))

                    else:
                        frappe.throw(
                            f"Failed to add value {attribute.attribute_value}."
                        )
            else:
                # Create option if not found (up to 2 options)
                if is_second_attribute < 2:
                    option_data = {
                        "name": attribute.attribute,
                        "type": "radio",
                        "values": [{"name": attribute.attribute_value}],
                    }
                    response = create_product_option(
                        headers, salla_base_url, temp_product_id, option_data
                    )
                    if response.status_code == 201:
                        frappe.msgprint(
                            f"Option {attribute.attribute} created successfully"
                        )
                        is_second_attribute += 1
                    else:
                        frappe.msgprint("Failed to create option.")
                        continue

        # Set or update the variant ID
        if doc.custom_salla_variant_id:
            variant_data = {"sku": barcode.barcode, "weight": doc.weight_per_unit}
            update_response = update_product_variant(
                headers, salla_base_url, doc.custom_salla_variant_id, variant_data
            )
            if update_response.status_code == 201:
                frappe.msgprint("Variant updated successfully.")
            else:
                frappe.throw("Failed to update item variant.")
        else:
            # Check for variant by option values
            temp_product_details = get_product_details(
                headers, salla_base_url, temp_barcode
            ).json()
            for sku in temp_product_details.get("data", {}).get("skus", []):
                if set(sku.get("related_option_values", [])) == set(values_id):
                    doc.custom_salla_variant_id = sku.get("id")
                    doc.save()
                    frappe.db.set_value(
                        "Item", doc.name, "custom_salla_variant_id", sku.get("id")
                    )
                    frappe.db.commit()
                    doc.reload()
                    break

    else:
        # Non-variant case
        response = get_product_details(headers, salla_base_url, barcode)
        if response.status_code == 200:
            frappe.msgprint("Item already exists.")
            if (
                update_item_by_barcode(
                    headers, salla_base_url, barcode, item_data
                ).status_code
                == 201
            ):
                frappe.msgprint("Item updated successfully.")
            else:
                frappe.throw("Failed to update item.")
        else:
            frappe.msgprint("Item not found. Adding new item.")
            item_data["images"] = [{"original": doc.custom_product_image}]
            add_response = add_new_salla_item(headers, salla_base_url, item_data)
            if add_response.status_code == 201:
                frappe.msgprint("New item created successfully.")
            else:
                frappe.throw(f"Failed to create new item. {add_response.reason}")


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
