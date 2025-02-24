import frappe
from salla_client.salla_utils import create_or_update_salla_item


def before_save(doc, method):
    Update_salla_online_qty(doc)
    update_item_barcode(doc)

    if doc.variant_of and not has_barcode(doc):
        parent = frappe.get_doc("Item", doc.variant_of)
        send_to_salla = parent.custom_send_item_to_salla == 1
        merchant_name = parent.custom_salla_item[0].merchant if send_to_salla else None

        # Set up default data for the variant based on parent item settings
        setup_variant_data(doc, send_to_salla, merchant_name)


def on_update(doc, method):
    for row in doc.custom_salla_item:
        print("ON UPDATE !!!!!")
        ## This should be optimized for bulk processing to reduce api calls
        create_or_update_salla_item(doc, row.merchant)


def update_item_barcode(doc):
    old_doc = doc.get_doc_before_save()
    if not old_doc or len(doc.barcodes) != len(old_doc.barcodes):
        barcodes_list = [row.barcode for row in doc.barcodes]
        if len(barcodes_list) > 0:
            doc.custom_concatenated_barcode = "#"
            doc.custom_concatenated_barcode += "#".join(barcodes_list)
            doc.custom_concatenated_barcode += "#"


def Update_salla_online_qty(doc):
    for salla_item_info in doc.custom_salla_item:
        update_online_qty(salla_item_info)


def update_online_qty(doc):
    total_online_qty = 0

    if doc.update_online_qty and not doc.parent.is_bundle:
        doc.update_online_qty = 0
        # Check for normal Items
        items = frappe.get_list(
            "Salla Order Item",
            filters=[
                ["is_document_submitted", "=", 0],
                ["merchant", "=", doc.merchant],
                ["order_status", "!=", "ملغي"],
                ["item_code", "=", doc.parent.item_code],
            ],
            fields=["qty"],
        )
        # frappe.msgprint('Non Bunsle items length is : ' + str(len(items)));
        if len(items) > 0:
            for item in items:
                total_online_qty = total_online_qty + item.qty

        # Check for Item in bundles
        bundel_items = frappe.get_list(
            "Salla Order Item",
            filters=[
                ["is_document_submitted", "=", 0],
                ["merchant", "=", doc.merchant],
                ["order_status", "!=", "ملغي"],
                ["is_bundle", "=", 1],
            ],
            fields=["qty", "barcode", "merchant"],
        )
        # frappe.msgprint('bundel_items length is : ' + str(len(bundel_items)));
        if len(bundel_items) > 0:
            for bundel_item in bundel_items:
                # frappe.msgprint('bundle barcode is : '+ bundel_item.barcode);
                # frappe.msgprint('bundle qty is : '+ str(bundel_item.qty));
                # frappe.msgprint('total_online_qty is ' + str(total_online_qty));
                barcodeList = bundel_item.barcode.split("-")
                for barcode in barcodeList:
                    # frappe.msgprint('item barcode is : '+ barcode);
                    # frappe.msgprint('Item to be updated barcode is : '+ doc.barcode);
                    if "#" + barcode + "#" in doc.parent.barcode:
                        # frappe.msgprint('barcode is in doc item');
                        total_online_qty = total_online_qty + bundel_item.qty
                        # frappe.msgprint('total_online_qty is ' + str(total_online_qty));
        doc.pending_online_quantity = total_online_qty
        # frappe.msgprint('total_online_qty is ' + str(total_online_qty));
        # frappe.msgprint('pending_online_quantity is ' + str(doc.pending_online_quantity));


def setup_variant_data(doc, send_to_salla, merchant_name):
    frappe.msgprint("Setting up default data for the variant")
    doc.custom_is_salla_item = 1
    if send_to_salla:
        doc.custom_send_item_to_salla = 1
        add_merchant(doc, merchant_name)
        frappe.msgprint("Merchant and Salla settings applied")

    add_barcode(doc)


def add_merchant(doc, merchant_name):
    if not any(row.merchant == merchant_name for row in doc.custom_salla_item):
        doc.append("custom_salla_item", {"merchant": merchant_name})
        frappe.msgprint(f"Merchant {merchant_name} added to variant.")


def add_barcode(doc):
    barcode_value = doc.item_code
    if not any(barcode.barcode == barcode_value for barcode in doc.barcodes):
        doc.append("barcodes", {"barcode": barcode_value, "custom_is_salla_barcode": 1})
        frappe.msgprint(f"Barcode {barcode_value} added to variant.")


def has_barcode(doc):
    """Checks if a barcode already exists in the item variant."""
    return any(barcode_entry.barcode for barcode_entry in doc.barcodes)
