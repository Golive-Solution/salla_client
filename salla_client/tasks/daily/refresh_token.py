import frappe
from frappe.utils.data import now
from salla_client.salla_utils import refresh_token


def refresh_token_every_day():
    merchants = frappe.db.sql(
        f"""
        SELECT name 
        FROM `tabSalla Settings`
        WHERE expires_on < '{now()}' or revoked = 1
        """,
        as_dict=1,
    )
    for merchant in merchants:
        refresh_token(merchant.name)
