from __future__ import annotations

import json
import requests
import frappe
from frappe.utils import add_to_date, get_datetime, now_datetime
from .base import CourierAdapter

DEFAULT_BASE_URL = "https://api-v2.nimbuspost.com"
AUTH_PATH = "/v2/users/login"
TRACK_PATH = "/v2/tracking/bulk"


class NimbusPostAdapter(CourierAdapter):
    """NimbusPost aggregator adapter.

    Auth: email/password -> POST {auth_url} -> Bearer token (confirmed against
    NimbusPost's official PHP SDK and Postman docs: same email+password->bearer-token
    pattern as Shiprocket).

    Tracking: NimbusPost's v2 endpoint is a *bulk* endpoint (POST {tracking_url} with
    {"awb": [...]})  -  called here with a single AWB per request, since this adapter
    tracks one shipment at a time. Response field names for the v2 API were not fully
    confirmed (their reference docs are JS-rendered and couldn't be read directly), so
    parse_response() tries several common key names defensively. If status/location
    come back empty on a real call, check the stored raw_response on the Shipment
    Event / Error Log and adjust the key names below to match.
    """

    def _integration(self):
        name = self.provider_doc.tracking_integration
        if not name:
            frappe.throw(frappe._("Tracking Integration is required for NimbusPost."))
        integration = frappe.get_cached_doc("Tracking API Integration", name)
        if not integration.enabled:
            frappe.throw(frappe._("Tracking integration {0} is disabled.").format(name))
        return integration

    def _base_url(self, integration):
        return (integration.base_url or DEFAULT_BASE_URL).rstrip("/")

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
            frappe.throw(frappe._("NimbusPost API User / Email and API Password are required."))

        auth_url = (integration.auth_url or self._base_url(integration) + AUTH_PATH).strip()
        response = requests.post(
            auth_url,
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        token = data.get("access_token") or payload.get("access_token") or payload.get("token")
        if not token:
            frappe.throw(frappe._(
                "NimbusPost authentication succeeded (HTTP {0}) but no token was found in the "
                "response. Confirm the Authentication URL matches NimbusPost's current login "
                "endpoint and check the response shape in the Error Log."
            ).format(response.status_code))

        # NimbusPost doesn't document a fixed token TTL in the sources checked; cache
        # conservatively and re-auth well before any reasonable expiry.
        expires_at = add_to_date(now_datetime(), hours=12, as_datetime=True)
        integration.db_set("api_token", token, update_modified=False)
        integration.db_set("token_expires_at", expires_at, update_modified=False)
        return token

    def track(self, tracking_id, doc=None):
        integration = self._integration()
        token = self._token(integration)
        url = (integration.tracking_url or self._base_url(integration) + TRACK_PATH).strip()

        headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        if integration.extra_headers:
            try:
                headers.update(json.loads(integration.extra_headers))
            except Exception:
                frappe.throw(frappe._("Extra Headers must contain valid JSON."))

        response = requests.post(url, json={"awb": [tracking_id]}, headers=headers, timeout=30)
        response.raise_for_status()
        return self.parse_response(response.json(), tracking_id)

    def parse_response(self, payload, tracking_id):
        record = self._find_record(payload, tracking_id)
        activities = self._find_list(record, ("scans", "tracking_activities", "activities", "checkpoints", "history", "track_activities"))

        current_status = None
        current_location = None
        if isinstance(record, dict):
            current_status = record.get("status") or record.get("current_status") or record.get("shipment_status")
            current_location = record.get("current_location") or record.get("location") or record.get("current_city")
        if not current_status and activities:
            current_status = activities[0].get("status") or activities[0].get("activity") or activities[0].get("remark")
        if not current_location and activities:
            current_location = activities[0].get("location") or activities[0].get("city")

        event = None
        if activities:
            item = activities[0]
            event_time = item.get("date") or item.get("timestamp") or item.get("datetime") or item.get("scan_date")
            event = {
                "event_datetime": get_datetime(event_time) if event_time else now_datetime(),
                "status": self.normalize_status(item.get("status") or item.get("activity") or current_status),
                "courier_status": str(item.get("status") or item.get("activity") or current_status or ""),
                "location": str(item.get("location") or item.get("city") or current_location or ""),
                "remarks": str(item.get("remark") or item.get("remarks") or item.get("description") or ""),
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
    def _find_record(payload, tracking_id):
        """The bulk response holds results for potentially multiple AWBs - pick out
        the one matching this tracking_id, defensively, across a few likely shapes."""
        candidates = []
        if isinstance(payload, dict):
            matched_container = False
            for key in ("data", "result", "results", "tracking_data", "shipments"):
                value = payload.get(key)
                if isinstance(value, list):
                    candidates = value
                    matched_container = True
                    break
                if isinstance(value, dict):
                    if tracking_id in value:
                        return value[tracking_id]
                    candidates = list(value.values())
                    matched_container = True
                    break
            if not matched_container:
                candidates = [payload]
        elif isinstance(payload, list):
            candidates = payload

        for item in candidates:
            if isinstance(item, dict) and str(item.get("awb") or item.get("awb_number") or item.get("tracking_id") or "") == str(tracking_id):
                return item
        for item in candidates:
            if isinstance(item, dict):
                return item
        return {}

    @staticmethod
    def _find_list(payload, keys):
        if isinstance(payload, dict):
            for key in keys:
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        return []
