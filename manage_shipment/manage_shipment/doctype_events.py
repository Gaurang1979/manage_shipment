import frappe


def create_shipment_from_delivery_note(doc, method=None):
    """Create/update Shipment when a Delivery Note has courier + AWB fields."""
    if not getattr(doc, "shipment_tracking_id", None) or not getattr(doc, "shipment_courier_service_provider", None):
        return
    existing = frappe.db.get_value(
        "Shipment",
        {"tracking_id": doc.shipment_tracking_id, "courier_service_provider": doc.shipment_courier_service_provider},
        "name",
    )
    if existing:
        shipment = frappe.get_doc("Shipment", existing)
        shipment.reference_doctype = "Delivery Note"
        shipment.reference_name = doc.name
        shipment.save(ignore_permissions=True)
    else:
        shipment = frappe.get_doc({"doctype": "Shipment", "courier_service_provider": doc.shipment_courier_service_provider, "tracking_id": doc.shipment_tracking_id, "shipment_date": doc.posting_date, "shipment_type": "Parcel", "status": "Created", "customer": doc.customer, "consignee_name": doc.customer_name, "company": doc.company, "reference_doctype": "Delivery Note", "reference_name": doc.name})
        shipment.insert(ignore_permissions=True)
    if hasattr(doc, "shipment_reference"):
        frappe.db.set_value(doc.doctype, doc.name, "shipment_reference", shipment.name, update_modified=False)
    return shipment.name
