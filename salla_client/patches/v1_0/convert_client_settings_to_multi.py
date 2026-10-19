import frappe


def execute():
    """Move the old Single Salla Client Settings values into a regular record named by site."""
    old_values = frappe._dict(
        frappe.db.sql(
            "select field, value from `tabSingles` where doctype = 'Salla Client Settings'"
        )
    )
    if not old_values.get("site"):
        return

    if not frappe.db.exists("Salla Client Settings", old_values.site):
        settings = frappe.get_doc(
            {
                "doctype": "Salla Client Settings",
                "server_url": old_values.server_url,
                "api_key": old_values.api_key,
                "api_secret": old_values.api_secret,
                "site": old_values.site,
                "update_product_balance_warehouse": old_values.update_product_balance_warehouse,
                "update_bulk_warehouse_balance": old_values.update_bulk_warehouse_balance,
                "create_or_update_salla_item": old_values.create_or_update_salla_item,
                "update_variant_qty": old_values.update_variant_qty,
                "update_salla_price": old_values.update_salla_price,
            }
        )

        # The Single had no merchant; it can only be inferred when the client has one merchant
        merchants = frappe.get_all("Salla Merchant", pluck="name")
        if len(merchants) == 1:
            settings.merchant = merchants[0]
        else:
            settings.flags.ignore_mandatory = True
            frappe.log_error(
                "Salla Client Settings missing merchant",
                f"Set the merchant on Salla Client Settings {old_values.site} manually. "
                f"Found {len(merchants)} Salla Merchants on this site.",
            )

        settings.insert(ignore_permissions=True)

    frappe.db.delete("Singles", {"doctype": "Salla Client Settings"})
