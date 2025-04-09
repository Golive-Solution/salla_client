import frappe
from datetime import datetime, timedelta


# def update_merchants_request():
#     merchants = frappe.get_list("Salla Merchant", pluck="name")

#     for merchant_name in merchants:
#         merchant = frappe.get_doc("Salla Merchant", merchant_name)

#         now = datetime.now()

#         if len(merchant.salla_requests):
#             last_request = merchant.salla_requests[-1]
#             if now > last_request.valid_to:
#                 last_request.number_of_requests = 0
#                 merchant.is_active = 0
#                 merchant.save()
#                 continue

#             if last_request.number_of_requests:
#                 merchant.is_active = 1

#                 yesterday_midnight = (now - timedelta(days=1)).replace(
#                     hour=0, minute=0, second=0, microsecond=0
#                 )
#                 yesterday_end_of_day = (now - timedelta(days=1)).replace(
#                     hour=23, minute=59, second=59, microsecond=0
#                 )

#                 yesterday_midnight_str = yesterday_midnight.strftime(
#                     "%Y-%m-%d %H:%M:%S"
#                 )
#                 yesterday_end_of_day_str = yesterday_end_of_day.strftime(
#                     "%Y-%m-%d %H:%M:%S"
#                 )

#                 merchant_requests = frappe.get_list(
#                     "Salla Order",
#                     filters=[
#                         ["merchant", "=", merchant_name],
#                         ["creation", ">=", yesterday_midnight_str],
#                         ["creation", "<=", yesterday_end_of_day_str],
#                         ["creation", ">=", last_request.valid_from],
#                         ["creation", "<=", last_request.valid_to],
#                     ],
#                 )
#                 last_request.remaining_requests -= len(merchant_requests)
#                 last_request.consumed_requests += len(merchant_requests)
#                 merchant.save()
#             else:
#                 merchant.is_active = 0
#                 merchant.save()


## Will add Another background task to send all the updated merchants data to the server `sync_merchants_requests_details`

# def sync_merchants_requests_details():
#     merchant_settings = frappe.get_doc("Salla Store App Authorize")
#     if (
#         merchant_settings.api_key
#         and merchant_settings.api_secret
#         and merchant_settings.api_url
#     ):
#         try:
#             merchants = frappe.get_list("Salla Merchant", pluck="name")
#             headers = {
#                 "Authorization": f"token {merchant_settings.api_key}:{merchant_settings.get_password('api_secret')}"
#             }

#             for merchant_row in merchants:
#                 merchant = frappe.get_doc("Salla Merchant", merchant_row)
#                 if len(merchant.salla_requests):
#                     last_row = merchant.salla_requests[-1]
#                     data = {
#                         "merchant": merchant.name,
#                         "plan_type": last_row.plan_type,
#                         "number_of_requests": last_row.number_of_requests,
#                         "created_on": (last_row.created_on).strftime("%Y-%m-%d"),
#                         "valid_from": (last_row.valid_from).strftime("%Y-%m-%d"),
#                         "valid_to": (last_row.valid_to).strftime("%Y-%m-%d"),
#                         "consumed_requests": last_row.consumed_requests,
#                         "remaining_requests": last_row.remaining_requests,
#                     }
#                     requests.post(
#                         f"{merchant_settings.api_url}/api/method/salla_store_app_monitor.salla_api.update_merchant_requests",
#                         headers=headers,
#                         json=data,
#                     ).json()
#                     send_to_salla(merchant.name, last_row.remaining_requests)
#         except Exception as e:
#             frappe.utils.logger.set_log_level("DEBUG")
#             frappe.logger("test", allow_site=1).info(f"Error is : {e}")


# def send_to_salla(merchant, balance):
#     merchant_settings = frappe.get_doc("Salla Settings", merchant)

#     headers = get_default_headers(merchant_settings)
#     data = {"balance": balance}
#     try:
#         requests.post(
#             "https://api.salla.dev/admin/v2/apps/balance", headers=headers, json=data
#         )
#     except Exception as e:
#         frappe.utils.logger.set_log_level("DEBUG")
#         frappe.logger("salla_api", allow_site=1).info(f"Error is : {e}")
