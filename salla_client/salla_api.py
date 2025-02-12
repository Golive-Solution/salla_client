import frappe
from frappe import _
from frappe.utils import now_datetime

from datetime import datetime, timedelta

from salla_client.salla_utils import (
    add_months,
    subscribe_event,
    unsubscribe_event,
    update_product_balance_warehouse,
    update_salla_balance,
)


@frappe.whitelist(methods=["POST"])
def receive_event(**args):
    args_dict = frappe._dict(args)
    merchant_exists = frappe.db.exists("Salla Merchant", args_dict.merchant)
    merchant_settings_exists = frappe.db.exists("Salla Settings", args_dict.merchant)
    if merchant_settings_exists and merchant_exists:
        merchant = frappe.get_doc("Salla Merchant", args_dict.merchant)
        if len(merchant.salla_requests):
            last_row = merchant.salla_requests[-1]
            merchant_settings = frappe.get_doc("Salla Settings", args_dict.merchant)
            now = datetime.now()
            grace_period_end = last_row.valid_to + timedelta(
                days=merchant_settings.grace_period
            )

            if last_row.remaining_requests > 0 or now <= grace_period_end:
                received_events = frappe.get_doc({"doctype": "Salla Received Events"})
                received_events.payload = str(args)
                received_events.received_on = now_datetime()
                # received_events.created_at = args_dict.created_at
                received_events.merchant = args_dict.merchant
                received_events.event = args_dict.event

                date_string = args_dict.created_at[:-5]
                original_format = "%a %b %d %Y %H:%M:%S %Z"
                # Parse the original string into a datetime object
                datetime_obj = datetime.strptime(date_string, original_format)
                # Desired output format
                desired_format = "%Y-%m-%d %H:%M:%S"
                # Convert the datetime object to the desired format
                received_events.created_at = datetime_obj.strftime(desired_format)

                received_events.save()


@frappe.whitelist()
def set_merchant_auth_data(auth_data):
    auth_data_dict = frappe._dict(auth_data)
    merchant_exists = frappe.db.exists("Salla Merchant", auth_data_dict.merchant)
    if not merchant_exists:
        merchant = frappe.get_doc({"doctype": "Salla Merchant"})
        merchant.merchant = auth_data_dict.merchant
        merchant.merchant_name = auth_data_dict.merchant_name
        merchant.save()

    salla_setting = None
    setting_name = frappe.get_value(
        "Salla Settings",
        filters={"merchant": auth_data_dict.merchant},
        fieldname="name",
    )

    if setting_name:
        salla_settings_exists = frappe.db.exists("Salla Settings", setting_name)
        if salla_settings_exists:
            salla_setting = frappe.get_doc("Salla Settings", setting_name)
        else:
            salla_setting = frappe.get_doc({"doctype": "Salla Settings"})
            salla_setting.merchant = auth_data_dict.merchant
    else:
        salla_setting = frappe.get_doc({"doctype": "Salla Settings"})
        salla_setting.merchant = auth_data_dict.merchant

    salla_setting.access_token = auth_data_dict.access_token
    salla_setting.refresh_token = auth_data_dict.refresh_token
    salla_setting.token_type = auth_data_dict.token_type
    salla_setting.expires_on = auth_data_dict.expires_on
    salla_setting.client_id = auth_data_dict.client_id
    salla_setting.client_secret = auth_data_dict.client_secret
    salla_setting.no_of_requests = auth_data_dict.no_of_requests
    salla_setting.save()
    response = frappe._dict({})
    response.status_code = 200
    response.ok = 1
    return response


@frappe.whitelist()
def event_subscribe(doc_name):
    subscribe_event(doc_name)


@frappe.whitelist()
def event_unsubscribe(doc_name):
    unsubscribe_event(doc_name)


@frappe.whitelist()
def update_products_balance():
    update_product_balance_warehouse()


@frappe.whitelist()
def update_salla_requests_balance(**args):
    update_salla_balance(**args)
