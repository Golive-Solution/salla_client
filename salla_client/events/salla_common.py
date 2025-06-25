import frappe
import re
from salla_common_lib.event import item, item_price, salla_order

def handle_salla_order_validate(doc, method):
    return salla_order.validate(doc, method)

def handle_salla_order_before_save(doc, method):
    return salla_order.before_save(doc, method)

def handle_salla_order_before_insert(doc, method):
    return salla_order.before_insert(doc, method)

def handle_salla_order_before_update_after_submit(doc, method):
    return salla_order.before_update_after_submit(doc, method)

def handle_salla_order_on_cancel(doc, method):
    return salla_order.on_cancel(doc, method)

def handle_salla_order_before_submit(doc, method):
    return salla_order.before_submit(doc, method)

def handle_item_on_validate(doc, method):
    if doc.custom_is_salla_item and doc.custom_send_item_to_salla:
        if not doc.custom_product_image:
            frappe.throw("The Product Image is mandatory for sending the item to Salla")

        # Check if the image is a valid URL and ends with .jpg, and is NOT a local /files path
        is_valid_jpg_url = re.match(r'^https?:\/\/.*\.jpg$', doc.custom_product_image, re.IGNORECASE)
        is_local_file = doc.custom_product_image.startswith("/files")

        if not is_valid_jpg_url or is_local_file:
            frappe.throw("The Product Image must be a valid .jpg URL and not a local /files path")
    

def handle_item_before_save(doc, method):
    return item.before_save(doc, method)

def handle_item_on_update(doc, method):
    return item.on_update(doc, method)

def handle_item_price_before_save(doc, method):
    return item_price.before_save(doc, method) 