# Copyright (c) 2023, Golive Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SallaOrderFulfilment(Document):
    def on_submit(self):
        SallaOrder = frappe.get_doc("Salla Order", self.salla_order_no)
        SallaOrder.docstatus = 1
        SallaOrder.order_status = "تم التنفيذ"
        SallaOrder.salla_order_fulfilment = self.name
        for fullFillmet_item in self.item:
            for salla_item in SallaOrder.item:
                if fullFillmet_item.barcode in salla_item.barcode:
                    salla_item.serial_no = fullFillmet_item.serial_no
                    break

        SallaOrder.save()

    def before_insert(self):
        self.scan_order_barcode = ""
        self.preparing_date = frappe.utils.today()
        sallaOrderItems = frappe.get_list(
            "Salla Order Item",
            filters={"parent": self.salla_order_no},
            fields=["barcode", "item_code", "salla_item_name", "qty", "rate"],
        )
        if len(sallaOrderItems) > 0:
            for item in sallaOrderItems:
                barcodeList = item.barcode.split("-")
                if len(barcodeList) > 1:
                    uniqueBarcodeList = []
                    for barcode in barcodeList:
                        if uniqueBarcodeList.count(barcode) == 0:
                            uniqueBarcodeList.append(barcode)
                    for uniqueBarcode in uniqueBarcodeList:
                        ItemCodeList = frappe.get_list(
                            "Item",
                            filters=[["barcode", "like", "%#" + uniqueBarcode + "#%"]],
                            fields=["item_code"],
                        )
                        sallaOrderItemFulfilment = frappe.get_doc(
                            {"doctype": "Salla Order Item Fulfilment"}
                        )
                        if len(ItemCodeList) > 0:
                            sallaOrderItemFulfilment.item_code = ItemCodeList[
                                0
                            ].item_code
                        sallaOrderItemFulfilment.barcode = uniqueBarcode
                        sallaOrderItemFulfilment.salla_item_name = item.salla_item_name
                        sallaOrderItemFulfilment.o_qty = (
                            barcodeList.count(uniqueBarcode) * item.qty
                        )
                        sallaOrderItemFulfilment.rate = item.rate
                        sallaOrderItemFulfilment.discount_amount = item.discount_amount
                        sallaOrderItemFulfilment.d_qty = (
                            0 - sallaOrderItemFulfilment.o_qty
                        )
                        self.append("item", sallaOrderItemFulfilment)
                else:
                    sallaOrderItemFulfilment = frappe.get_doc(
                        {"doctype": "Salla Order Item Fulfilment"}
                    )
                    sallaOrderItemFulfilment.barcode = item.barcode
                    sallaOrderItemFulfilment.item_code = item.item_code
                    sallaOrderItemFulfilment.salla_item_name = item.salla_item_name
                    sallaOrderItemFulfilment.o_qty = item.qty
                    sallaOrderItemFulfilment.rate = item.rate
                    sallaOrderItemFulfilment.discount_amount = item.discount_amount
                    sallaOrderItemFulfilment.d_qty = 0 - item.qty
                    self.append("item", sallaOrderItemFulfilment)
        sallaOrderShippments = frappe.get_list(
            "Salla Order Shipment Details",
            filters={"parent": self.salla_order_no},
            fields=["tracking_number", "tracking_link", "lable_url"],
        )
        if len(sallaOrderShippments) > 0:
            for Shippment in sallaOrderShippments:
                sallaOrderShipmentFulfilment = frappe.get_doc(
                    {"doctype": "Salla Order Shipment Fulfilment"}
                )
                sallaOrderShipmentFulfilment.tracking_number = Shippment.tracking_number
                sallaOrderShipmentFulfilment.tracking_link = (
                    '<a target="_blank" href="'
                    + Shippment.tracking_link
                    + '">Track </a>'
                )
                sallaOrderShipmentFulfilment.lable_url = Shippment.lable_url
                self.append("shipment_detials", sallaOrderShipmentFulfilment)
