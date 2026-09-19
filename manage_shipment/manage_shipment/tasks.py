import frappe
from frappe.utils import add_to_date, cint, getdate, now_datetime

FINAL_STATUSES = ("Delivered", "RTO Delivered", "Cancelled")
DEFAULT_AGEING_THRESHOLD_HOURS = 24


def track_shipments():
    if not frappe.db.exists("DocType", "Shipment"):
        return
    # Oldest-tracked-first: with more than 200 active shipments, a fixed unordered LIMIT
    # would keep re-tracking the same first 200 rows and starve the rest indefinitely.
    shipments = frappe.get_all(
        "Shipment",
        filters={"tracking_enabled": 1, "status": ["not in", list(FINAL_STATUSES)]},
        fields=["name"],
        order_by="last_tracked_on asc",
        limit=200,
    )
    for row in shipments:
        frappe.enqueue("manage_shipment.manage_shipment.api.refresh_shipment", shipment=row.name, queue="short", dedupe=True)


def mark_aged_shipments():
    from manage_shipment.manage_shipment.notify import notify_escalation

    thresholds = {
        p.name: cint(p.ageing_threshold_hours) or DEFAULT_AGEING_THRESHOLD_HOURS
        for p in frappe.get_all("Courier Service Provider", fields=["name", "ageing_threshold_hours"])
    }
    rows = frappe.get_all(
        "Shipment",
        filters={"tracking_enabled": 1, "status": ["not in", list(FINAL_STATUSES)]},
        fields=["name", "courier_service_provider", "last_movement_on", "last_tracked_on", "no_movement"],
        limit=1000,
    )
    now = now_datetime()
    for row in rows:
        last_activity = row.last_movement_on or row.last_tracked_on
        threshold_hours = thresholds.get(row.courier_service_provider, DEFAULT_AGEING_THRESHOLD_HOURS)
        cutoff = add_to_date(now, hours=-threshold_hours)
        if last_activity and last_activity < cutoff:
            was_already_aged = row.no_movement
            frappe.db.set_value("Shipment", row.name, {"no_movement": 1, "follow_up_required": 1, "follow_up_overdue": 1}, update_modified=False)
            if not was_already_aged:
                doc = frappe.get_doc("Shipment", row.name)
                notify_escalation(doc, frappe._("No movement for {0}h+").format(threshold_hours))
    frappe.db.commit()


def update_follow_up_flags():
    today = getdate()
    rows = frappe.get_all("Shipment", filters={"follow_up_required": 1}, fields=["name", "follow_up_date", "follow_up_status"], limit=1000)
    for row in rows:
        overdue = bool(row.follow_up_date and getdate(row.follow_up_date) < today and row.follow_up_status != "Resolved")
        frappe.db.set_value("Shipment", row.name, "follow_up_overdue", overdue, update_modified=False)
