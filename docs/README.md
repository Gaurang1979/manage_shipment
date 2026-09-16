# Manage Shipment Documentation

## User documents
- [Module Process](MODULE_PROCESS.md) — complete shipment lifecycle and operational process.
- [User Help](USER_HELP.md) — day-to-day instructions for users.
- [Settings Guide](SETTINGS.md) — courier/API/tracking configuration.

## Training flowcharts
- [Shipment User Training Flow](USER_TRAINING_FLOWCHART.svg)
- [Courier Setup Flow](COURIER_SETUP_FLOWCHART.svg)

## Suggested training sequence
1. Read User Help.
2. Walk through the Shipment User Training Flow.
3. Create a test Courier Service Provider.
4. Follow the Courier Setup Flow.
5. Create a test Shipment.
6. Refresh tracking and inspect the Event timeline.
7. Practice an exception/follow-up workflow.
8. Review the Dashboard filters and KPI cards.

## Administrator note
API credentials must never be committed to GitHub. Use secure ERPNext configuration and appropriate permissions. Test each courier integration with a controlled shipment before enabling scheduled production tracking.
