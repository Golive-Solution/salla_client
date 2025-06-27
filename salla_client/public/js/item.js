frappe.ui.form.on("Item", {
  refresh: function (frm) {
    // Apply custom class to button in existing rows
    apply_custom_button_style(frm);
    // update_image_button(frm)
  },

  // custom_salla_image_id: function (frm) {
  //   update_image_button(frm);
  // }
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
        method: "salla_client.utils.update_product_balance_warehouse",
        args: {
          merchant: row.merchant, // Assuming 'merchant' is a field in the child table
          item: frm.doc.name, // Assuming 'item' is a field in the child table
        },
        callback: function (r) {

          // frappe.msgprint(r.message.message, r.message.subject);
          frappe.model.set_value(cdt, cdn, 'last_update', frappe.datetime.get_today())

        },
      });
    } else {
      frappe.call({
        method: "salla_client.utils.update_variant_qty",
        args: {
          merchant_name: row.merchant, // Assuming 'merchant' is a field in the child table
          item_variant: frm.doc.name, // Assuming 'item' is a field in the child table
          salla_item_info_name: row.name,
        },
        callback: function (r) {

          frappe.model.set_value(cdt, cdn, 'last_update', frappe.datetime.get_today())


        },
      });
    }
  },
});

function update_image_button(frm) {
  // Remove existing button
  if (frm.custom_buttons && frm.custom_buttons['Update Image']) {
    frm.remove_custom_button(__('Update Image'));
  }

  // Add button if the image ID exists
  if (frm.doc.custom_salla_image_id) {
    frm.add_custom_button(__('Update Image'), function () {
      handle_salla_image_update(frm);
    });
  }
}

function handle_salla_image_update(frm) {
  const { item_name, custom_product_image, custom_salla_image_id } = frm.doc;

  const merchant = frm.doc.custom_salla_item[0].merchant

  // Call backend method
  frappe.call({
    method: 'salla_client.salla_utils.update_item_image',
    args: {
      item_name: item_name,
      file_url: custom_product_image,
      image_id: custom_salla_image_id,
      merchant: merchant,
    },
    callback: function (r) {
      if (!r.exc) {
        console.log(r);
      }
    },
  });
}

