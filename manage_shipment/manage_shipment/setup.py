import frappe

# Comprehensive master list of Indian domestic courier / logistics providers.
# Seeded disabled (enabled=0, tracking_enabled=0) - activate the ones you actually use
# from the Courier Service Provider list; everything else stays out of the way.
DEFAULT_PROVIDERS = [
    # National express / premium
    ("Blue Dart", "BLUEDART"),
    ("DTDC", "DTDC"),
    ("FedEx India", "FEDEX"),
    ("DHL Express India", "DHL"),
    ("Aramex India", "ARAMEX"),
    ("Amazon Shipping", "AMAZONSHIP"),
    ("India Post / Speed Post", "INDIAPOST"),
    # E-commerce / D2C focused
    ("Delhivery", "DELHIVERY"),
    ("XpressBees", "XPRESSBEES"),
    ("Ecom Express", "ECOMEXPRESS"),
    ("Ekart Logistics", "EKART"),
    ("Shadowfax", "SHADOWFAX"),
    ("DP World eCommerce", "DPWORLD"),
    # Regional / traditional courier network
    ("Trackon", "TRACKON"),
    ("Shree Maruti Courier", "MARUTI"),
    ("Anjani Courier", "ANJANI"),
    ("Professional Couriers", "PROFESSIONAL"),
    ("First Flight Couriers", "FIRSTFLIGHT"),
    ("Overnite Express", "OVERNITE"),
    ("ST Courier", "STCOURIER"),
    ("Shree Tirupati Courier", "TIRUPATI"),
    ("Continental Carriers", "CONTINENTAL"),
    ("Om Logistics", "OMLOGISTICS"),
    ("Bombino Express", "BOMBINO"),
    ("Skypak", "SKYPAK"),
    # Freight / heavy & bulk logistics
    ("AllCargo Gati", "GATI"),
    ("Safexpress", "SAFEXPRESS"),
    ("TCI Express", "TCIEXPRESS"),
    ("VRL Logistics", "VRL"),
    ("V-Xpress", "VXPRESS"),
    ("Spoton Logistics", "SPOTON"),
    # Hyperlocal / last-mile aggregated fleets
    ("LoadShare", "LOADSHARE"),
    ("Borzo", "BORZO"),
    ("Wow Express", "WOWEXPRESS"),
]
SHIPROCKET_ADAPTER = "manage_shipment.manage_shipment.integrations.shiprocket.ShiprocketAdapter"
GENERIC_ADAPTER = "manage_shipment.manage_shipment.integrations.generic.GenericHTTPAdapter"


def after_install():
    _ensure_shiprocket_integration()
    _ensure_default_providers()
    frappe.db.commit()


LEGACY_PROVIDER_RENAMES = {
    "Gati": "AllCargo Gati",
    "Shree Maruti": "Shree Maruti Courier",
    "Anjani": "Anjani Courier",
    "Ekart": "Ekart Logistics",
}


def after_migrate():
    # Must run first: renames old provider names in-place (carrying every Shipment /
    # Delivery Note reference with them) so _ensure_default_providers doesn't create
    # duplicate rows for the same courier under its updated name.
    _apply_legacy_provider_renames()
    _rename_existing_providers()
    _ensure_shiprocket_integration()
    # Seed any providers newly added to DEFAULT_PROVIDERS since this site last migrated.
    # Only ever inserts missing rows - never touches a provider that already exists,
    # so nothing here can clobber an already-configured integration.
    _ensure_default_providers()
    frappe.db.commit()


def _apply_legacy_provider_renames():
    for old_name, new_name in LEGACY_PROVIDER_RENAMES.items():
        if not frappe.db.exists("Courier Service Provider", old_name) or frappe.db.exists("Courier Service Provider", new_name):
            continue
        try:
            frappe.rename_doc("Courier Service Provider", old_name, new_name, force=True, show_alert=False)
            frappe.db.set_value("Courier Service Provider", new_name, "provider_name", new_name, update_modified=False)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Manage Shipment legacy provider rename failed: {old_name} -> {new_name}")


def _ensure_default_providers():
    for provider_name, provider_code in DEFAULT_PROVIDERS:
        if frappe.db.exists("Courier Service Provider", {"provider_name": provider_name}):
            continue
        frappe.get_doc({
            "doctype": "Courier Service Provider",
            "provider_name": provider_name,
            "provider_code": provider_code,
            "enabled": 0,
            "tracking_enabled": 0,
            "tracking_source": "Aggregator",
            "tracking_integration": "Shiprocket",
            "adapter_path": SHIPROCKET_ADAPTER,
        }).insert(ignore_permissions=True)


def _rename_existing_providers():
    providers = frappe.get_all("Courier Service Provider", fields=["name", "provider_name"], order_by="creation asc")
    for row in providers:
        old_name = row.name
        provider_name = (row.provider_name or "").strip()
        if not provider_name or old_name == provider_name:
            continue
        if frappe.db.exists("Courier Service Provider", provider_name):
            continue
        try:
            frappe.rename_doc("Courier Service Provider", old_name, provider_name, merge=False, force=False)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Manage Shipment provider rename failed: {old_name} -> {provider_name}")


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
