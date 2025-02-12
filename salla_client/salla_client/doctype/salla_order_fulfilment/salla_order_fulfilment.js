// Copyright (c) 2023, Golive Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salla Order Fulfilment", {
  scan_order_barcode: (frm) => {
    if (frm.doc.scan_order_barcode !== "") {
      getSallaOrderByNo(frm);
    } else {
      clearFormFields(frm);
    }
  },
  scan_item_barcode: (frm) => {
    let item = frm.doc.item.find(
      (i) => i.barcode === frm.doc.scan_item_barcode
    );
    if (item) {
      if (item.has_serial) {
        msgprint("هذا الصنف يحتوى سريل , يجب عمل مسح للسريل بدلا من البار كود");
      } else {
        if (item.completed) {
          msgprint("لقد اكتمل هذا الصنف بالفعل ");
        } else {
          let scanQty = item.s_qty + 1;
          let difQty = item.o_qty - scanQty;
          let completed = scanQty === item.o_qty;
          frappe.model.set_value(item.doctype, item.name, "s_qty", scanQty);
          frappe.model.set_value(item.doctype, item.name, "d_qty", difQty);
          frappe.model.set_value(
            item.doctype,
            item.name,
            "completed",
            completed
          );
        }
      }
    } else {
      scan_barcode(frm);
    }
    frm.set_value("scan_item_barcode", "");
    let isOrderCompleted =
      frm.doc.item.filter((i) => !i.completed).length === 0;
    frm.set_value("order_completed", isOrderCompleted);
  },
  print_shipment: function (frm) {
    if (frm.doc.shipment_detials.length > 0) {
      let length = frm.doc.shipment_detials.length;
      for (let index = 0; index < length; index++) {
        if (
          frm.doc.shipment_detials[index].lable_url &&
          frm.doc.shipment_detials[index].lable_url !== ""
        ) {
          window.open(frm.doc.shipment_detials[index].lable_url, "_blank");
          break;
        }
      }
    }
  },
  print_pos_invoice: function (frm) {
    if (frm.doc.pos_invoice) {
      window.open(
        "/api/method/frappe.utils.print_format.download_pdf?doctype=POS%20Invoice&name=" +
          frm.doc.pos_invoice +
          "&format=POS%20Invoice%20Arabic&no_letterhead=0&letterhead=Mokab&settings=%7B%7D&_lang=ar",
        frm.doc.pos_invoice
      );
    }
  },
});

var getSallaOrderByNo = (frm, dotIndex) => {
  let allowedStatus = ["قيد التجهيز"];
  let barcode = frm.doc.scan_order_barcode;
  frappe.call({
    method: "frappe.client.get_value",
    args: {
      doctype: "Salla Order",
      filters: {
        salla_order_no: barcode,
      },
      fieldname: ["name", "order_status"],
    },
    callback: function (r) {
      if (!r.exe) {
        let salla_order = r.message;
        let isValid = allowedStatus.includes(salla_order.order_status);
        if (isValid) {
          frm.set_value("salla_order_no", salla_order.name);
        } else {
          clearFormFields(frm);
          msgprint(
            " غير مسموح باعداد هذا الطلب لانه " + salla_order.order_status
          );
        }
      } else {
        console.log("errr :", r.exe);
      }
    },
  });
};

var scan_barcode = (frm) => {
  let me = this;
  let search_value = frm.doc.scan_item_barcode;
  if (search_value) {
    frappe
      .call({
        method:
          "erpnext.selling.page.point_of_sale.point_of_sale.search_for_serial_or_batch_or_barcode_number",
        args: {
          search_value: frm.doc.scan_item_barcode,
        },
      })
      .then((r) => {
        const data = r && r.message;
        if (!data || Object.keys(data).length === 0) {
          frappe.show_alert({
            message: __("Cannot find Item with this Barcode"),
            indicator: "red",
          });
          return;
        }
        let item = frm.doc.item.find((i) => i.item_code === data.item_code);
        if (item) {
          if (item.completed) {
            msgprint("لقد اكتمل هذا الصنف بالفعل ");
          } else {
            if (item.serial_no && item.serial_no.includes(search_value)) {
              msgprint("لقدتم اضافة هذاالسريال بالفعل ");
            } else {
              let scanQty = item.s_qty + 1;
              let difQty = item.o_qty - scanQty;
              let completed = scanQty === item.o_qty;
              let serial_Nos = "";
              if (!item.serial_no) {
                serial_Nos = search_value;
              } else {
                serial_Nos = item.serial_no + "\n" + search_value;
              }
              frappe.model.set_value(item.doctype, item.name, "s_qty", scanQty);
              frappe.model.set_value(item.doctype, item.name, "d_qty", difQty);
              frappe.model.set_value(
                item.doctype,
                item.name,
                "serial_no",
                serial_Nos
              );
              frappe.model.set_value(
                item.doctype,
                item.name,
                "completed",
                completed
              );
            }
          }
        }
        let isOrderCompleted =
          frm.doc.item.filter((i) => !i.completed).length === 0;
        frm.set_value("order_completed", isOrderCompleted);
      });
  }
};

var clearFormFields = (frm) => {
  frm.set_value("scan_order_barcode", "");
  frm.set_value("salla_order_no", "");
  frm.set_value("customer", "");
  frm.set_value("ready_to_complete", "");
  frm.set_value("customer_first_name", "");
  frm.set_value("customer_last_name", "");
  frm.set_value("phone_number", "");
  frm.set_value("order_status", "");
  frm.set_value("order_date", "");
  frm.set_value("total_tax", "");
  frm.set_value("salla_payment_method", "");
  frm.set_value("cod_cost", "");
  frm.set_value("shipping_cost", "");
  frm.set_value("grand_total", "");
  frm.reload_doc();
};
