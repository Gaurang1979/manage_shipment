import frappe
from frappe.utils import escape_html


def notify_escalation(shipment_doc, reason):
    """Email the courier's configured escalation address(es) when a shipment newly needs attention.

    Best-effort: never raises into the caller (tracking/ageing jobs should not fail because a
    notification could not be sent).
    """
    provider_name = shipment_doc.courier_service_provider
    if not provider_name:
        return

    recipients_raw = frappe.db.get_value("Courier Service Provider", provider_name, "escalation_emails")
    recipients = [r.strip() for r in (recipients_raw or "").split(",") if r.strip()]
    if not recipients:
        return

    subject = f"[Manage Shipment] {reason}: {shipment_doc.tracking_id or shipment_doc.name}"
    message = (
        f"<p>Shipment <b>{escape_html(shipment_doc.name)}</b> "
        f"({escape_html(shipment_doc.tracking_id or '')}) via "
        f"{escape_html(shipment_doc.courier_service_provider or '')} needs attention.</p>"
        f"<p><b>Reason:</b> {escape_html(reason)}<br>"
        f"<b>Status:</b> {escape_html(shipment_doc.status or '')}<br>"
        f"<b>Courier Status:</b> {escape_html(shipment_doc.courier_status or '')}<br>"
        f"<b>Location:</b> {escape_html(shipment_doc.current_location or '')}</p>"
        f"<p><a href='{frappe.utils.get_url_to_form('Shipment', shipment_doc.name)}'>Open Shipment</a></p>"
    )
    try:
        frappe.sendmail(recipients=recipients, subject=subject, message=message, now=False)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Manage Shipment escalation email failed: {shipment_doc.name}")
