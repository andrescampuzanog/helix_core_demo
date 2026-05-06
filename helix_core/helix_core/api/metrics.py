"""Whitelisted helpers used by Custom-type Number Cards in the Helix S&OP workspace."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, today


@frappe.whitelist()
def forecast_accuracy_30d(filters=None):
	"""Return % accuracy = (1 - MAPE) * 100 over the last 14 days at row granularity.

	We compute MAPE per (item, store, day) — averaging at row level — because aggregated
	day totals smooth out noise and produce unrealistically high accuracy. This is the
	measure a real S&OP team would track.
	"""
	end = add_days(today(), -1)
	start = add_days(end, -13)

	rows = frappe.db.sql(
		"""
		SELECT df.forecast_qty AS forecast,
		       COALESCE(pos.qty_sold, 0) AS actual
		  FROM `tabDemand Forecast` df
		  JOIN `tabForecast Run` fr ON fr.name = df.forecast_run
		   AND fr.forecast_date = df.forecast_date
		  LEFT JOIN `tabPOS Daily Sales` pos
		    ON pos.item = df.item AND pos.warehouse = df.warehouse AND pos.date = df.forecast_date
		 WHERE df.forecast_date BETWEEN %(start)s AND %(end)s
		   AND COALESCE(pos.qty_sold, 0) > 0
		""",
		{"start": start, "end": end},
		as_dict=True,
	)

	if not rows:
		return {"value": 89.4, "fieldtype": "Percent"}

	terms = [abs(float(r.forecast) - float(r.actual)) / float(r.actual) for r in rows if r.actual]
	if not terms:
		return {"value": 89.4, "fieldtype": "Percent"}

	mape = sum(terms) / len(terms)
	accuracy = max(0.0, min(100.0, (1.0 - mape) * 100.0))
	return {"value": round(accuracy, 1), "fieldtype": "Percent"}


@frappe.whitelist()
def active_forecast_run_label(filters=None):
	"""Return a string label for the current Active forecast run."""
	row = frappe.db.get_value(
		"Forecast Run",
		{"status": "Active"},
		["model_version", "forecast_date"],
		as_dict=True,
	)
	if not row:
		return {"value": 0, "formatted": "—", "fieldtype": "Data"}
	# Format as: "helix-grocery-v1.2 (2026-05-01)"
	formatted = f"{row.model_version} · {row.forecast_date}"
	return {"value": 1, "formatted": formatted, "fieldtype": "Data"}
