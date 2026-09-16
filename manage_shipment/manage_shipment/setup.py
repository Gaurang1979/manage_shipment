import frappe

DEFAULT_PROVIDERS = [("Trackon","TRACKON"),("Shree Maruti","MARUTI"),("DTDC","DTDC"),("Anjani","ANJANI"),("Professional Couriers","PROFESSIONAL"),("Delhivery","DELHIVERY"),("Blue Dart","BLUEDART"),("India Post / Speed Post","INDIAPOST"),("XpressBees","XPRESSBEES"),("Ecom Express","ECOMEXPRESS"),("Gati","GATI"),("Safexpress","SAFEXPRESS"),("Ekart","EKART"),("Shadowfax","SHADOWFAX")]
GENERIC_ADAPTER = "manage_shipment.manage_shipment.integrations.generic.GenericHTTPAdapter"


def after_install():
    for provider_name, provider_code in DEFAULT_PROVIDERS:
        name = frappe.db.get_value("Courier Service Provider", {"provider_name": provider_name}, "name")
        if not name:
            frappe.get_doc({"doctype":"Courier Service Provider","provider_name":provider_name,"provider_code":provider_code,"enabled":1,"integration_enabled":0,"adapter_path":GENERIC_ADAPTER}).insert(ignore_permissions=True)
        else:
            frappe.db.set_value("Courier Service Provider", name, {"provider_code":provider_code,"adapter_path":GENERIC_ADAPTER}, update_modified=False)
    frappe.db.commit()
