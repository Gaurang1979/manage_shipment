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
        if (!frm.is_new() && !frm.doc.tracking_id && frm.doc.booking_integration) {
            frm.add_custom_button(__("Check Rates"), () => check_rates(frm), __("Booking"));
            frm.add_custom_button(__("Create Shipment"), () => create_shipment(frm), __("Booking"));
        }
    }
});

function check_rates(frm) {
    frappe.call({
        method: "manage_shipment.manage_shipment.api.get_shipping_rates",
        args: {shipment: frm.doc.name},
        freeze: true,
        freeze_message: __("Checking rates..."),
        callback(r) {
            const rates = r.message || [];
            if (!rates.length) {
                frappe.msgprint(__("No courier options were returned for this route/weight."));
                return;
            }
            show_rate_dialog(frm, rates);
        }
    });
}

function show_rate_dialog(frm, rates) {
    const rows = rates.map((r, i) => `<tr>
        <td>${frappe.utils.escape_html(r.courier_name || "")}</td>
        <td>${frappe.utils.escape_html(String(r.estimated_days || ""))}</td>
        <td>${frappe.utils.escape_html(String(r.rate || ""))}</td>
        <td><button class="btn btn-xs btn-primary btn-book-rate" data-idx="${i}">${__("Book")}</button></td>
    </tr>`).join("");
    const dialog = new frappe.ui.Dialog({
        title: __("Available Couriers"),
        fields: [{
            fieldname: "rates_html", fieldtype: "HTML",
            options: `<table class="table table-bordered"><thead><tr>
                <th>${__("Courier")}</th><th>${__("ETA")}</th><th>${__("Rate")}</th><th></th>
            </tr></thead><tbody>${rows}</tbody></table>`
        }]
    });
    dialog.$wrapper.find(".btn-book-rate").on("click", function () {
        const rate = rates[$(this).data("idx")];
        dialog.hide();
        create_shipment(frm, rate.courier_name, rate.courier_id);
    });
    dialog.show();
}

function create_shipment(frm, courier_name, courier_id) {
    frappe.call({
        method: "manage_shipment.manage_shipment.api.create_shipment_booking",
        args: {shipment: frm.doc.name, courier_name: courier_name, courier_id: courier_id},
        freeze: true,
        freeze_message: __("Creating shipment..."),
        callback(r) {
            if (!r.message) return;
            if (r.message.warning) {
                frappe.msgprint(r.message.warning);
            } else {
                frappe.show_alert({message: __("Shipment created: {0}", [r.message.tracking_id]), indicator: "green"});
            }
            frm.reload_doc();
        }
    });
}
