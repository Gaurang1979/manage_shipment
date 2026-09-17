frappe.ui.form.on("Tracking API Integration", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Test Tracking API"), () => {
                frappe.prompt(
                    [{fieldname: "tracking_id", fieldtype: "Data", label: __("Tracking / AWB Number"), reqd: 1}],
                    values => {
                        frappe.call({
                            method: "manage_shipment.manage_shipment.api.test_tracking_integration",
                            args: {integration_name: frm.doc.name, tracking_id: values.tracking_id},
                            freeze: true,
                            freeze_message: __("Testing tracking API...")
                        }).then(r => {
                            const d = r.message || {};
                            frappe.msgprint({
                                title: __("Tracking API Connection Successful"),
                                indicator: "green",
                                message: `<b>Status:</b> ${frappe.utils.escape_html(d.status || "Not returned")}<br><b>Courier Status:</b> ${frappe.utils.escape_html(d.courier_status || "")}<br><b>Location:</b> ${frappe.utils.escape_html(d.current_location || "")}`
                            });
                        });
                    },
                    __("Test Tracking"),
                    __("Test")
                );
            });
        }
    }
});
