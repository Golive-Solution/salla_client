// Copyright (c) 2024, Golive-Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on('Salla Defaults', {
	onload: function(frm) {
        // Set filter on the 'next_shipment_item' Link field
        frm.set_query('cod_item', function(doc) {
            return {
                filters: {
                    'is_stock_item': 0
                }
            };
        });
    },
    validate: function(frm) {
        // Check if the selected item meets the filter criteria
        if (frm.doc.cod_item) {
            frappe.db.get_value('Item', frm.doc.cod_item, 'is_stock_item', function(data) {
                if (data && data.is_stock_item === 1) {
                    frappe.msgprint(__("The selected Item is a stock item and doesn't meet the filter criteria."));
                    frappe.validated = false; // Prevent saving the document
                }
            });
        }
    }
});