from __future__ import annotations


class CourierAdapter:
    """Base interface for every courier integration."""

    provider = None

    def __init__(self, provider_doc=None):
        self.provider_doc = provider_doc

    def track(self, tracking_id, doc=None):
        raise NotImplementedError

    @staticmethod
    def normalize_status(status, mapping=None):
        value = str(status or "").strip()
        if not value:
            return "Created"
        mapping = mapping or {}
        for key, normalized in mapping.items():
            if value.lower() == str(key).lower():
                return normalized
        text = value.lower()
        rules = (("rto delivered", "RTO Delivered"), ("delivered", "Delivered"), ("out for delivery", "Out for Delivery"), ("delivery attempted", "Delivery Attempted"), ("attempt", "Delivery Attempted"), ("ndr", "NDR / Delivery Exception"), ("exception", "NDR / Delivery Exception"), ("address", "Address Issue"), ("customer unavailable", "Customer Unavailable"), ("rto", "RTO In Transit"), ("lost", "Lost"), ("held", "Held"), ("delay", "Delayed"), ("in transit", "In Transit"), ("transit", "In Transit"), ("pickup", "Picked Up"), ("picked", "Picked Up"), ("hub", "Arrived at Destination Hub"))
        for needle, normalized in rules:
            if needle in text:
                return normalized
        return "In Transit"
