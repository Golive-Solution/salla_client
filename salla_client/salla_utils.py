import datetime
import time

from erpnext.stock.doctype.quick_stock_balance.quick_stock_balance import (
    get_stock_item_details,
)
import frappe
import requests

from frappe.utils.data import getdate, now_datetime, today


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


@frappe.whitelist()
def update_product_balance_warehouse(merchant_name=None, item=None):
    filters = {}
    if merchant_name:
        filters.update({"name": merchant_name})
    merchant_list = frappe.get_all(
        "Salla Merchant", filters=filters, fields=["name", "merchant_name"]
    )

    for merchant in merchant_list:
        salla_setting = frappe.get_doc("Salla Settings", merchant.name)
        if not salla_setting.update_product_balance:
            continue
        salla_job_setting = frappe.get_doc(
            "Salla Sync Job", f"{merchant.name}-{merchant.merchant_name}"
        )
        if salla_job_setting:
            filters = [
                {"merchant": merchant.name, "last_update": ("<", today())},
                {"merchant": merchant.name, "last_update": ("IS", "NULL")},
            ]
            if item:
                filters.append({"parent": item})
            merchant_item_info_list = frappe.get_all(
                "Salla Item Info",
                filters=filters,
                fields=[
                    "name",
                    "pending_online_quantity",
                    "parent",
                    "is_unlimited_qty",
                ],
                limit_page_length=salla_job_setting.product_balance_products_limit_per_request,
            )
            print(merchant_item_info_list)
            skus = []
            merchant_item_info_names = []
            for merchant_item_info in merchant_item_info_list:
                warehouse_balance = 0
                if salla_job_setting.warehouse:
                    warehouse_balance = get_stock_item_details(
                        salla_job_setting.warehouse,
                        frappe.utils.now(),
                        merchant_item_info.parent,
                    )
                salla_product_sku = frappe.get_value(
                    "Item Barcode",
                    filters={
                        "parent": merchant_item_info.parent,
                        "custom_is_salla_barcode": 1,
                    },
                    fieldname="barcode",
                )
                if salla_product_sku:
                    product_balance = (
                        warehouse_balance["qty"]
                        - merchant_item_info["pending_online_quantity"]
                    )
                    is_unlimited = False
                    if merchant_item_info["is_unlimited_qty"]:
                        is_unlimited = True
                    skus.append(
                        {
                            "sku": salla_product_sku,
                            "quantity": product_balance,
                            "unlimited_quantity": is_unlimited,
                        }
                    )
                merchant_item_info_names.append(merchant_item_info.name)
            if len(skus) > 0:
                update_bulk_quantite(skus, merchant)
            if len(merchant_item_info_names) > 0:
                bulk_update_merchant_item_info(merchant_item_info_names)
            time.sleep(salla_job_setting.product_balance_sending_interval)


def bulk_update_merchant_item_info(merchant_item_info_names):
    condition = ",".join([f"'{info_name}'" for info_name in merchant_item_info_names])
    today = datetime.datetime.today().date()
    query = f"""
        UPDATE `tabSalla Item Info`
        SET last_update = '{today}'
        WHERE name in ({condition})
    """
    frappe.db.sql(query)


def update_bulk_quantite(skus, merchant):
    merchant_settings = frappe.get_doc("Salla Settings", merchant.name)
    headers = get_default_headers(merchant_settings)
    data = {"skus": skus}
    sync_job_log = frappe.new_doc("Salla Sync Job Log")
    sync_job_log.merchant = merchant.name
    sync_job_log.job = "Product Balance"
    sync_job_log.sending_time = now_datetime()
    sync_job_log.message = str(data)

    try:
        response = requests.post(
            f"{salla_base_url}/{update_bulk_url}", headers=headers, json=data
        ).json()
        response_message = frappe._dict(response)
        sync_job_log.response = str(response_message)
    except Exception as e:
        sync_job_log.response = str(e)
    sync_job_log.save()


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


@frappe.whitelist()
def update_variant_qty(item_variant, merchant_name, salla_item_info_name):
    item = frappe.get_doc("Item", item_variant)
    merchant = frappe.get_doc("Salla Settings", merchant_name)

    if not merchant.update_product_balance:
        return

    if not frappe.db.exists(
        "Salla Sync Job", f"{merchant.name}-{merchant.merchant_name}"
    ):
        frappe.throw("You Have To Put Warehouse In Salla Sync Job")

    salla_job_setting = frappe.get_doc(
        "Salla Sync Job", f"{merchant.name}-{merchant.merchant_name}"
    )
    headers = {
        "Authorization": f"Bearer {merchant.access_token}",
        "Content-Type": "application/json",
    }
    qty = 0
    warehouse_balance = 0
    if salla_job_setting.warehouse:
        warehouse_balance = get_stock_item_details(
            salla_job_setting.warehouse, frappe.utils.now(), item_variant
        )

    salla_item_info = frappe.get_doc("Salla Item Info", salla_item_info_name)
    qty = warehouse_balance["qty"] - salla_item_info.pending_online_quantity

    data = {"quantity": qty}
    update_product_variant_qty(
        headers, salla_base_url, item.custom_salla_variant_id, data
    )
