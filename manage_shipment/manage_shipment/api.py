import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def refresh_shipment(shipment):
    """Refresh a shipment through its configured provider adapter."""
    doc = frappe.get_doc("Shipment", shipment)
    if not doc.tracking_enabled:
        return {"status": doc.status, "message": _("Tracking is disabled.")}

    from manage_shipment.manage_shipment.integrations.manager import get_adapter

    adapter = get_adapter(doc.courier_service_provider)
    if not adapter:
        doc.last_tracked_on = now_datetime()
        doc.save(ignore_permissions=True)
        return {"status": doc.status, "message": _("No integration is configured for this courier yet.")}

    result = adapter.track(doc.tracking_id, doc=doc) or {}
    _apply_tracking_result(doc, result)
    doc.last_tracked_on = now_datetime()
    doc.save(ignore_permissions=True)
    return result


@frappe.whitelist()
def get_tracking_url(shipment):
    doc = frappe.get_doc("Shipment", shipment)
    provider = frappe.get_doc("Courier Service Provider", doc.courier_service_provider)
    template = (provider.tracking_url_template or "").strip()
    if not template:
        return None
    return template.replace("{tracking_id}", doc.tracking_id or "")


@frappe.whitelist()
def get_dashboard_data(courier=None, status=None, company=None, follow_up=None):
    filters = {}
    if courier:
        filters["courier_service_provider"] = courier
    if status:
        filters["status"] = status
    if company:
        filters["company"] = company
    if follow_up == "1":
        filters["follow_up_required"] = 1
    elif follow_up == "0":
        filters["follow_up_required"] = 0

    rows = frappe.get_all(
        "Shipment",
        filters=filters,
        fields=["name", "tracking_id", "courier_service_provider", "consignee_name", "status", "courier_status", "current_location", "expected_delivery_date", "last_tracked_on", "follow_up_required", "follow_up_date", "follow_up_overdue"],
        order_by="modified desc",
        limit=500,
    )

    counts = {"Total Shipments": len(rows)}
    for key in ["In Transit", "Out for Delivery", "Delivered", "NDR / Delivery Exception", "Delayed", "RTO Initiated", "RTO In Transit", "Follow-up Required"]:
        counts[key] = sum(1 for r in rows if (r.follow_up_required if key == "Follow-up Required" else r.status == key))

    return {"counts": counts, "rows": rows}


def _apply_tracking_result(doc, result):
    if result.get("status"):
        doc.status = result["status"]
    if result.get("courier_status"):
        doc.courier_status = result["courier_status"]
    if result.get("current_location"):
        doc.current_location = result["current_location"]
    if result.get("expected_delivery_date"):
        doc.expected_delivery_date = result["expected_delivery_date"]
    if result.get("actual_delivery_date"):
        doc.actual_delivery_date = result["actual_delivery_date"]

    event = result.get("event")
    if event:
        doc.append("events", event)
