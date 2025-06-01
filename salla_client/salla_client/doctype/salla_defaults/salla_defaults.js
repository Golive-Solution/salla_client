// Copyright (c) 2025, Golive Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on('Salla Defaults', {
	taxe_included_in_basic_rate: function(frm) {
		if (frm.doc.taxe_included_in_basic_rate) {
			frm.set_value('tax_description', "");
			frm.set_value('tax_type', "");
		}
	}
});
