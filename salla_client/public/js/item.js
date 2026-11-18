frappe.ui.form.on("Item", {
  refresh: function (frm) {
    // Apply custom class to button in existing rows
    apply_custom_button_style(frm);
    update_image_button(frm)
  },

  custom_salla_image_id: function (frm) {
    update_image_button(frm);
  }
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
          merchant_name: row.merchant, // Only send stock for this row's merchant
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

// Rows whose merchant has a Salla image ID. Each merchant's store has its own
// image ID; the item-level field is only trusted when there is a single merchant.
function get_salla_image_rows(frm) {
  const rows = frm.doc.custom_salla_item || [];
  return rows
    .map((row) => ({
      merchant: row.merchant,
      image_id:
        row.salla_image_id ||
        (rows.length === 1 ? frm.doc.custom_salla_image_id : null),
    }))
    .filter((row) => row.merchant && row.image_id);
}

function update_image_button(frm) {
  // Remove existing button
  if (frm.custom_buttons && frm.custom_buttons[__('Update Image')]) {
    frm.remove_custom_button(__('Update Image'));
  }

  // Add button if any merchant has an image ID
  if (get_salla_image_rows(frm).length) {
    frm.add_custom_button(__('Update Image'), function () {
      handle_salla_image_update(frm);
    });
  }
}

function handle_salla_image_update(frm) {
  const rows = get_salla_image_rows(frm);

  if (rows.length === 1) {
    send_salla_image_update(frm, rows[0]);
    return;
  }

  frappe.prompt(
    {
      fieldname: 'merchant',
      fieldtype: 'Select',
      label: __('Merchant'),
      options: rows.map((row) => row.merchant),
      reqd: 1,
    },
    (values) => {
      send_salla_image_update(
        frm,
        rows.find((row) => row.merchant === values.merchant)
      );
    },
    __('Update Image For Merchant'),
    __('Update')
  );
}

function send_salla_image_update(frm, row) {
  frappe.call({
    method: 'salla_client.salla_utils.update_item_image',
    args: {
      item_name: frm.doc.item_name,
      file_url: frm.doc.custom_product_image,
      image_id: row.image_id,
      merchant: row.merchant,
    },
    callback: function (r) {
      if (!r.exc) {
        console.log(r);
      }
    },
  });
}
