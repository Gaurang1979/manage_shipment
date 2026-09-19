# Manage Shipment

ERPNext v16 application for managing domestic shipments, courier providers, tracking events, delivery exceptions, ageing and follow-ups.

## Module

**Manage Shipment**

## Included in 0.3.0

- Fixed a critical bug where every Direct Courier API / Custom HTTP provider crashed on tracking (`get_adapter` referenced a field that did not exist) — only the Shiprocket-aggregator path worked before this release.
- Fixed the Generic HTTP Adapter sending the masked placeholder password instead of the real decrypted API key/token — direct courier auth would fail even once the bug above was fixed.
- Configurable **Auth Header Style** (Bearer Token / Custom Header / Both) per provider, instead of always sending both.
- Comprehensive Indian courier master list (~38 providers) covering national express, e-commerce/D2C, regional, freight and last-mile carriers — seeded **disabled**, so nothing auto-activates; enable only what you use.
- New **Shipment User** role with working (non-System-Manager) access to Shipment and Courier Service Provider (read-only); Tracking API Integration stays System Manager-only since it holds credentials.
- Per-courier **Ageing Threshold (Hours)** (was a hardcoded 24h for every courier) and **Escalation Email(s)** sent when a shipment newly needs follow-up or goes No Movement.
- Dashboard: fixed the "Action" column (it showed follow-up pills, not an action), added real per-row Refresh/View buttons, and added server-side pagination ("Load more") so KPI counts stay accurate past 500 shipments.
- Fixed scheduled tracking starving shipments beyond the first 200 (now oldest-tracked-first).
- Fixed Delivery Note → Shipment matching to key on courier + AWB together, not AWB alone.
- Migration seeding no longer overwrites a provider you've already configured on `bench migrate`.

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

1. Open **Courier Service Provider** and pick the courier from the ~38-provider master list (all seeded disabled).
2. Set **Tracking Source** to `Direct Courier API` or `Custom HTTP` for a direct integration, or `Aggregator` + **Tracking Integration** to route through Shiprocket.
3. Keep **Tracking Enabled** off until the API endpoint and credentials below are configured and tested.
4. For a direct/custom integration, set **Adapter Python Path** to `manage_shipment.manage_shipment.integrations.generic.GenericHTTPAdapter`.
5. Configure API URL, HTTP method, tracking parameter, API token/key, **Auth Header Style** (most APIs want Bearer Token; set Custom Header if the courier expects a differently-named header) and any required JSON headers.
6. Optionally set **Ageing Threshold (Hours)** and **Escalation Email(s)** for this courier.
7. Test one AWB from Shipment using **Refresh Tracking**, then turn **Enabled** on for the provider so it appears in the dashboard filter.

## Delivery Note integration

After installing the app and running migration, Delivery Note gets shipment fields for Courier Service Provider and Tracking / AWB Number. When a submitted Delivery Note has both values, Manage Shipment automatically creates or links a Shipment record.

## Roles

- **System Manager** — full access, including Courier Service Provider credentials and Tracking API Integration.
- **Shipment User** (new in 0.3.0) — create/read/write on Shipment, read-only on Courier Service Provider (Password field values stay masked regardless of role). Assign this to logistics/support staff who need the dashboard without full admin access. Tracking API Integration remains System Manager-only since it holds aggregator credentials.

## Safety / credentials

API credentials are stored in Password fields. Do not commit provider tokens, API keys or customer credentials to GitHub.

## Compatibility

- Frappe Framework 16
- ERPNext 16
- Python 3.10+

## Development status

Core application, dashboard, scheduling, generic integration framework, Delivery Note linkage and user documentation are implemented. Courier-specific production adapters should only be enabled after verifying the provider's current API contract and account credentials.
