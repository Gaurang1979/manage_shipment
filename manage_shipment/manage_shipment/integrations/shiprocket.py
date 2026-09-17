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
