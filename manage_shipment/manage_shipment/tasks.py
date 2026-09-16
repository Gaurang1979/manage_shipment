import frappe
from frappe.utils import add_days, get_datetime, now_datetime


def track_shipments():
    """Queue tracking for active shipments without making provider-specific API calls here."""
    if not frappe.db.exists("DocType", "Shipment"):
        return

    shipments = frappe.get_all(
        "Shipment",
        filters={
            "tracking_enabled": 1,
            "status": ["not in", ["Delivered", "RTO Delivered", "Cancelled"]],
        },
        fields=["name", "last_tracked_on", "status"],
        limit=200,
    )

    for row in shipments:
        frappe.enqueue(
            "manage_shipment.manage_shipment.api.refresh_shipment",
            shipment=row.name,
            queue="short",
            dedupe=True,
        )


def mark_aged_shipments():
    """Reserved for SLA/no-movement rules once provider integrations are enabled."""
    cutoff = add_days(now_datetime(), -2)
    frappe.db.sql(
        """
        update `tabShipment`
        set follow_up_required = 1
        where tracking_enabled = 1
          and status not in ('Delivered', 'RTO Delivered', 'Cancelled')
          and last_tracked_on is not null
          and last_tracked_on < %s
        """,
        cutoff,
    )
