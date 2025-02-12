from salla_client.salla_utils import update_salla_price


def before_save(doc, method):
    update_salla_price(doc)
