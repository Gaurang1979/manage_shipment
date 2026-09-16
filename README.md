# Manage Shipment

ERPNext v16 application for managing domestic shipments, courier providers, tracking events, delivery exceptions, ageing and follow-ups.

## Module

**Manage Shipment**

## Included in 0.2.0

- Courier Service Provider master
- Shipment / AWB transaction
- Standardized status model across courier providers
- Detailed tracking event timeline
- Courier status and current location
- Expected and actual delivery dates
- Follow-up workflow with overdue detection
- No-movement / ageing detection
- Scheduled tracking every 10 minutes for enabled integrations
- Bulk refresh of up to 100 shipments
- Shipment dashboard with courier, status, company, date and follow-up filters
- KPI cards, status distribution and follow-up summary
- Delivery Note integration: courier + AWB fields can automatically create a Shipment on submission
- Configurable generic HTTP GET/POST adapter
- API token/key and custom-header support
- Configurable tracking URL template
- Initial provider master for Trackon, Shree Maruti, DTDC, Anjani, Professional Couriers, Delhivery, Blue Dart, India Post / Speed Post, XpressBees, Ecom Express, Gati, Safexpress, Ekart and Shadowfax

## Courier API integrations

The application deliberately does **not** pretend that every courier has the same API. Each provider can be configured independently with its endpoint, method, parameter name, credentials and headers. Provider-specific adapters can be added without changing Shipment or the dashboard.

Delhivery currently provides a client developer portal with shipment tracking APIs and API-token authentication; its current documentation should be used when configuring the production endpoint and token for a customer account. citeturn1search0turn1search1

## Installation

```bash
cd ~/frappe-bench
bench get-app https://github.com/Gaurang1979/manage_shipment.git
bench --site erp.sundaramtech.com install-app manage_shipment
bench --site erp.sundaramtech.com migrate
bench build --app manage_shipment
bench restart
```

After installation, open **Manage Shipment** from the Apps screen or `/app/shipment-dashboard`.

## Provider configuration

1. Open **Courier Service Provider**.
2. Select a provider.
3. Keep **Integration Enabled** disabled until its API endpoint and credentials are configured.
4. Set **Adapter Python Path** to:
   `manage_shipment.manage_shipment.integrations.generic.GenericHTTPAdapter`
5. Configure API URL, HTTP method, tracking parameter, API token/key and any required JSON headers.
6. Test one AWB from Shipment using **Refresh Tracking**.

Frappe provides standard REST APIs for DocTypes and supports scheduled jobs through `scheduler_events`; the app uses those framework facilities rather than modifying ERPNext core. citeturn0search0turn0search1

## Safety / credentials

API credentials are stored in Password fields. Do not commit provider tokens, API keys or customer credentials to GitHub.

## Compatibility

- Frappe Framework 16
- ERPNext 16
- Python 3.10+

## Development status

Core application, dashboard, scheduling, generic integration framework and Delivery Note linkage are implemented. Courier-specific production adapters should only be enabled after verifying the provider's current API contract and account credentials.
