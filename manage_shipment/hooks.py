app_name = "manage_shipment"
app_title = "Manage Shipment"
app_publisher = "Sundaram Technologies"
app_description = "Shipment and domestic courier tracking for ERPNext."
app_email = "support@sundaramtech.com"
app_license = "MIT"
app_version = "0.1.0"

required_apps = ["erpnext"]

add_to_apps_screen = [{
    "name": "manage_shipment",
    "logo": "/assets/manage_shipment/images/manage-shipment.svg",
    "title": "Manage Shipment",
    "route": "/app/shipment"
}]

scheduler_events = {
    "all": [
        "manage_shipment.manage_shipment.tasks.track_shipments"
    ]
}
