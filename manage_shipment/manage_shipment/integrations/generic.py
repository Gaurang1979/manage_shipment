from __future__ import annotations

import requests
import frappe
from frappe.utils import get_datetime
from .base import CourierAdapter


class GenericHTTPAdapter(CourierAdapter):
    """Configurable JSON tracking adapter for couriers without a built-in parser."""

    def track(self, tracking_id, doc=None):
        provider = self.provider_doc
        raw_url = (provider.api_url or "").strip()
        if not raw_url:
            frappe.throw(frappe._("API URL is required for {0}.").format(provider.provider_name))
        has_placeholder = "{tracking_id}" in raw_url
        url = raw_url.replace("{tracking_id}", requests.utils.quote(tracking_id, safe=""))
        headers = {"Accept": "application/json"}
        token = provider.api_token or provider.api_key
        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["X-API-Key"] = token
        params = {} if has_placeholder else {"waybill": tracking_id}
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return self.parse_response(response.json())

    def parse_response(self, payload):
        records = payload if isinstance(payload, list) else payload.get("data", payload) if isinstance(payload, dict) else {}
        if isinstance(records, list):
            records = records[0] if records else {}
        if not isinstance(records, dict):
            records = {}
        status = records.get("status") or records.get("current_status") or records.get("Status")
        location = records.get("location") or records.get("current_location") or records.get("city")
        event_time = records.get("event_datetime") or records.get("timestamp") or records.get("updated_at")
        event = None
        if status or location or event_time:
            event = {
                "event_datetime": get_datetime(event_time) if event_time else frappe.utils.now_datetime(),
                "status": self.normalize_status(status),
                "courier_status": str(status or ""),
                "location": str(location or ""),
                "remarks": str(records.get("remarks") or records.get("message") or ""),
            }
        return {"status": self.normalize_status(status), "courier_status": str(status or ""), "current_location": str(location or ""), "event": event, "raw_response": payload}
