// Copyright (c) 2023, Golive Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salla Order", {
  refresh: (frm) => {
    $("[data-fieldname=salla_order_name_barcode]").attr("disabled", "disabled");
    frm.refresh_field("pos_profile");
  },
  generate_barcode: (frm) => {
    frm.set_value("salla_order_name_barcode", frm.doc.salla_order_no);
  },
});
