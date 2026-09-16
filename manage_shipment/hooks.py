app_name = "manage_shipment"
app_title = "Manage Shipment"
app_publisher = "Sundaram Technologies"
app_description = "Shipment and domestic courier tracking for ERPNext."
app_email = "support@sundaramtech.com"
app_license = "MIT"
app_version = "0.1.0"

required_apps = ["erpnext"]

after_install = "manage_shipment.manage_shipment.setup.after_install"

add_to_apps_screen = [{
    "name": "manage_shipment",
    "title": "Manage Shipment",
    "route": "/app/shipment-dashboard"
}]

app_include_css = "/assets/manage_shipment/css/manage_shipment.css"

doctype_js = {
    "Shipment": "public/js/shipment.js"
}

scheduler_events = {
    "all": [
        "manage_shipment.manage_shipment.tasks.track_shipments"
    ]
}
