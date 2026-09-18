import json
import frappe
from frappe import _
from frappe.utils import add_to_date, cint, getdate, now_datetime

from manage_shipment.manage_shipment.notify import notify_escalation

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
            doc.last_tracked_on = now_datetime(); doc.save()
            return {"status": doc.status, "message": _("No integration is configured for this courier yet.")}
        result = adapter.track(doc.tracking_id, doc=doc) or {}
        newly_needs_follow_up = _apply_tracking_result(doc, result)
        doc.last_tracked_on = now_datetime(); doc.save()
        if newly_needs_follow_up:
            notify_escalation(doc, _("Follow-up required"))
        return result
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Shipment tracking failed: {doc.name}")
        frappe.throw(_("Tracking failed. Check Error Log for shipment {0}.").format(doc.name))

@frappe.whitelist()
def test_tracking_integration(integration_name, tracking_id):
    if not integration_name or not tracking_id:
        frappe.throw(_("Integration and Tracking / AWB Number are required."))
    integration = frappe.get_doc("Tracking API Integration", integration_name)
    if not integration.enabled:
        frappe.throw(_("Enable the integration before testing it."))
    from manage_shipment.manage_shipment.integrations.shiprocket import ShiprocketAdapter
    provider = frappe._dict({"tracking_integration": integration.name, "tracking_source": integration.integration_type, "enabled": 1, "tracking_enabled": 1})
    if integration.name.lower() == "shiprocket":
        result = ShiprocketAdapter(provider).track(tracking_id)
    else:
        frappe.throw(_("No test adapter is registered for {0} yet.").format(integration.name))
    return {"ok": True, "status": result.get("status"), "courier_status": result.get("courier_status"), "current_location": result.get("current_location"), "message": _("Tracking API connection successful.")}

@frappe.whitelist()
def bulk_refresh_shipments(shipments):
    if isinstance(shipments, str): shipments = json.loads(shipments)
    if not isinstance(shipments, list) or not shipments: frappe.throw(_("Select at least one shipment."))
    if len(shipments) > 100: frappe.throw(_("A maximum of 100 shipments can be refreshed at once."))
    results = []
    for name in shipments:
        try:
            result = refresh_shipment(name); results.append({"shipment": name, "ok": True, "status": result.get("status"), "message": result.get("message", "")})
        except Exception as exc: results.append({"shipment": name, "ok": False, "error": str(exc)})
    return results

@frappe.whitelist()
def get_tracking_url(shipment):
    doc = frappe.get_doc("Shipment", shipment)
    provider = frappe.get_doc("Courier Service Provider", doc.courier_service_provider)
    template = (provider.tracking_url_template or "").strip()
    return template.replace("{tracking_id}", doc.tracking_id or "") if template else None

@frappe.whitelist()
def get_dashboard_data(courier=None, status=None, company=None, follow_up=None, from_date=None, to_date=None, start=0, page_length=200):
    filters = {}
    if courier: filters["courier_service_provider"] = courier
    if status: filters["status"] = status
    if company: filters["company"] = company
    if follow_up in ("1", "0"): filters["follow_up_required"] = int(follow_up)
    if from_date and to_date: filters["shipment_date"] = ["between", [getdate(from_date), getdate(to_date)]]
    elif from_date: filters["shipment_date"] = [">=", getdate(from_date)]
    elif to_date: filters["shipment_date"] = ["<=", getdate(to_date)]

    start = cint(start)
    page_length = min(cint(page_length) or 200, 500)

    total = frappe.db.count("Shipment", filters=filters)
    rows = frappe.get_all(
        "Shipment", filters=filters,
        fields=["name","tracking_id","courier_service_provider","consignee_name","customer","status","courier_status","current_location","expected_delivery_date","actual_delivery_date","last_tracked_on","follow_up_required","follow_up_date","follow_up_overdue","no_movement","company"],
        order_by="modified desc", start=start, page_length=page_length,
    )
    provider_names = {p.name: p.provider_name for p in frappe.get_all("Courier Service Provider", fields=["name", "provider_name"], limit_page_length=0)}
    for row in rows:
        row.courier_service_provider_name = provider_names.get(row.courier_service_provider, row.courier_service_provider or "")

    # Counts are queried against the full filtered set, independent of the page window above,
    # so KPIs stay accurate regardless of how many shipments are being paged through.
    counts = {"Total Shipments": total}
    status_lookup = {r.status: r.count for r in frappe.get_all("Shipment", filters=filters, fields=["status", "count(name) as count"], group_by="status")}
    for key in ("In Transit","Out for Delivery","Delivered","NDR / Delivery Exception","Delayed","RTO Initiated","RTO In Transit","RTO Delivered"):
        counts[key] = status_lookup.get(key, 0)
    counts["Follow-up Required"] = frappe.db.count("Shipment", filters={**filters, "follow_up_required": 1})
    counts["Follow-up Overdue"] = frappe.db.count("Shipment", filters={**filters, "follow_up_overdue": 1})
    counts["No Movement"] = frappe.db.count("Shipment", filters={**filters, "no_movement": 1})
    stale_cutoff = add_to_date(now_datetime(), hours=-24)
    counts["Not Updated 24h+"] = frappe.db.count("Shipment", filters={**filters, "last_tracked_on": ["<", stale_cutoff]})

    return {"counts": counts, "rows": rows, "start": start, "page_length": page_length, "total": total}

def _apply_tracking_result(doc, result):
    previous_status = doc.status
    previous_location = doc.current_location
    if result.get("status"): doc.status = result["status"]
    for field in ("courier_status","current_location","expected_delivery_date","actual_delivery_date"):
        if result.get(field): setattr(doc, field, result[field])
    event = result.get("event")
    if event and not _duplicate_event(doc, event):
        doc.append("events", event)
        doc.last_movement_on = event.get("event_datetime") or now_datetime()
        doc.no_movement = 0
    elif result.get("current_location") and result.get("current_location") != previous_location:
        doc.last_movement_on = now_datetime(); doc.no_movement = 0
    if result.get("raw_response"):
        doc.raw_response = frappe.as_json(result["raw_response"])
    if doc.status in FINAL_STATUSES: doc.tracking_enabled = 0
    newly_needs_follow_up = False
    if doc.status != previous_status and doc.status in ("NDR / Delivery Exception","Address Issue","Customer Unavailable","Delayed","Lost","Held","Delivery Attempted"):
        newly_needs_follow_up = not doc.follow_up_required
        doc.follow_up_required = 1
        if not doc.follow_up_date: doc.follow_up_date = getdate()
        if not doc.follow_up_status: doc.follow_up_status = "Pending"
    return newly_needs_follow_up

def _duplicate_event(doc, event):
    timestamp = str(event.get("event_datetime") or ""); status = event.get("status") or ""; location = event.get("location") or ""
    return any(str(row.event_datetime) == timestamp and row.status == status and row.location == location for row in doc.events)
