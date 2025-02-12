import ast
import json
import frappe
from frappe.utils.data import get_datetime


def check_key_value_exists(data, key_path):
    """
    Checks if a key exists in a nested dictionary and its value is not None.

    Args:
        data: The nested dictionary to search.
        key_path: A list representing the path to the key (e.g., ["outer_key", "inner_key"])

    Returns:
        True if the key exists and its value is not None, False otherwise.
    """
    if len(key_path) == 1:
        # Base case: Check for key in the current dictionary
        return key_path[0] in data and data[key_path[0]] is not None
    else:
        # Recursive case: Check if the first key exists and is a dictionary
        if key_path[0] in data and isinstance(data[key_path[0]], dict):
            return check_key_value_exists(data[key_path[0]], key_path[1:])
        else:
            return False


@frappe.whitelist(allow_guest=True)
def received_events_salla_order():
    frappe.utils.logger.set_log_level("DEBUG")
    logger = frappe.logger("recived-event", allow_site=1)
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    order_event_list = [ORDER_CREATED, ORDER_UPDATED]

    SHIPMENT_CREATING = "shipment.creating"
    SHIPMENT_CREATED = "shipment.created"
    SHIPMENT_CANCELLED = "shipment.cancelled"
    SHIPMENT_UPDATED = "shipment.updated"
    shipment_event_list = [
        SHIPMENT_CREATING,
        SHIPMENT_CREATED,
        SHIPMENT_CANCELLED,
        SHIPMENT_UPDATED,
    ]

    event_list = order_event_list + shipment_event_list
    recived_events = frappe.get_list(
        "Salla Received Events",
        filters=[["event", "in", event_list], ["status", "=", "Pending"]],
        order_by="received_on",
    )
    for received in recived_events:
        try:
            logger.info(f"event is {received}")

            received_event_doc = frappe.get_doc("Salla Received Events", received)
            merchant_settings = frappe.get_doc(
                "Salla Settings", received_event_doc.merchant
            )
            merchant_data = frappe.get_doc(
                "Salla Merchant", received_event_doc.merchant
            )
            if int(merchant_data.is_active):
                received_event_payload = received_event_doc.payload

                # double_quote_payload = received_event_payload.replace("'", "\"").replace('False','false').replace('True','true').replace("None","null")
                received_event = frappe._dict(
                    safely_convert_payload(received_event_payload)
                )

                # Iterate over dictionary items and replace values
                for key, value in received_event.items():
                    if value is None:
                        received_event[key] = None  # Keep None values unchanged
                # Add more conditions for other data types or specific values if needed
                # Handle different shipment events
                if received_event_doc.event in order_event_list:
                    logger.info(
                        f"Got Into Handle Order Created : {received_event_doc.event}"
                    )
                    handling_order_event(received_event, received_event_doc, logger)
                elif received_event_doc.event in shipment_event_list:
                    handle_shipment_event(received_event, received_event_doc)

                received_event_doc.status = "Completed"
                received_event_doc.save()
        except Exception as e:
            logger.info(f"Error Occur : {e}")
            received_event_doc.add_comment("Comment", text=str(e))
            received_event_doc.status = "Failed"
            received_event_doc.save()


def handling_order_event(received_event, received_event_doc, logger):
    logger.info(f"Got Into Handle Orders Events")

    salla_order = None
    if frappe.db.exists("Salla Order", received_event.data["reference_id"]):
        salla_order = frappe.get_doc("Salla Order", received_event.data["reference_id"])
    else:
        salla_order = frappe.get_doc({"doctype": "Salla Order"})

    salla_order.merchant = received_event["merchant"]
    if check_key_value_exists(
        received_event.data, ["amounts", "cash_on_delivery", "amount"]
    ):
        salla_order.cod_cost = received_event.data["amounts"]["cash_on_delivery"][
            "amount"
        ]
    if check_key_value_exists(
        received_event.data, ["amounts", "shipping_cost", "amount"]
    ):
        salla_order.shipping_cost = (
            0
            if received_event.data["amounts"]["shipping_cost"]["amount"] < 0
            else received_event.data["amounts"]["shipping_cost"]["amount"]
        )
    if check_key_value_exists(
        received_event.data, ["amounts", "tax", "amount", "amount"]
    ):
        salla_order.total_tax = received_event.data["amounts"]["tax"]["amount"][
            "amount"
        ]
    if check_key_value_exists(received_event.data, ["amounts", "total"]):
        salla_order.grand_total = received_event.data["amounts"]["total"]["amount"]
    if check_key_value_exists(received_event.data, ["customer", "city"]):
        salla_order.customer_city = received_event.data["customer"]["city"]
    if check_key_value_exists(received_event.data, ["customer", "country"]):
        salla_order.customer_country = received_event.data["customer"]["country"]
    if check_key_value_exists(received_event.data, ["customer", "email"]):
        salla_order.customer_email = received_event.data["customer"]["email"]
    if check_key_value_exists(received_event.data, ["customer", "first_name"]):
        salla_order.customer_first_name = received_event.data["customer"]["first_name"]
    if check_key_value_exists(received_event.data, ["customer", "last_name"]):
        salla_order.customer_last_name = received_event.data["customer"]["last_name"]
    if check_key_value_exists(received_event.data, ["customer", "mobile"]):
        salla_order.phone_number = str(received_event.data["customer"]["mobile"])
    if check_key_value_exists(received_event.data, ["customer", "currency"]):
        salla_order.customer_currency = received_event.data["customer"]["currency"]
    if check_key_value_exists(received_event.data, ["date", "date"]):
        salla_order.date = get_datetime(received_event.data["date"]["date"])
    if check_key_value_exists(received_event.data, ["status", "name"]):
        salla_order.order_status = received_event.data["status"]["name"]
    if check_key_value_exists(received_event.data, ["status", "customized", "name"]):
        salla_order.custom_status = received_event.data["status"]["customized"]["name"]
    if check_key_value_exists(received_event.data, ["reference_id"]):
        salla_order.salla_order_no = received_event.data["reference_id"]
    if check_key_value_exists(received_event.data, ["payment_method"]):
        salla_order.salla_payment_method = received_event.data["payment_method"]
    if check_key_value_exists(received_event.data, ["currency"]):
        salla_order.currency = received_event.data["currency"]
    if check_key_value_exists(received_event.data, ["shipping", "company"]):
        salla_order.salla_shipping_method = received_event.data["shipping"]["company"]
    if check_key_value_exists(received_event.data, ["bank", "id"]):
        salla_order.bank_reference = received_event.data["bank"]["id"]

    new_items = []
    logger.info(f"salla order Before But the items is {salla_order}")

    logger.info(f"The Items is {received_event.data['items']}")

    for item in received_event.data["items"]:
        salla_order_item = None
        if frappe.db.exists("Salla Order Item", item["id"]):
            salla_order_item = frappe.get_doc("Salla Order Item", item["id"])
        else:
            salla_order_item = frappe.get_doc({"doctype": "Salla Order Item"})

        if check_key_value_exists(item, ["sku"]):
            salla_order_item.barcode = item["sku"]
        if check_key_value_exists(item, ["quantity"]):
            salla_order_item.qty = item["quantity"]
        if check_key_value_exists(item, ["amounts", "price_without_tax", "amount"]):
            salla_order_item.rate = item["amounts"]["price_without_tax"]["amount"]
        if check_key_value_exists(item, ["amounts", "total_discount", "amount"]):
            salla_order_item.discount_amount = (
                item["amounts"]["total_discount"]["amount"] / item["quantity"]
                if item["quantity"] != 0
                else 0
            )
        if check_key_value_exists(item, ["name"]):
            salla_order_item.salla_item_name = item["name"]
        if check_key_value_exists(item, ["id"]):
            salla_order_item.salla_item_id = item["id"]

        new_items.append(salla_order_item)

    # Clear existing items and add new ones in the correct order
    salla_order.items = []
    for item in new_items:
        logger.info(f"The item is {item}")
        salla_order.append("items", item)

    salla_order.received_event = received_event_doc.name
    try:
        salla_order.save()
    except Exception as e:
        logger.info(f"Error On Save : {e}")


def handle_shipment_event(received_event, received_event_doc):
    salla_order = None
    order_reference_id = received_event.data["order_reference_id"]
    if frappe.db.exists("Salla Order", order_reference_id):
        salla_order = frappe.get_doc("Salla Order", order_reference_id)
    else:
        frappe.throw(f"Failed to find order with reference ID: {order_reference_id}")

    if not check_key_value_exists(received_event.data, ["id"]):
        frappe.throw("Missing shipment ID")

    shipment_id = received_event.data["id"]
    if frappe.db.exists("Salla Order Shipment Details", shipment_id):
        salla_order_shipment = frappe.get_doc(
            "Salla Order Shipment Details", shipment_id
        )
    else:
        salla_order_shipment = frappe.get_doc(
            {"doctype": "Salla Order Shipment Details"}
        )

    salla_order_shipment.shipment_id = shipment_id
    if check_key_value_exists(received_event.data, ["tracking_number"]):
        salla_order_shipment.tracking_number = received_event.data["tracking_number"]
    if check_key_value_exists(received_event.data, ["tracking_link"]):
        salla_order_shipment.tracking_link = received_event.data["tracking_link"]
    if check_key_value_exists(received_event.data, ["label", "url"]):
        salla_order_shipment.lable_url = received_event.data["label"]["url"]
    if check_key_value_exists(received_event.data, ["status"]):
        salla_order_shipment.status = received_event.data["status"]

    salla_order.append("shipment_detials", salla_order_shipment)
    salla_order.received_event = received_event_doc.name
    salla_order.save()


def safely_convert_payload(payload):
    try:
        # Attempt to use ast.literal_eval to safely evaluate the payload
        received_event = ast.literal_eval(payload)
    except ValueError:
        # If there's an error with ast.literal_eval, fall back to replacing quotes cautiously
        # Convert to a valid JSON string by escaping inner single quotes
        payload = (
            payload.replace("False", "false")
            .replace("True", "true")
            .replace("None", "null")
        )
        double_quote_payload = ""
        in_string = False
        escape_next = False

        for char in payload:
            if char == "'" and not escape_next:
                if in_string:
                    double_quote_payload += '"'
                    in_string = False
                else:
                    double_quote_payload += '"'
                    in_string = True
            elif char == '"' and not escape_next:
                double_quote_payload += '\\"' if in_string else '"'
            else:
                double_quote_payload += char

            if char == "\\" and not escape_next:
                escape_next = True
            else:
                escape_next = False

        received_event = json.loads(double_quote_payload)

    return received_event
