# Manage Shipment

ERPNext v16 application for managing domestic shipments, courier providers, tracking events, delivery exceptions, follow-ups, and shipment dashboards.

## Module

**Manage Shipment**

## First development milestone

The repository now contains the first installable application structure with:

- **Courier Service Provider** master with configurable integration credentials, adapter path, and tracking URL template.
- **Shipment** transaction with AWB/tracking number, courier, status, consignee, ERPNext reference, follow-up controls, and tracking timeline.
- **Shipment Event** child table for normalized courier events, locations, remarks, and event codes.
- Rich **Shipment Dashboard** with courier/status/follow-up filters, KPI cards, and shipment table.
- Shipment form actions for **Refresh Tracking** and **Open Tracking**.
- Provider-independent adapter architecture so each courier can be integrated without changing the Shipment DocType.
- Scheduled background tracking queue for active shipments.
- Seeded Indian domestic courier provider master records: Trackon, Shree Maruti, DTDC, Anjani, Professional Couriers, Delhivery, Blue Dart, India Post / Speed Post, XpressBees, Ecom Express, Gati, Safexpress, Ekart, and Shadowfax.

Provider records are created with integration disabled. API credentials, official tracking URL templates, and adapter configuration must be supplied before live provider calls are enabled.

## Installation

From the Frappe bench directory:

```bash
bench get-app https://github.com/Gaurang1979/manage_shipment.git
bench --site erp.sundaramtech.com install-app manage_shipment
bench --site erp.sundaramtech.com migrate
bench build --app manage_shipment
bench --site erp.sundaramtech.com clear-cache
```

Then open **Manage Shipment → Shipment Dashboard** from the Apps page or use `/app/shipment-dashboard`.

## Architecture

```text
Manage Shipment
├── Courier Service Provider
├── Shipment
│   └── Shipment Event
├── Shipment Dashboard
└── Integration Manager
    └── Courier Adapter
        ├── Delhivery
        ├── DTDC
        ├── Trackon
        ├── Shree Maruti
        ├── Professional Couriers
        └── Anjani
```

Provider integrations are intentionally not hard-coded into the master. The next development milestone will add verified provider adapters using each courier's currently supported API/authentication method.

## Compatibility

- Frappe Framework 16
- ERPNext 16

## Status

**Milestone 1: Core application and dashboard implemented.**
