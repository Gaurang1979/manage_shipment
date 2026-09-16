from manage_shipment.manage_shipment.integrations.base import CourierAdapter


def test_status_normalization():
    assert CourierAdapter.normalize_status("Delivered") == "Delivered"
    assert CourierAdapter.normalize_status("Out for delivery") == "Out for Delivery"
    assert CourierAdapter.normalize_status("NDR - customer unavailable") == "NDR / Delivery Exception"
    assert CourierAdapter.normalize_status("RTO in transit") == "RTO In Transit"
