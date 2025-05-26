# Copyright (c) 2023, Golive Solutions and contributors
# For license information, please see license.txt

from http.client import HTTPException
import frappe
from frappe import _, msgprint
from frappe.model.document import Document


class SallaOrder(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from salla_client.salla_client.doctype.salla_order_item.salla_order_item import SallaOrderItem
        from salla_client.salla_client.doctype.salla_order_shipment_details.salla_order_shipment_details import SallaOrderShipmentDetails

        amended_from: DF.Link | None
        bank_reference: DF.Data | None
        cod_cost: DF.Currency
        company: DF.Link | None
        currency: DF.Link | None
        custom_status: DF.Data | None
        customer: DF.Link | None
        customer_city: DF.Data | None
        customer_country: DF.Data | None
        customer_currency: DF.Link | None
        customer_email: DF.Data | None
        customer_first_name: DF.Data | None
        customer_full_name: DF.Data | None
        customer_last_name: DF.Data | None
        customer_type: DF.Literal["Individual", "Company"]
        date: DF.Date | None
        grand_total: DF.Currency
        is_salla_order: DF.Check
        is_store_delivery: DF.Check
        items: DF.Table[SallaOrderItem]
        merchant: DF.Link | None
        merchant_name: DF.Data | None
        old_order_status: DF.Data | None
        order_status: DF.Data | None
        phone_number: DF.Data | None
        pos_profile: DF.Link | None
        ready_to_complete: DF.Check
        salla_barcode: DF.AttachImage | None
        salla_order_fulfilment: DF.Link | None
        salla_order_no: DF.Data | None
        salla_payment_method: DF.Data | None
        salla_shipping_method: DF.Data | None
        selling_price_list: DF.Link | None
        shipment_detials: DF.Table[SallaOrderShipmentDetails]
        shipping_cost: DF.Currency
        total_tax: DF.Currency
        update_document: DF.Check
    # end: auto-generated types
    pass
    # def submit(doc, method=None):
    #     if doc.docstatus != 1:
    #         try:
    #             msgprint(
    #                 _(
    #                     "The task has been enqueued as a background job. In case there is any issue on processing in background, the system will add a comment about the error on this Salla Order and revert to the Draft stage"
    #                 )
    #             )
    #             doc.queue_action("submit", timeout=2000)
    #         except HTTPException as e:
    #             doc.status = "Failed"
    #             return e
    #     else:
    #         doc._submit()