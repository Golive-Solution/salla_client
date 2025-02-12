import datetime
import time

from erpnext.stock.doctype.quick_stock_balance.quick_stock_balance import (
    get_stock_item_details,
)
import frappe
import requests

from frappe.utils.data import get_url, getdate, now, now_datetime, today


salla_base_url = "https://api.salla.dev/admin/v2"
receive_event_api_path = "api/method/salla_client.salla_api.receive_event"
update_bulk_url = "/products/quantities/bulkSkus"


def get_default_headers(merchant_settings):
    headers = {
        "Authorization": f"Bearer {merchant_settings.access_token}",
        "Content-Type": "application/json",
    }
    return headers


def subscribe_event(doc_name):
    doc = frappe.get_doc("Salla Store Webhook", doc_name)
    merchant_settings = frappe.get_doc("Salla Settings", doc.merchant)
    headers = get_default_headers(merchant_settings)
    url = get_url() + f"/{receive_event_api_path}"
    data = {"event": doc.event, "url": url, "name": doc.name}
    if doc.version:
        data.update({"version": doc.version})
    if doc.rule:
        data.update({"rule": doc.rule})

    body_headers = []
    salla_user = frappe.get_doc("User", merchant_settings.salla_user)

    body_headers.append(
        {
            "key": "authorization",
            "value": f"token {salla_user.api_key}:{salla_user.get_password('api_secret')}",
        }
    )
    for header in doc.headers:
        body_headers.append({f"{header.key}": f" {header.value}"})

    data.update({"headers": body_headers})
    print(f"data : {data}")
    response = requests.post(
        f"{salla_base_url}/webhooks/subscribe", headers=headers, json=data
    ).json()
    response_message = frappe._dict(response)

    if response_message.status == 200:
        doc.id = response_message.data["id"]
        doc.status = "Active"
        doc.save()
    else:
        comment = f"Failed to subscribe for event {doc.event} ,Status Response Cod:{response_message.status},Error message : {response_message.error['message']}"
        doc.add_comment(comment_type="Comment", text=comment)
        doc.status = "Failed"
        doc.save()


def unsubscribe_event(doc_name):
    doc = frappe.get_doc("Salla Store Webhook", doc_name)
    merchant_settings = frappe.get_doc("Salla Settings", doc.merchant)
    headers = get_default_headers(merchant_settings)
    url = get_url() + f"/{receive_event_api_path}"
    # url = f"https://golive14-stg.frappe.cloud/{doc.url}"#get_url()
    data = {"id": doc.id, "url": url}
    response = requests.delete(
        f"{salla_base_url}/webhooks/unsubscribe", headers=headers, json=data
    ).json()
    response_message = frappe._dict(response)
    print(f"response_message : {response_message}")
    if response_message.status == 202 or response_message.status == 200:
        doc.status = "Inactive"
        doc.save()
    else:
        comment = f"Failed to unsubscribe for event {doc.event} ,Status Response Cod:{response_message.status},Error message : {response_message.error['message']}"
        doc.add_comment(comment_type="Comment", text=comment)
        doc.status = "Failed"
        doc.save()


################################
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


#################################
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


def convert_item_to_salla_item(item):
    return {
        "name": "T-Shirt Blue",
        "price": 96.33,
        "status": "out",
        "product_type": "product",
        "quantity": 4,
        "sku": "23-4324432",
        "images": [
            {
                "original": "https://salla-dev.s3.eu-central-1.amazonaws.com/nWzD/2E0Z2t6Q8FG3ca620rwqcTY2CC2j2PAGrqqeDROY.jpg",
                "thumbnail": "https://salla-dev.s3.eu-central-1.amazonaws.com/nWzD/2E0Z2t6Q8FG3ca620rwqcTY2CC2j2PAGrqqeDROY.jpg",
                "alt": "image",
                "default": 1,
            }
        ],
        "values": [{"name": "كبير", "price": 120, "quantity": 10}],
    }


def refresh_token(merchant_setting):
    current_datetime = now_datetime()
    doc = frappe.get_doc("Salla Settings", merchant_setting)
    salla_sync_token = frappe.get_doc({"doctype": "Salla Sync Token Log"})
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    data = {
        "client_id": doc.get_password("client_id"),
        "client_secret": doc.get_password("client_secret"),
        "refresh_token": doc.refresh_token,
        "grant_type": "refresh_token",
    }
    salla_sync_token.merchant = doc.merchant
    salla_sync_token.sending_time = now()
    salla_sync_token.message = str(data)
    print(f"data : {data}")
    response = requests.post(
        "https://accounts.salla.sa/oauth2/token", headers=headers, data=data
    )
    print(f"response is {response}")
    response_message = frappe._dict(response.json())
    salla_sync_token.response = response_message
    salla_sync_token.save()
    if response.status_code == 200:
        doc.access_token = response_message["access_token"]
        doc.refresh_token = response_message["refresh_token"]
        doc.expires_on = current_datetime + datetime.timedelta(
            seconds=response_message["expires_in"]
        )
        doc.save()
    else:
        print(response_message)
        comment = f"Failed to Refresh Token For The Body {data}, Error Description : {response_message['error_description']} With Status Code : {response.status_code}"
        doc.add_comment(comment_type="Comment", text=comment)
        doc.save()


@frappe.whitelist()
def update_price_using_barcode(item, price, merchant_name):
    doc = frappe.get_doc("Item", item)
    merchant = frappe.get_doc("Salla Settings", merchant_name)
    barcode = frappe.get_doc(
        "Item Barcode", {"parent": doc.name, "custom_is_salla_barcode": 1}
    )
    headers = {
        "Authorization": f"Bearer {merchant.access_token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    data = {"price": price}

    print(f"data : {data}")
    response = requests.post(
        f"https://api.salla.dev/admin/v2/products/sku/{barcode.barcode}/price",
        headers=headers,
        data=data,
    )
    print(f"response is {response}")
    response_message = frappe._dict(response.json())
    if response.status_code == 200:
        return response_message
    else:
        print(response_message)
        return response_message


def update_salla_price(item_price):
    today = getdate()
    if item_price.selling and getdate(item_price.valid_from) == today:
        item = frappe.get_doc("Item", item_price.item_code)
        if item.custom_is_salla_item:
            merchant_salla_setting_list = frappe.get_list(
                "Salla Defaults", filters={"price_list": item_price.price_list}
            )
            print(merchant_salla_setting_list)
            for salla_setting in merchant_salla_setting_list:
                # handle updating price for variant items
                if item.variant_of:
                    update_variant_price(
                        item, item_price.price_list_rate, salla_setting.name
                    )
                else:
                    update_price_using_barcode(
                        item_price.item_code,
                        item_price.price_list_rate,
                        salla_setting.name,
                    )


def add_months(dt, months):
    # Calculate new month and year
    new_month = dt.month + months
    new_year = dt.year + (new_month - 1) // 12
    new_month = (new_month - 1) % 12 + 1

    # Handle days
    day = dt.day
    # Check if the new month has fewer days
    if day > 28:
        # Handle end-of-month cases
        while True:
            try:
                new_dt = datetime(
                    new_year, new_month, day, dt.hour, dt.minute, dt.second
                )
                break
            except ValueError:
                day -= 1
    else:
        new_dt = datetime(new_year, new_month, day, dt.hour, dt.minute, dt.second)

    return new_dt


def update_salla_balance(**args):
    try:
        args_dict = frappe._dict(args)
        merchant = frappe.get_doc("Salla Merchant", args_dict.merchant)

        if len(merchant.salla_requests):
            last_row = merchant.salla_requests[-1]
            last_row.plan_type = args_dict.get("plan_type", last_row.plan_type)
            last_row.number_of_requests = args_dict.get(
                "number_of_requests", last_row.number_of_requests
            )
            last_row.created_on = args_dict.get("created_on", last_row.created_on)
            last_row.valid_from = args_dict.get("valid_from", last_row.valid_from)
            last_row.valid_to = args_dict.get("valid_to", last_row.valid_to)
            last_row.consumed_requests = args_dict.get(
                "consumed_requests", last_row.consumed_requests
            )
            last_row.remaining_requests = args_dict.get(
                "remaining_requests", last_row.remaining_requests
            )
            merchant.save()
        else:
            new_request = {
                "plan_type": args_dict.get("plan_type"),
                "number_of_requests": args_dict.get("number_of_requests"),
                "created_on": args_dict.get("created_on"),
                "valid_from": args_dict.get("valid_from"),
                "valid_to": args_dict.get("valid_to"),
                "consumed_requests": args_dict.get("consumed_requests", 0),
                "remaining_requests": args_dict.get(
                    "remaining_requests", args_dict.get("number_of_requests", 0)
                ),
            }
            merchant.append("salla_requests", new_request)
            merchant.save()
            return set_response_and_message(200, "Success")
    except Exception as e:
        return set_response_and_message(400, e)


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


# Helper functions
def get_product_details(headers, salla_base_url, barcode):
    check_url = f"{salla_base_url}/products/sku/{barcode.barcode}"
    return requests.get(check_url, headers=headers)


def update_item_by_barcode(headers, salla_base_url, barcode, item_data):
    update_url = f"{salla_base_url}/products/sku/{barcode.barcode}"
    return requests.put(update_url, json=item_data, headers=headers)


def add_new_salla_item(headers, salla_base_url, item_data):
    add_url = f"{salla_base_url}/products"
    return requests.post(add_url, json=item_data, headers=headers)


def create_product_option(headers, salla_base_url, product_id, option_data):
    create_product_option_url = f"{salla_base_url}/products/{product_id}/options"
    return requests.post(create_product_option_url, json=option_data, headers=headers)


def create_product_option_value(headers, salla_base_url, option_id, option_data):
    create_product_option_value_url = f"{salla_base_url}/products/options/{option_id}"
    return requests.post(
        create_product_option_value_url, json=option_data, headers=headers
    )


def update_product_variant(headers, salla_base_url, variant, variant_data):
    update_product_variant_url = f"{salla_base_url}/products/variants/{variant}"
    return requests.put(update_product_variant_url, json=variant_data, headers=headers)


def update_product_variant_qty(headers, salla_base_url, variant, variant_data):
    update_product_variant_url = (
        f"{salla_base_url}/products/quantities/variant/{variant}"
    )
    return requests.put(update_product_variant_url, json=variant_data, headers=headers)


def set_response_and_message(statusCode, message):
    frappe.local.response.http_status_code = statusCode
    return message


def acknowlege_merchant_request_details():
    merchant_settings = frappe.get_doc("Salla Store App Authorize")
    if (
        merchant_settings.api_key
        and merchant_settings.api_secret
        and merchant_settings.api_url
    ):
        try:
            merchants = frappe.get_list("Salla Merchant", pluck="name")
            headers = {
                "Authorization": f"token {merchant_settings.api_key}:{merchant_settings.get_password('api_secret')}"
            }

            for merchant_row in merchants:
                merchant = frappe.get_doc("Salla Merchant", merchant_row)
                if len(merchant.salla_requests):
                    last_row = merchant.salla_requests[-1]
                    data = {
                        "merchant": merchant.name,
                        "plan_type": last_row.plan_type,
                        "number_of_requests": last_row.number_of_requests,
                        "created_on": (last_row.created_on).strftime("%Y-%m-%d"),
                        "valid_from": (last_row.valid_from).strftime("%Y-%m-%d"),
                        "valid_to": (last_row.valid_to).strftime("%Y-%m-%d"),
                        "consumed_requests": last_row.consumed_requests,
                        "remaining_requests": last_row.remaining_requests,
                    }
                    requests.post(
                        f"{merchant_settings.api_url}/api/method/salla_store_app_monitor.salla_api.update_merchant_requests",
                        headers=headers,
                        json=data,
                    ).json()
                    send_to_salla(merchant.name, last_row.remaining_requests)
        except Exception as e:
            frappe.utils.logger.set_log_level("DEBUG")
            frappe.logger("test", allow_site=1).info(f"Error is : {e}")


def send_to_salla(merchant, balance):
    merchant_settings = frappe.get_doc("Salla Settings", merchant)

    headers = get_default_headers(merchant_settings)
    data = {"balance": balance}
    try:
        requests.post(
            "https://api.salla.dev/admin/v2/apps/balance", headers=headers, json=data
        )
    except Exception as e:
        frappe.utils.logger.set_log_level("DEBUG")
        frappe.logger("salla_api", allow_site=1).info(f"Error is : {e}")


def update_variant_price(item_variant, price, merchant_name):
    merchant = frappe.get_doc("Salla Settings", merchant_name)
    headers = {
        "Authorization": f"Bearer {merchant.access_token}",
        "Content-Type": "application/json",
    }
    data = {"price": price}
    update_product_variant(
        headers, salla_base_url, item_variant.custom_salla_variant_id, data
    )


#######################
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


###################################
