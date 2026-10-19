import frappe

from salla_common_lib.utils import update_product_balance_warehouse


def update_warehouse_balance():
    # Per-merchant flags are checked again when the payload is sent
    if not frappe.db.exists(
        "Salla Client Settings",
        {"update_product_balance_warehouse": 1, "update_bulk_warehouse_balance": 1},
    ):
        return
    update_product_balance_warehouse(is_bulk=True)
