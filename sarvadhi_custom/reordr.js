frappe.ui.form.on('Item', {
    refresh: function(frm) {
        frm.add_custom_button(__('Reorder Now'), function() {
            frappe.call({
                method: 'sarvadhi_custom.custom_api.task.manual_reorder',
				args: {
                    item_nm: frm.doc.item_name  
                },
                callback: function(response) {
                    frappe.msgprint(__('Reorder Triggered: ' + response.message));
                }
            });
        }, __("Actions"));
    }
});
