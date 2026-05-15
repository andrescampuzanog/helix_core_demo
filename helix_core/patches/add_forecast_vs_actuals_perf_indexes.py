"""Add indexes matching Forecast vs Actuals dashboard query filters."""

from __future__ import annotations

import frappe


def execute():
	frappe.db.add_index(
		"Demand Forecast",
		["forecast_date", "forecast_run", "item"],
		"helix_df_date_run_item",
	)
	frappe.db.add_index(
		"Forecast Run",
		["status"],
		"helix_fr_status",
	)
