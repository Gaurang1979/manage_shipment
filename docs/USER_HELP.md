# Manage Shipment — User Help

## Dashboard
The dashboard gives a quick operational view of shipments. Use the filters at the top to narrow the view by courier, status, company, follow-up and date range.

### KPI meanings
- **Total Shipments:** Shipments matching the selected filters.
- **In Transit:** Shipment is moving through the courier network.
- **Out for Delivery:** Courier has assigned the shipment for delivery.
- **Delivered:** Shipment has reached the consignee.
- **NDR / Exception:** Delivery or movement requires attention.
- **Delayed:** Shipment is taking longer than the expected movement/delivery window.
- **RTO:** Return-to-origin processing or completion.
- **Follow-up Required:** User action is required.
- **Follow-up Overdue:** Follow-up date has passed without resolution.

## Creating a Shipment
1. Open **Manage Shipment > Shipment**.
2. Click **Add Shipment**.
3. Select the Courier Service Provider.
4. Enter the Tracking / AWB Number.
5. Enter shipment and consignee information.
6. Link the relevant ERPNext document if applicable.
7. Save/submit.

## Refreshing tracking
Open a Shipment and click **Refresh Tracking**. If a provider integration is configured, the application requests the current tracking information and records the result.

## Tracking timeline
The Events section records the event date/time, normalized status, courier status, location, remarks and event code when supplied by the provider.

## Follow-up
For an exception, set:
- Follow-up Required
- Follow-up Date
- Follow-up Person
- Follow-up Status
- Follow-up Remarks

Use **Pending**, **Called Courier**, **Called Customer**, **Escalated** or **Resolved** as appropriate.

## Open courier tracking
If the provider has a Tracking URL Template, the Shipment can open the courier's public tracking page using the AWB number.

## Common problems
### No tracking result
Check that the courier is active, tracking is enabled, API URL/credentials are correct, and the AWB is valid.

### Status is not changing
Check the Shipment Event timeline and the provider's original courier status. Some courier systems update less frequently than others.

### Follow-up is appearing unexpectedly
Exception statuses can automatically flag a Shipment for follow-up. Review the current courier status and remarks before resolving the follow-up.

## User training rule
Always verify the AWB number before saving. Do not manually change a courier status just to make a shipment appear delivered; use the courier response or document the reason in Follow-up Remarks.
