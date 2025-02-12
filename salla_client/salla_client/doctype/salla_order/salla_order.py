# Copyright (c) 2023, Golive Solutions and contributors
# For license information, please see license.txt

from http.client import HTTPException
import frappe
from frappe import _, msgprint
from frappe.model.document import Document


class SallaOrder(Document):
    def before_save(self):
        if frappe.db.exists("Salla Defaults", self.merchant):
            salla_default = frappe.get_doc("Salla Defaults", self.merchant)
        else:
            frappe.throw(f"Merchant {self.merchant} Defaults Not Exist.")
        if not self.company:
            self.company = salla_default.company
        for salla_item in self.items:
            salla_item.order_status = self.order_status
            salla_item.merchant = self.merchant
            # salla_item.workflow_state = self.workflow_state
            if "-" in salla_item.barcode:
                salla_item.is_bundle = 1
        # update pending online Online quantity for items
        decremant_pending_online_quantity = 0
        if self.order_status != self.old_order_status and self.order_status == "ملغي":
            decremant_pending_online_quantity = 1
        if decremant_pending_online_quantity:
            for salla_item in self.items:
                if salla_item.barcode:
                    barcodeList = salla_item.barcode.split("-")
                    for barcode in barcodeList:
                        ItemCodeList = frappe.get_list(
                            "Item",
                            filters=[
                                [
                                    "custom_concatenated_barcode",
                                    "like",
                                    "%#" + barcode + "#%",
                                ]
                            ],
                            fields=["item_code", "name"],
                        )
                        if len(ItemCodeList) > 0:
                            item = frappe.get_doc("Item", ItemCodeList[0].name)
                            salla_item_info = None
                            # salla_item.item_code = ItemCodeList[0].item_code
                            # salla_item.item_name = ItemCodeList[0].name
                            # print(f"ItemCodeList: {ItemCodeList[0]}")
                            salla_item_info_exist = frappe.db.exists(
                                "Salla Item Info",
                                f"{self.merchant}-{ItemCodeList[0].name}",
                            )
                            if salla_item_info_exist:
                                salla_item_info = frappe.get_doc(
                                    "Salla Item Info",
                                    f"{self.merchant}-{ItemCodeList[0].name}",
                                )
                            else:
                                salla_item_info = frappe.get_doc(
                                    {"doctype": "Salla Item Info"}
                                )
                                salla_item_info.parent = ItemCodeList[0].name
                                salla_item_info.merchant = self.merchant

                            if (
                                salla_item_info.pending_online_quantity
                                and salla_item_info.pending_online_quantity
                                >= salla_item.qty
                            ):
                                salla_item_info.pending_online_quantity = (
                                    salla_item_info.pending_online_quantity
                                    - salla_item.qty
                                )
                            else:
                                salla_item_info.pending_online_quantity = 0
                            item.append("custom_salla_item", salla_item_info)
                            salla_item_info.save()

        if not self.customer:
            CustomerList = frappe.get_list(
                "Customer",
                filters=[["mobile_no", "=", self.phone_number]],
                fields=["name", "customer_name"],
            )
            if len(CustomerList) > 0:
                self.customer = CustomerList[0].name
                self.customer_full_name = CustomerList[0].customer_name
            else:
                customer = frappe.get_doc({"doctype": "Customer"})

                last_name = ""
                if self.customer_last_name:
                    last_name = self.customer_last_name

                customer.customer_name = (
                    self.customer_first_name + " " + last_name
                )  # + " - "+self.phone_number
                customer.mobile_no = self.phone_number
                customer.customer_name_in_arabic = customer.customer_name
                customer.mobile_number = self.phone_number
                if frappe.db.exists(
                    "Salla Currency Mapping", {"name": self.customer_currency}
                ):
                    currency_mapping_customer_group = frappe.get_doc(
                        "Salla Currency Mapping", self.customer_currency
                    )
                    customer.customer_group = (
                        currency_mapping_customer_group.customer_group
                    )
                else:
                    frappe.throw(
                        f"This Customer Cannot Be Created because This Currency {self.customer_currency} Didn't Mapped To Customer Group"
                    )
                customer.territory = salla_default.territory
                customer.customer_type = self.customer_type
                customer.email_id = self.customer_email

                customer.insert()
                self.customer = customer.name
                self.customer_full_name = customer.customer_name

        self.old_order_status = self.order_status

        # check if the recipient no is already has been modified
        # if self.is_notify == 0 and not self.recipient:
        # 	self.recipient = "966"+self.phone_number

    def before_insert(self):
        if frappe.db.exists("Salla Defaults", self.merchant):
            salla_default = frappe.get_doc("Salla Defaults", self.merchant)
        else:
            frappe.throw(f"Merchant {self.merchant} Defaults Not Exist.")

        self.pos_profile = salla_default.pos_profile
        self.old_order_status = ""
        ready_to_complete = True
        for salla_item in self.items:
            if salla_item.barcode:
                ItemCodeList = frappe.get_list(
                    "Item",
                    filters=[
                        [
                            "custom_concatenated_barcode",
                            "like",
                            "%#" + salla_item.barcode + "#%",
                        ]
                    ],
                    fields=["item_code", "item_name", "name"],
                )
                if len(ItemCodeList) > 0:
                    salla_item.item_code = ItemCodeList[0].item_code
                    salla_item.item_name = ItemCodeList[0].item_name
                else:
                    ready_to_complete = False
        self.ready_to_complete = ready_to_complete

        if self.order_status != "ملغي":
            for salla_item in self.items:
                if salla_item.barcode:
                    barcodeList = salla_item.barcode.split("-")
                    for barcode in barcodeList:
                        ItemCodeList = frappe.get_list(
                            "Item",
                            filters=[
                                [
                                    "custom_concatenated_barcode",
                                    "like",
                                    "%#" + barcode + "#%",
                                ]
                            ],
                            fields=["item_code", "name"],
                        )
                        if len(ItemCodeList) > 0:
                            item = frappe.get_doc("Item", ItemCodeList[0].name)
                            salla_item_info = None
                            salla_item_info_exist = frappe.db.exists(
                                "Salla Item Info", f"{self.merchant}-{item.name}"
                            )
                            if salla_item_info_exist:
                                salla_item_info = frappe.get_doc(
                                    "Salla Item Info", f"{self.merchant}-{item.name}"
                                )
                            else:
                                salla_item_info = frappe.get_doc(
                                    {"doctype": "Salla Item Info"}
                                )
                                salla_item_info.parent = item.name
                                salla_item_info.merchant = self.merchant

                            if (
                                salla_item_info.pending_online_quantity
                                and salla_item_info.pending_online_quantity
                                >= salla_item.qty
                            ):
                                salla_item_info.pending_online_quantity = (
                                    salla_item_info.pending_online_quantity
                                    - salla_item.qty
                                )
                            else:
                                salla_item_info.pending_online_quantity = 0
                            item.append("custom_salla_item", salla_item_info)
                            salla_item_info.save()

    def submit(self):
        if self.docstatus != 1:
            try:
                msgprint(
                    _(
                        "The task has been enqueued as a background job. In case there is any issue on processing in background, the system will add a comment about the error on this Salla Order and revert to the Draft stage"
                    )
                )
                self.queue_action("submit", timeout=2000)
            except HTTPException as e:
                self.status = "Failed"
                return e
        else:
            self._submit()

    def before_update_after_submit(self):
        for salla_item in self.items:
            salla_item.is_document_submitted = 1
            salla_item.order_status = self.order_status

    def cancel(self):
        try:
            msgprint(
                _(
                    "The task has been enqueued as a background job. In case there is any issue on processing in background, the system will add a comment about the error on this Salla Order  and revert to the Submitted stage"
                )
            )
            self.queue_action("cancel", timeout=2000)
        except HTTPException as e:
            self.status = "Failed"
            return e
