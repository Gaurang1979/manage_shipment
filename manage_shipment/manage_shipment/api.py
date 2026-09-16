import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def refresh_shipment(shipment):
    """Refresh a shipment through its configured provider adapter.

    Provider-specific integrations are deliberately isolated behind this API so
    adding a courier never changes the Shipment DocType or dashboard.
    """
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
