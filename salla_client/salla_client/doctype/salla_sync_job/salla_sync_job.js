// Copyright (c) 2025, Golive Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on('Salla Sync Job', {
	update_bulk_warehouse: function (frm) {
		if (!(frm.doc.warehouse || frm.doc.merchant)) return;
		frm.set_df_property('update_bulk_warehouse', 'hidden', 1);
		frm.refresh_field('update_bulk_warehouse');

		frappe.call({
			method: "salla_client.utils.update_product_balance_warehouse",
			args: {
				merchant_name: frm.doc.merchant, 
				is_bulk: 1
			},
			callback: function(r){
				frm.set_df_property('update_bulk_warehouse', 'hidden', 0);
				frm.refresh_field('update_bulk_warehouse');
			}
		});
	}
});
