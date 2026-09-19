from __future__ import annotations

import json
import requests
import frappe
from frappe.utils import add_to_date, get_datetime, now_datetime
from .base import CourierAdapter


AUTH_PATH = "/v1/external/auth/login"
TRACK_PATH = "/v1/external/courier/track/awb/{tracking_id}"


class ShiprocketAdapter(CourierAdapter):
    """Shiprocket aggregator adapter for AWB tracking."""

    def _base_url(self):
        return (self.provider_doc.get("tracking_integration_doc").base_url or "https://apiv2.shiprocket.in").rstrip("/")

    def _integration(self):
        name = self.provider_doc.tracking_integration
        if not name:
            frappe.throw(frappe._("Tracking Integration is required for Shiprocket."))
        integration = frappe.get_cached_doc("Tracking API Integration", name)
        if not integration.enabled:
            frappe.throw(frappe._("Tracking integration {0} is disabled.").format(name))
        return integration

    def _token(self, integration):
        if integration.api_token and integration.token_expires_at:
            try:
                if get_datetime(integration.token_expires_at) > now_datetime():
                    return integration.get_password("api_token")
            except Exception:
                pass

        email = integration.api_user
        password = integration.get_password("api_password")
        if not email or not password:
            frappe.throw(frappe._("Shiprocket API User / Email and API Password are required."))

        auth_url = (integration.auth_url or (integration.base_url or "https://apiv2.shiprocket.in").rstrip("/") + AUTH_PATH).strip()
        response = requests.post(auth_url, json={"email": email, "password": password}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        token = payload.get("token")
        if not token:
            frappe.throw(frappe._("Shiprocket authentication succeeded but no token was returned."))

        expires_at = add_to_date(now_datetime(), days=9, as_datetime=True)
        integration.db_set("api_token", token, update_modified=False)
        integration.db_set("token_expires_at", expires_at, update_modified=False)
        return token

    def track(self, tracking_id, doc=None):
        integration = self._integration()
        token = self._token(integration)
        base_url = (integration.base_url or "https://apiv2.shiprocket.in").rstrip("/")
        template = integration.tracking_url or TRACK_PATH
        url = template.replace("{tracking_id}", requests.utils.quote(tracking_id, safe=""))
        if not url.startswith("http"):
            url = base_url + ("" if url.startswith("/") else "/") + url

        headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
        if integration.extra_headers:
            try:
                headers.update(json.loads(integration.extra_headers))
            except Exception:
                frappe.throw(frappe._("Extra Headers must contain valid JSON."))

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return self.parse_response(response.json())

    def get_rates(self, params):
        integration = self._integration()
        token = self._token(integration)
        url = self._base_url() + "/v1/external/courier/serviceability/"
        query = {
            "pickup_postcode": params["pickup_pincode"],
            "delivery_postcode": params["delivery_pincode"],
            "weight": params["weight"],
            "cod": 1 if params.get("cod") else 0,
        }
        if params.get("order_amount"):
            query["declared_value"] = params["order_amount"]

        response = requests.get(url, params=query, headers={"Accept": "application/json", "Authorization": f"Bearer {token}"}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        companies = ((payload.get("data") or {}).get("available_courier_companies") or [])
        return [{
            "courier_name": c.get("courier_name") or c.get("name") or "",
            "courier_id": c.get("courier_company_id") or c.get("id"),
            "rate": c.get("rate") or c.get("freight_charge") or 0,
            "estimated_days": c.get("etd") or c.get("estimated_delivery_days") or "",
            "raw": c,
        } for c in companies]

    def create_shipment(self, params):
        integration = self._integration()
        token = self._token(integration)
        headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        consignee = params["consignee"]
        order_payload = {
            "order_id": params["order_reference"],
            "order_date": frappe.utils.nowdate(),
            "pickup_location": params["pickup_location"],
            "billing_customer_name": consignee.get("name") or "",
            "billing_last_name": "",
            "billing_address": consignee.get("address") or "",
            "billing_city": consignee.get("city") or "",
            "billing_pincode": consignee.get("pincode") or "",
            "billing_state": consignee.get("state") or "",
            "billing_country": "India",
            "billing_email": consignee.get("email") or "noreply@example.com",
            "billing_phone": consignee.get("phone") or "",
            "shipping_is_billing": True,
            "order_items": params.get("items") or [{
                "name": params.get("order_reference") or "Item",
                "sku": params.get("order_reference") or "SKU",
                "units": 1,
                "selling_price": params.get("order_amount") or 0,
            }],
            "payment_method": "COD" if params.get("payment_mode") == "COD" else "Prepaid",
            "sub_total": params.get("order_amount") or 0,
            "length": params.get("length") or 10,
            "breadth": params.get("breadth") or 10,
            "height": params.get("height") or 10,
            "weight": params.get("weight") or 0.5,
        }
        response = requests.post(self._base_url() + "/v1/external/orders/create/adhoc", json=order_payload, headers=headers, timeout=30)
        response.raise_for_status()
        order_result = response.json()
        shipment_id = order_result.get("shipment_id") or (order_result.get("payload") or {}).get("shipment_id")
        if not shipment_id:
            frappe.throw(frappe._("Shiprocket order was created but no shipment_id was returned: {0}").format(json.dumps(order_result)))

        assign_payload = {"shipment_id": [shipment_id], "courier_id": params.get("courier_id") or 0}
        response = requests.post(self._base_url() + "/v1/external/courier/assign/awb", json=assign_payload, headers=headers, timeout=30)
        response.raise_for_status()
        assign_result = response.json()
        data = assign_result.get("response", {}).get("data", {}) if isinstance(assign_result.get("response"), dict) else (assign_result.get("data") or {})
        awb = data.get("awb_code") or assign_result.get("awb_code")
        courier_name = data.get("courier_name") or assign_result.get("courier_name") or ""
        if not awb:
            frappe.throw(frappe._("Shiprocket order {0} was created (shipment_id {1}) but AWB assignment did not return an AWB: {2}").format(order_result.get("order_id"), shipment_id, json.dumps(assign_result)))

        return {"tracking_id": awb, "courier_name": courier_name, "raw": {"order": order_result, "awb_assign": assign_result}}

    def parse_response(self, payload):
        shipment = self._first_dict(payload, ("shipment_track", "shipment_track_activities", "tracking_data", "data"))
        activities = self._find_list(payload, ("shipment_track_activities", "track_activities", "activities"))
        current_status = None
        current_location = None
        if isinstance(shipment, dict):
            current_status = shipment.get("current_status") or shipment.get("status") or shipment.get("current_status_name")
            current_location = shipment.get("current_location") or shipment.get("location")
        if not current_status and activities:
            current_status = activities[0].get("activity") or activities[0].get("status")
        if not current_location and activities:
            current_location = activities[0].get("location") or activities[0].get("location_name")

        event = None
        if activities:
            item = activities[0]
            event_time = item.get("date") or item.get("event_time") or item.get("timestamp") or item.get("datetime")
            event = {
                "event_datetime": get_datetime(event_time) if event_time else now_datetime(),
                "status": self.normalize_status(item.get("activity") or item.get("status") or current_status),
                "courier_status": str(item.get("activity") or item.get("status") or current_status or ""),
                "location": str(item.get("location") or item.get("location_name") or current_location or ""),
                "remarks": str(item.get("sr-status-label") or item.get("remark") or item.get("remarks") or ""),
            }
        elif current_status or current_location:
            event = {
                "event_datetime": now_datetime(),
                "status": self.normalize_status(current_status),
                "courier_status": str(current_status or ""),
                "location": str(current_location or ""),
                "remarks": "",
            }

        return {
            "status": self.normalize_status(current_status),
            "courier_status": str(current_status or ""),
            "current_location": str(current_location or ""),
            "event": event,
            "raw_response": payload,
        }

    @staticmethod
    def _first_dict(payload, keys):
        if isinstance(payload, dict):
            for key in keys:
                value = payload.get(key)
                if isinstance(value, dict):
                    return value
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    return value[0]
            return payload
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            return payload[0]
        return {}

    @staticmethod
    def _find_list(payload, keys):
        if isinstance(payload, dict):
            for key in keys:
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
            for value in payload.values():
                found = ShiprocketAdapter._find_list(value, keys)
                if found:
                    return found
        elif isinstance(payload, list):
            for value in payload:
                found = ShiprocketAdapter._find_list(value, keys)
                if found:
                    return found
        return []
