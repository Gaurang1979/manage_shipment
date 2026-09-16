import frappe
from frappe.utils import add_days, getdate, now_datetime

FINAL_STATUSES = ("Delivered", "RTO Delivered", "Cancelled")


def track_shipments():
    if not frappe.db.exists("DocType", "Shipment"):
        return
    shipments = frappe.get_all("Shipment", filters={"tracking_enabled": 1, "status": ["not in", list(FINAL_STATUSES)]}, fields=["name"], limit=200)
    for row in shipments:
        frappe.enqueue("manage_shipment.manage_shipment.api.refresh_shipment", shipment=row.name, queue="short", dedupe=True)
    mark_aged_shipments()


def mark_aged_shipments():
    cutoff = add_days(now_datetime(), -1)
    rows = frappe.get_all("Shipment", filters={"tracking_enabled": 1, "status": ["not in", list(FINAL_STATUSES)]}, fields=["name", "last_movement_on", "last_tracked_on", "follow_up_required"], limit=1000)
    for row in rows:
        last_activity = row.last_movement_on or row.last_tracked_on
        if last_activity and last_activity < cutoff:
            frappe.db.set_value("Shipment", row.name, {"no_movement": 1, "follow_up_required": 1, "follow_up_overdue": 1}, update_modified=False)
    frappe.db.commit()


def update_follow_up_flags():
    today = getdate()
    rows = frappe.get_all("Shipment", filters={"follow_up_required": 1}, fields=["name", "follow_up_date", "follow_up_status"], limit=1000)
    for row in rows:
        overdue = bool(row.follow_up_date and getdate(row.follow_up_date) < today and row.follow_up_status != "Resolved")
        frappe.db.set_value("Shipment", row.name, "follow_up_overdue", overdue, update_modified=False)
