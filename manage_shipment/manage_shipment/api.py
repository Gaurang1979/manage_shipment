import json
import frappe
from frappe import _
from frappe.utils import getdate, now_datetime

FINAL_STATUSES = ("Delivered", "RTO Delivered", "Cancelled")

@frappe.whitelist()
def refresh_shipment(shipment):
    doc = frappe.get_doc("Shipment", shipment)
    if not doc.tracking_enabled:
        return {"status": doc.status, "message": _("Tracking is disabled.")}
    from manage_shipment.manage_shipment.integrations.manager import get_adapter
    try:
        adapter = get_adapter(doc.courier_service_provider)
        if not adapter:
            doc.last_tracked_on = now_datetime(); doc.save(ignore_permissions=True)
            return {"status": doc.status, "message": _("No integration is configured for this courier yet.")}
        result = adapter.track(doc.tracking_id, doc=doc) or {}
        _apply_tracking_result(doc, result)
        doc.last_tracked_on = now_datetime(); doc.save(ignore_permissions=True)
        return result
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Shipment tracking failed: {doc.name}")
        frappe.throw(_("Tracking failed. Check Error Log for shipment {0}.").format(doc.name))

@frappe.whitelist()
def bulk_refresh_shipments(shipments):
    if isinstance(shipments, str): shipments = json.loads(shipments)
    if not isinstance(shipments, list) or not shipments: frappe.throw(_("Select at least one shipment."))
    if len(shipments) > 100: frappe.throw(_("A maximum of 100 shipments can be refreshed at once."))
    results = []
    for name in shipments:
        try:
            result = refresh_shipment(name)
            results.append({"shipment": name, "ok": True, "status": result.get("status"), "message": result.get("message", "")})
        except Exception as exc:
            results.append({"shipment": name, "ok": False, "error": str(exc)})
    return results

@frappe.whitelist()
def get_tracking_url(shipment):
    doc = frappe.get_doc("Shipment", shipment)
    provider = frappe.get_doc("Courier Service Provider", doc.courier_service_provider)
    template = (provider.tracking_url_template or "").strip()
    return template.replace("{tracking_id}", doc.tracking_id or "") if template else None

@frappe.whitelist()
def get_dashboard_data(courier=None, status=None, company=None, follow_up=None, from_date=None, to_date=None):
    filters = {}
    if courier: filters["courier_service_provider"] = courier
    if status: filters["status"] = status
    if company: filters["company"] = company
    if follow_up in ("1", "0"): filters["follow_up_required"] = int(follow_up)
    if from_date and to_date: filters["shipment_date"] = ["between", [getdate(from_date), getdate(to_date)]]
    elif from_date: filters["shipment_date"] = [">=", getdate(from_date)]
    elif to_date: filters["shipment_date"] = ["<=", getdate(to_date)]
    rows = frappe.get_all("Shipment", filters=filters, fields=["name","tracking_id","courier_service_provider","consignee_name","customer","status","courier_status","current_location","expected_delivery_date","actual_delivery_date","last_tracked_on","follow_up_required","follow_up_date","follow_up_overdue","company"], order_by="modified desc", limit=500)
    counts = {"Total Shipments": len(rows)}
    for key in ("In Transit","Out for Delivery","Delivered","NDR / Delivery Exception","Delayed","RTO Initiated","RTO In Transit","RTO Delivered"):
        counts[key] = sum(1 for row in rows if row.status == key)
    counts["Follow-up Required"] = sum(1 for row in rows if row.follow_up_required)
    counts["Follow-up Overdue"] = sum(1 for row in rows if row.follow_up_overdue)
    counts["Not Updated 24h+"] = sum(1 for row in rows if row.last_tracked_on and (now_datetime() - row.last_tracked_on).total_seconds() > 86400)
    return {"counts": counts, "rows": rows}

def _apply_tracking_result(doc, result):
    previous_status = doc.status
    if result.get("status"): doc.status = result["status"]
    for field in ("courier_status","current_location","expected_delivery_date","actual_delivery_date"):
        if result.get(field): setattr(doc, field, result[field])
    event = result.get("event")
    if event and not _duplicate_event(doc, event): doc.append("events", event)
    if doc.status in FINAL_STATUSES: doc.tracking_enabled = 0
    if doc.status != previous_status and doc.status in ("NDR / Delivery Exception","Address Issue","Customer Unavailable","Delayed","Lost","Held","Delivery Attempted"):
        doc.follow_up_required = 1
        if not doc.follow_up_date: doc.follow_up_date = getdate()
        if not doc.follow_up_status: doc.follow_up_status = "Pending"

def _duplicate_event(doc, event):
    timestamp = str(event.get("event_datetime") or "")
    status = event.get("status") or ""
    location = event.get("location") or ""
    return any(str(row.event_datetime) == timestamp and row.status == status and row.location == location for row in doc.events)
