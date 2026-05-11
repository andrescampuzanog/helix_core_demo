"""Add indexes used by the Helix SOP dashboard chart."""

from __future__ import annotations

import frappe


def execute():
	frappe.db.add_index(
		"Demand Forecast",
		["forecast_run", "forecast_date"],
		"helix_df_run_date",
	)
	frappe.db.add_index(
		"Forecast Run",
		["forecast_date"],
		"helix_fr_forecast_date",
	)
	frappe.db.add_index(
		"POS Daily Sales",
		["date", "item"],
		"helix_pos_date_item",
	)
