# Manage Shipment — Settings Guide

## Courier Service Provider
Open **Courier Service Provider** and maintain one record per courier.

### General
- Provider Name
- Provider Code
- Enabled (master list ships with every provider disabled - turn on only what you use)
- Tracking Enabled
- Tracking Source (Aggregator / Direct Courier API / Custom HTTP)
- Tracking URL Template

Use `{tracking_id}` in the tracking URL template where the AWB number must be inserted.

### API configuration
Only enter credentials supplied by the courier or an approved integration provider.

- API URL
- API Method
- Tracking Parameter
- API Key
- API Token
- Auth Header Style (Bearer Token / Custom Header / Both) and Custom Header Name — controls how the API Key/Token above is sent; check the courier's API docs for which one they expect
- Account ID
- Custom Headers JSON

Do not put credentials into source code or GitHub. Store them in ERPNext configuration fields and restrict access through roles/permissions.

### Ageing & escalation
- Ageing Threshold (Hours) — hours without a status change before this courier's shipments are flagged No Movement / Follow-up (default 24)
- Escalation Email(s) — comma-separated addresses emailed when a shipment on this courier newly needs follow-up or goes No Movement

## Tracking behaviour
Active shipments are eligible for scheduled tracking. Final statuses such as Delivered, RTO Delivered and Cancelled stop automatic tracking.

## Roles
- **System Manager**: full access, including all credential fields.
- **Shipment User**: create/read/write on Shipment, read-only on Courier Service Provider. Assign to staff who work the dashboard day to day.

## Status mapping
Courier-specific responses are normalized to the common Manage Shipment statuses. Keep the original courier status in the Shipment record so users can see the provider's wording.

## Recommended setup sequence
1. Create the Courier Service Provider.
2. Enable the provider only after its endpoint and credentials have been tested.
3. Configure the tracking URL template if public web tracking is available.
4. Create one test Shipment.
5. Click **Refresh Tracking**.
6. Confirm the Shipment status and Event timeline.
7. Only then enable scheduled tracking for production shipments.

## Security
Never commit API keys, tokens, passwords or account secrets to this repository. If a provider requires special authentication, implement it through a secure server-side integration and keep secrets outside source control.

## Delivery Note settings
The application adds shipment fields to Delivery Note:
- Courier Service Provider
- Tracking / AWB Number
- Shipment reference

The exact placement can be adjusted through ERPNext Custom Field configuration if the customer's Delivery Note layout differs.
