import frappe
from frappe.model.document import Document


class ForecastRun(Document):
	def before_insert(self):
		if not self.created_by:
			self.created_by = frappe.session.user

	def on_update(self):
		# Only one Active run at a time.
		if self.status == "Active":
			frappe.db.sql(
				"UPDATE `tabForecast Run` SET status='Archived' WHERE name != %s AND status='Active'",
				(self.name,),
			)
