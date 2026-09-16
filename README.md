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

## Documentation and user training

All operational documentation is maintained in the [`docs`](docs/) folder:

- [Documentation Index](docs/README.md)
- [Module Process](docs/MODULE_PROCESS.md)
- [Settings Guide](docs/SETTINGS.md)
- [User Help](docs/USER_HELP.md)
- [Shipment User Training Flowchart](docs/USER_TRAINING_FLOWCHART.svg)
- [Courier Setup Flowchart](docs/COURIER_SETUP_FLOWCHART.svg)

The SVG flowcharts can be opened directly in a browser and used during user training or included in internal training material.

## Courier API integrations

The application deliberately does **not** pretend that every courier has the same API. Each provider can be configured independently with its endpoint, method, parameter name, credentials and headers. Provider-specific adapters can be added without changing Shipment or the dashboard.

Delhivery provides a client developer portal with shipment tracking APIs and API-token authentication. Configure the current production endpoint and token supplied for the customer's Delhivery account before enabling the integration.

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
4. Set **Adapter Python Path** to `manage_shipment.manage_shipment.integrations.generic.GenericHTTPAdapter`.
5. Configure API URL, HTTP method, tracking parameter, API token/key and any required JSON headers.
6. Test one AWB from Shipment using **Refresh Tracking**.

## Delivery Note integration

After installing the app and running migration, Delivery Note gets shipment fields for Courier Service Provider and Tracking / AWB Number. When a submitted Delivery Note has both values, Manage Shipment automatically creates or links a Shipment record.

## Safety / credentials

API credentials are stored in Password fields. Do not commit provider tokens, API keys or customer credentials to GitHub.

## Compatibility

- Frappe Framework 16
- ERPNext 16
- Python 3.10+

## Development status

Core application, dashboard, scheduling, generic integration framework, Delivery Note linkage and user documentation are implemented. Courier-specific production adapters should only be enabled after verifying the provider's current API contract and account credentials.
