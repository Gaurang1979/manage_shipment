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


def _get_booking_adapter(integration):
    if not integration.enabled:
        frappe.throw(_("Tracking integration {0} is disabled.").format(integration.name))
    path = (integration.adapter_path or "").strip()
    if not path:
        frappe.throw(_("Set Adapter Python Path on Tracking API Integration {0} before using it for Check Rates / Create Shipment.").format(integration.name))
    try:
        adapter_class = frappe.get_attr(path)
    except Exception:
        frappe.throw(_("Could not import adapter {0} - check the Adapter Python Path.").format(path))
    provider_stub = frappe._dict({"tracking_integration": integration.name})
    return adapter_class(provider_stub)


def _consignee_params(doc):
    return {
        "name": doc.consignee_name or doc.customer or "",
        "phone": doc.consignee_phone or "",
        "email": doc.consignee_email or "",
        "address": doc.address or "",
        "city": doc.city or "",
        "state": doc.state or "",
        "pincode": doc.pincode or "",
    }


@frappe.whitelist()
def get_shipping_rates(shipment):
    doc = frappe.get_doc("Shipment", shipment)
    doc.check_permission("write")
    if not doc.booking_integration:
        frappe.throw(_("Set Booking Integration before checking rates."))
    if not doc.pincode:
        frappe.throw(_("Set the consignee Pincode before checking rates."))
    if not doc.pickup_pincode:
        frappe.throw(_("Set Pickup Pincode before checking rates."))
    if not doc.package_weight:
        frappe.throw(_("Set Weight (kg) before checking rates."))

    integration = frappe.get_cached_doc("Tracking API Integration", doc.booking_integration)
    adapter = _get_booking_adapter(integration)
    rates = adapter.get_rates({
        "pickup_pincode": doc.pickup_pincode,
        "delivery_pincode": doc.pincode,
        "weight": doc.package_weight,
        "cod": doc.payment_mode == "COD",
        "order_amount": doc.order_amount,
    })
    return rates


@frappe.whitelist()
def create_shipment_booking(shipment, courier_name=None, courier_id=None):
    doc = frappe.get_doc("Shipment", shipment)
    doc.check_permission("write")
    if doc.tracking_id:
        frappe.throw(_("This Shipment already has a Tracking / AWB Number ({0}) - booking again is not supported here.").format(doc.tracking_id))
    if not doc.booking_integration:
        frappe.throw(_("Set Booking Integration before creating a shipment."))
    if not doc.pickup_location:
        frappe.throw(_("Set Pickup Location before creating a shipment."))
    for label, value in ((_("Weight (kg)"), doc.package_weight), (_("Pincode"), doc.pincode), (_("Consignee Name"), doc.consignee_name), (_("Address"), doc.address)):
        if not value:
            frappe.throw(_("Set {0} before creating a shipment.").format(label))

    integration = frappe.get_cached_doc("Tracking API Integration", doc.booking_integration)
    adapter = _get_booking_adapter(integration)
    result = adapter.create_shipment({
        "order_reference": doc.reference_name or doc.name,
        "pickup_location": doc.pickup_location,
        "consignee": _consignee_params(doc),
        "weight": doc.package_weight,
        "length": doc.package_length,
        "breadth": doc.package_breadth,
        "height": doc.package_height,
        "payment_mode": doc.payment_mode,
        "order_amount": doc.order_amount,
        "cod_amount": doc.cod_amount,
        "courier_id": courier_id,
    })

    doc.tracking_id = result["tracking_id"]
    doc.raw_response = frappe.as_json(result.get("raw"))
    matched = _match_courier_provider(integration.name, courier_name or result.get("courier_name"))
    warning = None
    if matched:
        doc.courier_service_provider = matched
        doc.tracking_enabled = 1
    else:
        warning = _(
            "Shipment booked (AWB: {0}) but no Courier Service Provider matching '{1}' "
            "was found for this integration - set Courier Service Provider manually so "
            "automatic tracking picks it up."
        ).format(result["tracking_id"], courier_name or result.get("courier_name") or "?")
    doc.save()
    return {"tracking_id": result["tracking_id"], "courier_name": courier_name or result.get("courier_name"), "warning": warning}


def _match_courier_provider(integration_name, courier_name):
    if not courier_name:
        return None
    needle = str(courier_name).strip().lower()
    candidates = frappe.get_all(
        "Courier Service Provider",
        filters={"tracking_source": "Aggregator", "tracking_integration": integration_name},
        fields=["name", "provider_name"],
    )
    for row in candidates:
        provider_lower = (row.provider_name or "").strip().lower()
        if provider_lower and (provider_lower in needle or needle in provider_lower):
            return row.name
    return None
