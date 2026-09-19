from manage_shipment.manage_shipment.integrations.base import CourierAdapter
from manage_shipment.manage_shipment.integrations.generic import GenericHTTPAdapter
from manage_shipment.manage_shipment.integrations.nimbuspost import NimbusPostAdapter


def test_status_normalization():
    assert CourierAdapter.normalize_status("Delivered") == "Delivered"
    assert CourierAdapter.normalize_status("Out for delivery") == "Out for Delivery"
    assert CourierAdapter.normalize_status("NDR - customer unavailable") == "NDR / Delivery Exception"
    assert CourierAdapter.normalize_status("RTO in transit") == "RTO In Transit"


def test_build_auth_headers_bearer_default():
    headers = GenericHTTPAdapter.build_auth_headers(None, None, "tok123")
    assert headers == {"Authorization": "Bearer tok123"}


def test_build_auth_headers_custom_header():
    headers = GenericHTTPAdapter.build_auth_headers("Custom Header", "X-Client-Key", "tok123")
    assert headers == {"X-Client-Key": "tok123"}


def test_build_auth_headers_both():
    headers = GenericHTTPAdapter.build_auth_headers("Both", "X-API-Key", "tok123")
    assert headers == {"Authorization": "Bearer tok123", "X-API-Key": "tok123"}


def test_build_auth_headers_no_token():
    assert GenericHTTPAdapter.build_auth_headers("Bearer Token", None, None) == {}


def test_nimbuspost_find_record_data_list():
    payload = {"data": [{"awb": "AWB1", "status": "In Transit"}, {"awb": "AWB2", "status": "Delivered"}]}
    assert NimbusPostAdapter._find_record(payload, "AWB2")["status"] == "Delivered"


def test_nimbuspost_find_record_keyed_by_awb():
    payload = {"data": {"AWB1": {"status": "In Transit"}, "AWB2": {"status": "Delivered"}}}
    assert NimbusPostAdapter._find_record(payload, "AWB2")["status"] == "Delivered"


def test_nimbuspost_find_record_bare_list():
    payload = [{"awb": "AWB1", "status": "Out for Delivery"}]
    assert NimbusPostAdapter._find_record(payload, "AWB1")["status"] == "Out for Delivery"
