# Changelog

## 0.3.0

### Fixed
- **Critical**: `get_adapter()` referenced `provider.integration_enabled`, a field that did not exist anywhere in the app. This crashed every tracking attempt for a provider not using the Shiprocket aggregator path (i.e. any Direct Courier API / Custom HTTP provider) — the failure was swallowed by the caller's try/except and only visible in the Error Log.
- **Generic HTTP Adapter was sending the masked placeholder password** (`"********"`) instead of the real decrypted API key/token, because it read the Password field directly instead of calling `get_password()`. Direct/custom courier authentication would fail 100% of the time even after the bug above was fixed.
- Auth headers: the adapter always sent both `Authorization: Bearer <token>` and `X-API-Key: <token>` regardless of what the target API expected. Now configurable per provider (Auth Header Style: Bearer Token / Custom Header / Both).
- Dashboard KPI counts silently undercounted once a filtered result set passed 500 shipments (counts were derived from the same capped row list used for the table). Counts are now queried independently of the row page.
- Scheduled tracking (`track_shipments`) capped at 200 shipments per run with no ordering — once a site had more than 200 active shipments, the same first 200 kept getting re-tracked and the rest were starved indefinitely. Now ordered oldest-tracked-first.
- Delivery Note → Shipment auto-linking matched on AWB number alone, which could misattach a shipment if two couriers reused the same AWB, or if an AWB was corrected on a new Delivery Note. Now matches on courier + AWB together.
- `_ensure_default_providers()` (run on every `after_install`/`after_migrate`) unconditionally overwrote `tracking_source`, `tracking_integration`, `adapter_path` and `tracking_enabled` on *existing* provider records, meaning any manual integration configuration was silently reverted back to Shiprocket defaults on the next `bench migrate`. It now only ever inserts missing providers and never touches an existing one.
- `refresh_shipment` / `bulk_refresh_shipments` saved with `ignore_permissions=True`, bypassing the permission framework entirely for any logged-in user who could reach the whitelisted method. Now respects normal write permissions (the new Shipment User role covers the intended use case).
- Dashboard's 7th table column was headed "Action" but rendered follow-up/overdue pills, with no actual per-row action. Now a real Actions column (Refresh, View) with the follow-up pills correctly labelled.
- `app_version` in `hooks.py` (0.1.0) didn't match `__version__.py` (0.2.0).

### Added
- Master list expanded from 14 to ~38 Indian courier/logistics providers, covering national express, e-commerce/D2C, regional, freight and last-mile carriers. Seeded **disabled** — nothing auto-activates.
- New `Shipment User` role: create/read/write on Shipment, read-only on Courier Service Provider. Tracking API Integration (credentials) stays System Manager-only.
- Per-courier **Ageing Threshold (Hours)** field (was a hardcoded 24h for every courier).
- **Escalation Email(s)** per courier — emailed when a shipment on that courier newly needs follow-up or goes No Movement.
- Server-side pagination on the dashboard ("Load more") backing the accurate KPI counts above.
- Clean rename path for the 4 providers whose canonical names changed (Gati → AllCargo Gati, Shree Maruti → Shree Maruti Courier, Anjani → Anjani Courier, Ekart → Ekart Logistics) so existing installs don't end up with duplicate rows.
- Regression tests for the auth-header-style logic.

### Upgrade notes
- Run `bench migrate` to pick up the new fields, the new Shipment User role, and the expanded provider list.
- Any Courier Service Provider using `tracking_source = Direct Courier API` or `Custom HTTP` will start working for the first time after this upgrade — re-test its **Refresh Tracking** action, since it was silently broken before.
- If you were relying on the previous (buggy) behaviour of `_ensure_default_providers` resetting providers back to Shiprocket defaults on every migrate, that no longer happens — your direct-integration configuration will now persist as expected.
