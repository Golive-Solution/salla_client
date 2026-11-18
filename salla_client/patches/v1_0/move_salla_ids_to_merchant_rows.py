import frappe


def execute():
    """Copy the item-level Salla IDs onto the merchant's Salla Item Info row.

    The Salla variant/image ID is different in every merchant's store, but it used
    to be stored once on the Item. When an item has a single merchant row we know
    which store the ID belongs to, so it is copied there. When an item has several
    merchant rows the stored ID belongs to only one of them (whichever synced last),
    so the rows are left empty; the next sync finds each product by SKU and fills
    the right ID per merchant.
    """
    if not all(
        frappe.db.has_column("Item", column)
        for column in ("custom_salla_variant_id", "custom_salla_image_id", "custom_is_synced")
    ):
        return

    rows = frappe.db.sql(
        """
        select info.name, info.parent, info.merchant,
            item.custom_salla_variant_id, item.custom_salla_image_id, item.custom_is_synced
        from `tabSalla Item Info` info
        join `tabItem` item on item.name = info.parent
        where info.parenttype = 'Item' and info.parentfield = 'custom_salla_item'
        """,
        as_dict=True,
    )

    rows_per_item = {}
    for row in rows:
        rows_per_item.setdefault(row.parent, []).append(row)

    ambiguous_items = []
    for item, item_rows in rows_per_item.items():
        if len(item_rows) > 1:
            if item_rows[0].custom_salla_variant_id:
                ambiguous_items.append(item)
            continue

        row = item_rows[0]
        frappe.db.set_value(
            "Salla Item Info",
            row.name,
            {
                "salla_variant_id": row.custom_salla_variant_id,
                "salla_image_id": row.custom_salla_image_id,
                "is_synced": row.custom_is_synced or 0,
            },
            update_modified=False,
        )

    if ambiguous_items:
        frappe.log_error(
            "Salla IDs not migrated for multi-merchant items",
            "These items are linked to more than one merchant, so their single Salla ID "
            "cannot be assigned to a merchant. They will get a per-merchant ID on the next "
            "sync (looked up by SKU):\n" + "\n".join(ambiguous_items),
        )
