from salla_common_lib.event import unified_integration

def handle_salla_order_before_submit(doc, method):
    return unified_integration.before_submit(doc, method)

def handle_salla_order_before_save(doc, method):
    return unified_integration.before_save(doc, method)

def handle_salla_order_on_update_after_submit(doc, method):
    return unified_integration.on_update_after_submit(doc, method)

def handle_update_custom_status_sales_order(doc):
    return unified_integration.update_custom_status_sales_order(doc)

def handle_get_payment_method(salla_payment_method):
    return unified_integration.get_payment_method(salla_payment_method)

def handle_get_shipping_item(salla_shipping_method):
    return unified_integration.get_shipping_item(salla_shipping_method)

def handle_create_pos_invoice(doc, salla_default):
    return unified_integration.create_pos_invoice(doc, salla_default)

def handle_create_sales_invoice(doc, salla_default):
    return unified_integration.create_sales_invoice(doc, salla_default)

def handle_create_sales_order(doc, salla_default):
    return unified_integration.create_sales_order(doc, salla_default)

def handle_add_invoice_items(invoice, items, pos_profile_doc, item_doctype):
    return unified_integration.add_invoice_items(invoice, items, pos_profile_doc, item_doctype)

def handle_add_shipping_item(invoice, shipping_item, shipping_cost, pos_profile_doc, item_doctype):
    return unified_integration.add_shipping_item(invoice, shipping_item, shipping_cost, pos_profile_doc, item_doctype)

def handle_add_cod_item(invoice, cod_item, cod_cost, pos_profile_doc, item_doctype):
    return unified_integration.add_cod_item(invoice, cod_item, cod_cost, pos_profile_doc, item_doctype)

def handle_add_order_items(sales_order, items, salla_default):
    return unified_integration.add_order_items(sales_order, items, salla_default)

def handle_add_shipping_order_item(sales_order, shipping_item, shipping_cost, salla_default):
    return unified_integration.add_shipping_order_item(sales_order, shipping_item, shipping_cost, salla_default)

def handle_add_cod_order_item(sales_order, cod_item, cod_cost, salla_default):
    return unified_integration.add_cod_order_item(sales_order, cod_item, cod_cost, salla_default)

def handle_add_tax_charges(document, total_tax, salla_default):
    return unified_integration.add_tax_charges(document, total_tax, salla_default)

def handle_add_payment(invoice, payment_method, amount, payment_doctype):
    return unified_integration.add_payment(invoice, payment_method, amount, payment_doctype)

def handle_create_payment_entry(sales_order, payment_method, doc):
    return unified_integration.create_payment_entry(sales_order, payment_method, doc)

def handle_update_order_fulfillment(salla_order_no, invoice_name):
    return unified_integration.update_order_fulfillment(salla_order_no, invoice_name)
