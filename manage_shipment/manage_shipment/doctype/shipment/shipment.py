import frappe
from frappe.model.document import Document


class Shipment(Document):
    def validate(self):
        if self.status == "Delivered" and not self.actual_delivery_date:
            self.actual_delivery_date = frappe.utils.getdate()

        if self.status in ("Delivered", "RTO Delivered", "Cancelled"):
            self.tracking_enabled = 0

        if self.follow_up_required and not self.follow_up_date:
            frappe.throw("Follow-up Date is required when Follow-up Required is enabled.")

    def on_update(self):
        self._update_follow_up_flags()

    def _update_follow_up_flags(self):
        if self.follow_up_required and self.follow_up_date:
            self.db_set("follow_up_overdue", frappe.utils.getdate(self.follow_up_date) < frappe.utils.getdate(), update_modified=False)
