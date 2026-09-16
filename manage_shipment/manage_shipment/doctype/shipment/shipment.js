frappe.ui.form.on("Shipment", {
    refresh(frm) {
        if (frm.doc.tracking_id && frm.doc.courier_service_provider) {
            frm.add_custom_button(__("Open Tracking"), () => {
                frappe.call({
                    method: "manage_shipment.manage_shipment.api.get_tracking_url",
                    args: {shipment: frm.doc.name},
                    callback(r) {
                        if (r.message) window.open(r.message, "_blank");
                        else frappe.msgprint(__("No tracking URL is configured for this courier."));
                    }
                });
            });
        }
        if (!frm.is_new() && frm.doc.tracking_enabled) {
            frm.add_custom_button(__("Refresh Tracking"), () => {
                frappe.call({
                    method: "manage_shipment.manage_shipment.api.refresh_shipment",
                    args: {shipment: frm.doc.name},
                    freeze: true,
                    freeze_message: __("Refreshing shipment tracking..."),
                    callback() { frm.reload_doc(); }
                });
            });
        }
    }
});
