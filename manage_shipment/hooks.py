app_name = "manage_shipment"
app_title = "Manage Shipment"
app_publisher = "Sundaram Technologies"
app_description = "Shipment and domestic courier tracking for ERPNext."
app_email = "support@sundaramtech.com"
app_license = "MIT"
app_version = "0.1.0"
required_apps = ["erpnext"]
after_install = "manage_shipment.manage_shipment.setup.after_install"
after_migrate = "manage_shipment.manage_shipment.setup.after_migrate"
add_to_apps_screen = [{"name": "manage_shipment", "title": "Manage Shipment", "route": "/app/shipment-dashboard"}]
app_include_css = "/assets/manage_shipment/css/manage_shipment.css"
doctypes_js = {"Shipment": "public/js/shipment.js", "Tracking API Integration": "public/js/tracking_api_integration.js"}
fixtures = [{"dt": "Custom Field", "filters": [["module", "=", "Manage Shipment"]]}]
doc_events = {"Delivery Note": {"on_submit": "manage_shipment.manage_shipment.doctype_events.create_shipment_from_delivery_note"}}
scheduler_events = {"cron": {"*/10 * * * *": ["manage_shipment.manage_shipment.tasks.track_shipments"], "5 * * * *": ["manage_shipment.manage_shipment.tasks.update_follow_up_flags"]}}
