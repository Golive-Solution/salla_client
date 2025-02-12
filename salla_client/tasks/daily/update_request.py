import frappe
from datetime import datetime, timedelta

from salla_client.salla_utils import acknowlege_merchant_request_details


##################################
def update_merchants_request():
    merchants = frappe.get_list("Salla Merchant", pluck="name")

    for merchant_name in merchants:
        merchant = frappe.get_doc("Salla Merchant", merchant_name)

        now = datetime.now()

        if len(merchant.salla_requests):
            last_request = merchant.salla_requests[-1]
            if now > last_request.valid_to:
                last_request.number_of_requests = 0
                merchant.is_active = 0
                merchant.save()
                continue

            if last_request.number_of_requests:
                merchant.is_active = 1

                yesterday_midnight = (now - timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                yesterday_end_of_day = (now - timedelta(days=1)).replace(
                    hour=23, minute=59, second=59, microsecond=0
                )

                yesterday_midnight_str = yesterday_midnight.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                yesterday_end_of_day_str = yesterday_end_of_day.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                merchant_requests = frappe.get_list(
                    "Salla Order",
                    filters=[
                        ["merchant", "=", merchant_name],
                        ["creation", ">=", yesterday_midnight_str],
                        ["creation", "<=", yesterday_end_of_day_str],
                        ["creation", ">=", last_request.valid_from],
                        ["creation", "<=", last_request.valid_to],
                    ],
                )
                last_request.remaining_requests -= len(merchant_requests)
                last_request.consumed_requests += len(merchant_requests)
                merchant.save()
            else:
                merchant.is_active = 0
                merchant.save()


def update_to_salla_monitor():
    acknowlege_merchant_request_details()


###############################################
