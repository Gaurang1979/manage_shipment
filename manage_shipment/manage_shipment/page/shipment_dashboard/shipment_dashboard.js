frappe.pages['shipment-dashboard'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({parent: wrapper, title: __('Manage Shipment'), single_column: true});
    $(frappe.render_template('shipment_dashboard', {})).appendTo(page.main);

    const root = $(page.main);
    const filters = root.find('.shipment-filters');
    const kpis = root.find('.shipment-kpis');
    const table = root.find('.shipment-table-wrap');

    function make_filter(fieldname, label, options) {
        const control = frappe.ui.form.make_control({
            parent: $('<div class="col-sm-3"></div>').appendTo(filters),
            df: {fieldname, label, fieldtype: 'Select', options: [''].concat(options || [])},
            render_input: true
        });
        control.refresh();
        return control;
    }

    const courier = make_filter('courier', __('Courier Service Provider'), []);
    const status = make_filter('status', __('Status'), ['Created','Picked Up','In Transit','Arrived at Destination Hub','Out for Delivery','Delivered','Delivery Attempted','NDR / Delivery Exception','Delayed','RTO Initiated','RTO In Transit','RTO Delivered','Cancelled']);
    const follow_up = make_filter('follow_up', __('Follow-up'), ['1', '0']);

    root.find('.btn-new-shipment').on('click', () => frappe.new_doc('Shipment'));

    function load() {
        frappe.call({
            method: 'manage_shipment.manage_shipment.api.get_dashboard_data',
            args: {courier: courier.get_value(), status: status.get_value(), follow_up: follow_up.get_value()},
            callback(r) {
                const data = r.message || {counts: {}, rows: []};
                render_kpis(data.counts || {});
                render_table(data.rows || []);
            }
        });
    }

    function render_kpis(counts) {
        const items = [
            ['Total Shipments', 'Total Shipments'], ['In Transit', 'In Transit'],
            ['Out for Delivery', 'Out for Delivery'], ['Delivered', 'Delivered'],
            ['NDR / Delivery Exception', 'NDR / Exception'], ['Delayed', 'Delayed'],
            ['RTO Initiated', 'RTO'], ['Follow-up Required', 'Follow-up']
        ];
        kpis.empty();
        items.forEach(([key, label]) => {
            $(`<div class="col-sm-3 col-md-3 shipment-kpi"><div class="shipment-kpi-card"><div class="text-muted">${__(label)}</div><div class="shipment-kpi-value">${counts[key] || 0}</div></div></div>`).appendTo(kpis);
        });
    }

    function render_table(rows) {
        if (!rows.length) {
            table.html(`<div class="text-muted text-center p-5">${__('No shipments found')}</div>`);
            return;
        }
        const body = rows.map(r => `<tr>
            <td><a href="/app/shipment/${encodeURIComponent(r.name)}">${frappe.utils.escape_html(r.tracking_id || r.name)}</a></td>
            <td>${frappe.utils.escape_html(r.courier_service_provider || '')}</td>
            <td>${frappe.utils.escape_html(r.consignee_name || '')}</td>
            <td><span class="indicator-pill ${status_class(r.status)}">${frappe.utils.escape_html(r.status || '')}</span></td>
            <td>${frappe.utils.escape_html(r.current_location || '')}</td>
            <td>${frappe.utils.escape_html(r.expected_delivery_date || '')}</td>
            <td>${r.follow_up_required ? '<span class="indicator-pill red">Follow-up</span>' : ''}</td>
        </tr>`).join('');
        table.html(`<div class="table-responsive"><table class="table table-bordered table-hover"><thead><tr><th>AWB / Tracking</th><th>Courier</th><th>Consignee</th><th>Status</th><th>Location</th><th>Expected Delivery</th><th>Action</th></tr></thead><tbody>${body}</tbody></table></div>`);
    }

    function status_class(value) {
        if (value === 'Delivered' || value === 'RTO Delivered') return 'green';
        if (value === 'Delayed' || value === 'NDR / Delivery Exception' || value === 'Lost') return 'red';
        if (value === 'Out for Delivery') return 'orange';
        return 'blue';
    }

    [courier, status, follow_up].forEach(c => c.$input.on('change', load));
    frappe.call({method: 'frappe.client.get_list', args: {doctype: 'Courier Service Provider', fields: ['name'], filters: {enabled: 1}, limit_page_length: 100}, callback(r) {
        const names = (r.message || []).map(x => x.name);
        courier.df.options = [''].concat(names);
        courier.refresh();
        load();
    }});
};
