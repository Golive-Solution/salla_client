import frappe

from salla_common.utils import update_product_balance_warehouse


def update_warehouse_balance():
    settings = frappe.get_single("Salla Client Settings")
    if not settings.update_product_balance_warehouse:
        return
    update_product_balance_warehouse()
