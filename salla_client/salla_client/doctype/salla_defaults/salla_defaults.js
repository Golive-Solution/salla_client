// Copyright (c) 2023, Golive Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on('Salla Defaults', {
	integration_type: function(frm) {
		if (frm.doc.integration_type) {
			// Show confirmation dialog when changing integration type
			if (frm.doc.__islocal === 0) {  // Only for existing documents
				frappe.confirm(
					__('Changing integration type will modify custom fields across the system. This action will require a page refresh. Continue?'),
					function() {
						// User confirmed - proceed with the change
						frm.save().then(() => {
							frappe.show_alert({
								message: __('Integration type updated. Please refresh the page to see changes.'),
								indicator: 'green'
							});
							
							// Auto refresh after 2 seconds
							setTimeout(() => {
								location.reload();
							}, 2000);
						});
					},
					function() {
						// User cancelled - revert the change
						frm.reload_doc();
					}
				);
			}
		}
	},
	
	refresh: function(frm) {
		// Add custom buttons or indicators based on integration type
		if (frm.doc.integration_type) {
			add_integration_info(frm);
		}
		
		// Add button to refresh field configuration
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Refresh Fields'), function() {
				frappe.call({
					method: 'manage_custom_fields',
					doc: frm.doc,
					callback: function(r) {
						frappe.show_alert({
							message: __('Custom fields refreshed successfully'),
							indicator: 'green'
						});
						setTimeout(() => {
							location.reload();
						}, 1500);
					}
				});
			});
		}
	},
	
	onload: function(frm) {
		// Set field descriptions based on integration type
		update_field_descriptions(frm);
	}
});

function add_integration_info(frm) {
	// Remove existing integration info
	frm.dashboard.clear_comment();
	
	let integration_type = frm.doc.integration_type;
	let info_html = '';
	
	switch(integration_type) {
		case 'POS Invoice':
			info_html = `
				<div class="alert alert-info">
					<strong>POS Invoice Integration Active</strong><br>
					Salla Orders will create POS Invoices with immediate stock updates and payment processing.
					<br><strong>Features:</strong> Real-time inventory, POS workflow, immediate payment capture
				</div>
			`;
			break;
			
		case 'Sales Invoice':
			info_html = `
				<div class="alert alert-success">
					<strong>Sales Invoice Integration Active</strong><br>
					Salla Orders will create Sales Invoices with flexible payment and delivery options.
					<br><strong>Features:</strong> Standard invoicing, flexible payments, delivery tracking
				</div>
			`;
			break;
			
		case 'Sales Order':
			info_html = `
				<div class="alert alert-warning">
					<strong>Sales Order Integration Active</strong><br>
					Salla Orders will create Sales Orders for order management workflow.
					<br><strong>Features:</strong> Order pipeline, delivery scheduling, payment entries
				</div>
			`;
			break;
	}
	
	if (info_html) {
		frm.dashboard.add_comment(info_html, 'blue', true);
	}
}

function update_field_descriptions(frm) {
	// Add helpful descriptions to fields
	frm.set_df_property('integration_type', 'description', 
		'Choose how Salla Orders will be processed: POS Invoice (immediate), Sales Invoice (flexible), or Sales Order (workflow)');
	
	frm.set_df_property('custom_warehouse', 'description', 
		'Default warehouse for Sales Order items (only applicable for Sales Order integration)');
	
	frm.set_df_property('custom_days_to_delivery_order', 'description', 
		'Default number of days to add to current date for delivery date in Sales Orders');
}
