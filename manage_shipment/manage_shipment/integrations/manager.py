import frappe

from .base import CourierAdapter

SHIPROCKET_ADAPTER = "manage_shipment.manage_shipment.integrations.shiprocket.ShiprocketAdapter"


def get_adapter(provider_name):
    if not provider_name:
        return None
    provider = frappe.get_doc("Courier Service Provider", provider_name)
    if not provider.enabled or not provider.tracking_enabled:
        return None

    path = (provider.adapter_path or "").strip()
    if provider.tracking_source == "Aggregator" and provider.tracking_integration:
        integration = frappe.get_cached_doc("Tracking API Integration", provider.tracking_integration)
        if not integration.enabled:
            return None
        provider.tracking_integration_doc = integration
        if integration.integration_name.lower() == "shiprocket":
            path = SHIPROCKET_ADAPTER

    if not path:
        return None

    adapter_class = frappe.get_attr(path)
    if not issubclass(adapter_class, CourierAdapter):
        frappe.throw(f"Courier adapter must inherit from CourierAdapter: {path}")
    return adapter_class(provider)
