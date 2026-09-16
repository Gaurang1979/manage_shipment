import frappe


DEFAULT_PROVIDERS = [
    ("Trackon", "TRACKON"),
    ("Shree Maruti", "MARUTI"),
    ("DTDC", "DTDC"),
    ("Anjani", "ANJANI"),
    ("Professional Couriers", "PROFESSIONAL"),
    ("Delhivery", "DELHIVERY"),
    ("Blue Dart", "BLUEDART"),
    ("India Post / Speed Post", "INDIAPOST"),
    ("XpressBees", "XPRESSBEES"),
    ("Ecom Express", "ECOMEXPRESS"),
    ("Gati", "GATI"),
    ("Safexpress", "SAFEXPRESS"),
    ("Ekart", "EKART"),
    ("Shadowfax", "SHADOWFAX"),
]


def after_install():
    for provider_name, provider_code in DEFAULT_PROVIDERS:
        if not frappe.db.exists("Courier Service Provider", {"provider_name": provider_name}):
            frappe.get_doc({
                "doctype": "Courier Service Provider",
                "provider_name": provider_name,
                "provider_code": provider_code,
                "enabled": 1,
                "integration_enabled": 0,
            }).insert(ignore_permissions=True)
    frappe.db.commit()
