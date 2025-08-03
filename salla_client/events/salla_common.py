import frappe
import re
from salla_common_lib.event import item, item_price, salla_order

def handle_salla_order_validate(doc, method):
    return salla_order.validate(doc, method)

def handle_salla_order_before_save(doc, method):
    return salla_order.before_save(doc, method)

def handle_salla_order_before_insert(doc, method):
    return salla_order.before_insert(doc, method)

def handle_salla_order_on_update(doc, method):
    if not doc.is_new():
        old_salla_order = doc.get_doc_before_save()
        # Convert item_code values to sets for comparison
        set_a = {item.item_code for item in old_salla_order.items}  # Use curly braces for a set
        set_b = {item.item_code for item in doc.items}

        # Find items in A that are not in B
        deleted_items = list(set_a - set_b)
        print(deleted_items)
        for item in deleted_items:
            item_doc = frappe.get_doc("Item", item)
            item_doc.custom_update_pending_online_quantity = 1
            item_doc.save()
def handle_salla_order_before_update_after_submit(doc, method):
    return salla_order.before_update_after_submit(doc, method)

def handle_salla_order_on_cancel(doc, method):
    return salla_order.on_cancel(doc, method)

def handle_salla_order_before_submit(doc, method):
    return salla_order.before_submit(doc, method)

import re
import frappe

def handle_item_on_validate(doc, method):
    if doc.custom_is_salla_item and doc.custom_send_item_to_salla:
        if not doc.custom_product_image:
            frappe.throw("The Product Image is mandatory for sending the item to Salla")

        image_url = doc.custom_product_image.strip()
        is_valid_image_url = re.match(r'^https?:\/\/.*\.(jpg|jpeg)(\?.*)?$', image_url, re.IGNORECASE)
        is_local_file = image_url.startswith("/files")

        if not is_valid_image_url or is_local_file:
            frappe.throw("The Product Image must be a valid .jpg or .jpeg URL and not a local /files path")

def handle_item_before_save(doc, method):
    return item.before_save(doc, method)

def handle_item_on_update(doc, method):
    return item.on_update(doc, method)

def handle_item_price_before_save(doc, method):
    return item_price.before_save(doc, method) 