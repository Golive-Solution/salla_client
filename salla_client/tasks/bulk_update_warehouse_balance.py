import frappe

from salla_common.utils import update_product_balance_warehouse


def update_warehouse_balance():
    settings = frappe.get_single("Salla Client Settings")
    if not (settings.update_product_balance_warehouse and settings.update_bulk_warehouse_balance):
        return
    update_product_balance_warehouse()
