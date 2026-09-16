# Manage Shipment — Module Process

## 1. Purpose
Manage Shipment provides one place to create, monitor and follow up domestic shipments handled by Indian courier service providers.

## 2. Basic process
```text
ERPNext Delivery Note / Manual Shipment
        |
        v
Select Courier Service Provider
        |
        v
Enter Tracking / AWB Number
        |
        v
Save / Submit Shipment
        |
        v
Tracking enabled
        |
        +--------------------+
        |                    |
        v                    v
Manual Refresh       Scheduled Tracking
        |                    |
        +---------+----------+
                  v
          Courier Response
                  |
                  v
       Normalize Courier Status
                  |
                  v
       Shipment Event Timeline
                  |
        +---------+---------+
        |                   |
        v                   v
 Normal delivery       Exception / NDR
        |                   |
        v                   v
   Delivered          Follow-up Required
        |                   |
        v                   v
 Tracking stops       Resolve / Escalate
```

## 3. Shipment lifecycle
1. Create Shipment.
2. Select Courier Service Provider.
3. Enter AWB/Tracking ID.
4. Enter customer/consignee and expected delivery details.
5. Save/submit.
6. Use **Refresh Tracking** for an immediate update.
7. Scheduler automatically checks active shipments when an integration is configured.
8. Every meaningful tracking update is recorded in the Shipment Event timeline.
9. Exceptions such as NDR, address issue, customer unavailable, delayed or lost can create a follow-up.
10. Delivered, RTO Delivered and Cancelled shipments stop automatic tracking.

## 4. Dashboard process
Users open **Manage Shipment > Dashboard**, select filters and review KPI cards, status distribution, courier-wise activity, follow-ups and shipment rows. Selecting a shipment opens its complete timeline and follow-up information.

## 5. Delivery Note process
When Delivery Note contains Courier Service Provider and Tracking/AWB Number, the application can create or link a Shipment. The Shipment reference is written back to the Delivery Note.

## 6. Exception process
```text
Exception detected
      |
      v
Follow-up Required = Yes
      |
      v
Set Follow-up Date / Person / Remarks
      |
      v
Contact courier/customer
      |
      +----> Escalated
      |
      +----> Resolved
```

## 7. Bulk tracking
From the shipment list/dashboard, select shipments and run bulk refresh. Bulk operations are limited to protect the server and courier APIs.
