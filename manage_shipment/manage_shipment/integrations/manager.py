import frappe

from .base import CourierAdapter


def get_adapter(provider_name):
    if not provider_name:
        return None
    provider = frappe.get_doc("Courier Service Provider", provider_name)
    if not provider.enabled or not provider.integration_enabled:
        return None

    path = (provider.adapter_path or "").strip()
    if not path:
        return None

    module_name, class_name = path.rsplit(".", 1)
    adapter_class = frappe.get_attr(path)
    if not issubclass(adapter_class, CourierAdapter):
        frappe.throw(f"Courier adapter must inherit from CourierAdapter: {path}")
    return adapter_class(provider)
