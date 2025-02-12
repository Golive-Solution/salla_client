frappe.ui.form.on("Item", {
  refresh: function (frm) {
    // Apply custom class to button in existing rows
    apply_custom_button_style(frm);

    // // Apply custom class to button in new rows
    // frm.fields_dict['custom_salla_item'].grid.wrapper.on('row-render', function() {
    //     apply_custom_button_style(frm);
    // });
  },
});

function apply_custom_button_style(frm) {
  frm.fields_dict["custom_salla_item"].grid.grid_rows.forEach((row) => {
    // Find the button in the row and add the custom class
    $(document).on("DOMNodeInserted", function (event) {
      let button = $(row.row).find(
        'button[data-fieldname="update_product_qty"]'
      );
      if (button.length) {
        button.removeClass().addClass("btn btn-primary btn-sm primary-action");
      }
    });
  });
}

frappe.ui.form.on("Salla Item Info", {
  update_product_qty: function (frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    console.log("Merchant: " + row.merchant + " Parent: " + frm.doc.name);
    if (!frm.doc.variant_of) {
      frappe.call({
        method: "salla_client.salla_utils.update_product_balance_warehouse",
        args: {
          merchant: row.merchant, // Assuming 'merchant' is a field in the child table
          item: frm.doc.name, // Assuming 'item' is a field in the child table
        },
        callback: function (r) {
          if (r.message) {
            frappe.msgprint(r.message.message, r.message.subject);
          }
        },
      });
    } else {
      frappe.call({
        method: "salla_client.salla_utils.update_variant_qty",
        args: {
          merchant_name: row.merchant, // Assuming 'merchant' is a field in the child table
          item_variant: frm.doc.name, // Assuming 'item' is a field in the child table
          salla_item_info_name: row.name,
        },
        callback: function (r) {
          if (r.message) {
            // frappe.msgprint(r.message.message, r.message.subject);
          }
        },
      });
    }
  },
});
