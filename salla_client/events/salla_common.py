from salla_common.event import item, item_price, salla_order

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

def handle_item_before_save(doc, method):
    return item.before_save(doc, method)

def handle_item_on_update(doc, method):
    return item.on_update(doc, method)

def handle_item_price_before_save(doc, method):
    return item_price.before_save(doc, method) 