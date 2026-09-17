import frappe

DEFAULT_PROVIDERS = [("Trackon","TRACKON"),("Shree Maruti","MARUTI"),("DTDC","DTDC"),("Anjani","ANJANI"),("Professional Couriers","PROFESSIONAL"),("Delhivery","DELHIVERY"),("Blue Dart","BLUEDART"),("India Post / Speed Post","INDIAPOST"),("XpressBees","XPRESSBEES"),("Ecom Express","ECOMEXPRESS"),("Gati","GATI"),("Safexpress","SAFEXPRESS"),("Ekart","EKART"),("Shadowfax","SHADOWFAX")]
SHIPROCKET_ADAPTER = "manage_shipment.manage_shipment.integrations.shiprocket.ShiprocketAdapter"
GENERIC_ADAPTER = "manage_shipment.manage_shipment.integrations.generic.GenericHTTPAdapter"


def after_install():
    _ensure_shiprocket_integration()
    for provider_name, provider_code in DEFAULT_PROVIDERS:
        name = frappe.db.get_value("Courier Service Provider", {"provider_name": provider_name}, "name")
        values = {
            "provider_code": provider_code,
            "tracking_source": "Aggregator",
            "tracking_integration": "Shiprocket",
            "adapter_path": SHIPROCKET_ADAPTER,
            "tracking_enabled": 1,
            "integration_enabled": 0,
        }
        if not name:
            values.update({"doctype": "Courier Service Provider", "provider_name": provider_name, "enabled": 1})
            frappe.get_doc(values).insert(ignore_permissions=True)
        else:
            frappe.db.set_value("Courier Service Provider", name, values, update_modified=False)
    frappe.db.commit()


def _ensure_shiprocket_integration():
    if not frappe.db.exists("Tracking API Integration", "Shiprocket"):
        frappe.get_doc({
            "doctype": "Tracking API Integration",
            "integration_name": "Shiprocket",
            "integration_type": "Aggregator",
            "enabled": 0,
            "base_url": "https://apiv2.shiprocket.in",
            "auth_url": "https://apiv2.shiprocket.in/v1/external/auth/login",
            "tracking_url": "https://apiv2.shiprocket.in/v1/external/courier/track/awb/{tracking_id}",
            "http_method": "GET",
            "tracking_param": "awb_code",
            "notes": "Create a dedicated Shiprocket API user under Settings > API. Enter the API email and password here. Credentials are stored in ERPNext and are not committed to GitHub.",
        }).insert(ignore_permissions=True)
