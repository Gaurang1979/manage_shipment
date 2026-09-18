frappe.pages['shipment-dashboard'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({parent: wrapper, title: __('Manage Shipment'), single_column: true});
    $(frappe.render_template('shipment_dashboard', {})).appendTo(page.main);
    const root = $(page.main), filters = root.find('.shipment-filters'), kpis = root.find('.shipment-kpis'), table = root.find('.shipment-table-wrap');
    const summary = root.find('.shipment-status-summary'), followup = root.find('.shipment-followup-summary');
    const PAGE_LENGTH = 200;
    let currentRows = [], currentTotal = 0;

    function make_filter(fieldname, label, options, type='Select') {
        const holder = $('<div class="col-md-3 col-sm-6"></div>').appendTo(filters);
        const df = {fieldname, label, fieldtype: type, options: options ? [''].concat(options) : undefined};
        const control = frappe.ui.form.make_control({parent: holder, df, render_input: true}); control.refresh(); return control;
    }
    const courier = make_filter('courier', __('Courier'), []);
    const status = make_filter('status', __('Status'), ['Created','Picked Up','In Transit','Arrived at Destination Hub','Out for Delivery','Delivered','Delivery Attempted','NDR / Delivery Exception','Address Issue','Customer Unavailable','Held','Delayed','Lost','RTO Initiated','RTO In Transit','RTO Delivered','Cancelled']);
    const follow_up = make_filter('follow_up', __('Follow-up'), ['1','0']);
    const company = make_filter('company', __('Company'), []);
    const from_date = make_filter('from_date', __('From Date'), null, 'Date');
    const to_date = make_filter('to_date', __('To Date'), null, 'Date');

    root.find('.btn-new-shipment').on('click', () => frappe.new_doc('Shipment'));
    root.find('.btn-bulk-refresh').on('click', bulk_refresh);
    [courier,status,follow_up,company,from_date,to_date].forEach(c => c.$input && c.$input.on('change', () => load(true)));

    // Event delegation: rows are replaced/appended on every load(), so bind on the
    // static wrapper once instead of re-binding per row.
    table.on('click', '.btn-row-refresh', function() {
        const name = $(this).data('name'), $btn = $(this);
        $btn.prop('disabled', true).text(__('Refreshing...'));
        frappe.call({method:'manage_shipment.manage_shipment.api.refresh_shipment', args:{shipment:name}, callback(){ load(true); }, error(){ $btn.prop('disabled', false).text(__('Refresh')); }});
    });

    function load(reset) {
        if (reset) { currentRows = []; }
        const start = reset ? 0 : currentRows.length;
        frappe.call({method:'manage_shipment.manage_shipment.api.get_dashboard_data', args:{courier:courier.get_value(),status:status.get_value(),follow_up:follow_up.get_value(),company:company.get_value(),from_date:from_date.get_value(),to_date:to_date.get_value(),start:start,page_length:PAGE_LENGTH}, callback(r){
            const data=r.message||{counts:{},rows:[],total:0};
            currentRows = reset ? (data.rows||[]) : currentRows.concat(data.rows||[]);
            currentTotal = data.total||0;
            render_kpis(data.counts||{}); render_table(currentRows); render_summary(currentRows,data.counts||{});
        }});
    }
    function render_kpis(c) {
        const items=[['Total Shipments','Total Shipments'],['In Transit','In Transit'],['Out for Delivery','Out for Delivery'],['Delivered','Delivered'],['NDR / Delivery Exception','NDR / Exception'],['Delayed','Delayed'],['RTO In Transit','RTO'],['Follow-up Required','Follow-up'],['Follow-up Overdue','Overdue'],['Not Updated 24h+','No Update 24h+']];
        kpis.empty(); items.forEach(([key,label])=>kpis.append(`<div class="col-lg-2 col-md-3 col-sm-4 shipment-kpi"><div class="shipment-kpi-card"><div class="text-muted small">${__(label)}</div><div class="shipment-kpi-value">${c[key]||0}</div></div></div>`));
    }
    function render_table(rows) {
        root.find('.shipment-result-count').text(`${rows.length} ${__('of')} ${currentTotal} ${__('records')}`);
        if(!rows.length){table.html(`<div class="text-muted text-center p-5">${__('No shipments found')}</div>`);return;}
        const body=rows.map(r=>`<tr><td><input type="checkbox" class="shipment-select" data-name="${frappe.utils.escape_html(r.name)}"></td><td><a href="/app/shipment/${encodeURIComponent(r.name)}">${frappe.utils.escape_html(r.tracking_id||r.name)}</a><div class="text-muted small">${frappe.utils.escape_html(r.courier_service_provider_name||'')}</div></td><td>${frappe.utils.escape_html(r.consignee_name||r.customer||'')}</td><td><span class="indicator-pill ${status_class(r.status)}">${frappe.utils.escape_html(r.status||'')}</span><div class="text-muted small">${frappe.utils.escape_html(r.courier_status||'')}</div></td><td>${frappe.utils.escape_html(r.current_location||'')}</td><td>${frappe.utils.escape_html(r.expected_delivery_date||'')}<div class="text-muted small">${frappe.utils.escape_html(r.last_tracked_on||'')}</div></td><td>${r.follow_up_required?'<span class="indicator-pill red">Follow-up</span>':''}${r.follow_up_overdue?'<span class="indicator-pill orange ml-1">Overdue</span>':''}</td><td class="text-nowrap"><button class="btn btn-xs btn-default btn-row-refresh" data-name="${frappe.utils.escape_html(r.name)}">${__('Refresh')}</button> <a class="btn btn-xs btn-default" href="/app/shipment/${encodeURIComponent(r.name)}">${__('View')}</a></td></tr>`).join('');
        const more = currentRows.length < currentTotal ? `<div class="text-center p-2"><button class="btn btn-sm btn-default btn-load-more">${__('Load more')} (${currentTotal - currentRows.length} ${__('remaining')})</button></div>` : '';
        table.html(`<div class="table-responsive"><table class="table table-bordered table-hover"><thead><tr><th></th><th>${__('AWB / Tracking')}</th><th>${__('Consignee')}</th><th>${__('Status')}</th><th>${__('Location')}</th><th>${__('Delivery / Updated')}</th><th>${__('Follow-up')}</th><th>${__('Actions')}</th></tr></thead><tbody>${body}</tbody></table></div>${more}`);
        table.find('.btn-load-more').on('click', () => load(false));
    }
    function render_summary(rows,c) {
        const groups={}; rows.forEach(r=>groups[r.status]=(groups[r.status]||0)+1);
        const total=rows.length||1; summary.empty(); Object.keys(groups).sort((a,b)=>groups[b]-groups[a]).slice(0,10).forEach(s=>summary.append(`<div class="shipment-summary-row"><div><span class="indicator-pill ${status_class(s)}">${frappe.utils.escape_html(s)}</span></div><div class="shipment-summary-count">${groups[s]} <span class="text-muted small">(${Math.round(groups[s]*100/total)}%)</span></div></div>`));
        followup.html(`<div class="shipment-followup-box"><div><strong>${c['Follow-up Required']||0}</strong><span>Follow-up Required</span></div><div><strong>${c['Follow-up Overdue']||0}</strong><span>Overdue</span></div><div><strong>${c['Not Updated 24h+']||0}</strong><span>No Update 24h+</span></div></div>`);
    }
    function status_class(v){if(v==='Delivered'||v==='RTO Delivered')return'green';if(['Delayed','NDR / Delivery Exception','Lost','Address Issue'].includes(v))return'red';if(v==='Out for Delivery')return'orange';return'blue';}
    function bulk_refresh(){const names=[];root.find('.shipment-select:checked').each(function(){names.push($(this).data('name'));});if(!names.length){frappe.msgprint(__('Select at least one shipment.'));return;}frappe.call({method:'manage_shipment.manage_shipment.api.bulk_refresh_shipments',args:{shipments:names},freeze:true,freeze_message:__('Refreshing shipments...'),callback(){load(true);}});}

    frappe.call({method:'frappe.client.get_list',args:{doctype:'Courier Service Provider',fields:['name','provider_name'],filters:{enabled:1},limit_page_length:100},callback(r){courier.df.options=[''].concat((r.message||[]).map(x=>x.name));courier.refresh();load(true);}});
    frappe.call({method:'frappe.client.get_list',args:{doctype:'Company',fields:['name'],limit_page_length:100},callback(r){company.df.options=[''].concat((r.message||[]).map(x=>x.name));company.refresh();}});
};
