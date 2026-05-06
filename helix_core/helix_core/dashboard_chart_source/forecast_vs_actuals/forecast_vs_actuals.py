"""Data source for the 'Forecast vs Actuals' Dashboard Chart on the Helix S&OP workspace.

For each of the last 14 days, we plot:
  • forecast — the forecast for date D issued at the morning run dated D
  • actual   — POS Daily Sales sum for date D

If a category (Item Group) filter is provided, both lines are scoped to that group.
"""

from __future__ import annotations

import frappe
from frappe.utils import add_days, today


@frappe.whitelist()
def get(chart_name=None, chart=None, no_cache=None, filters=None, from_date=None, to_date=None, timespan=None, time_interval=None, heatmap_year=None, **kwargs):
	if isinstance(filters, str):
		import json

		try:
			filters = json.loads(filters)
		except Exception:
			filters = None

	item_group = None
	if filters:
		if isinstance(filters, dict):
			item_group = filters.get("item_group")
		elif isinstance(filters, list):
			for f in filters:
				if isinstance(f, list) and len(f) >= 4 and f[1] == "item_group":
					item_group = f[3]
					break

	end = add_days(today(), -1)
	start = add_days(end, -13)

	params = {"start": start, "end": end}
	group_filter = ""
	if item_group:
		group_filter = "AND it.item_group = %(item_group)s"
		params["item_group"] = item_group

	rows = frappe.db.sql(
		f"""
		SELECT df.forecast_date AS d,
		       SUM(df.forecast_qty) AS forecast,
		       SUM(COALESCE(pos.qty_sold, 0)) AS actual
		  FROM `tabDemand Forecast` df
		  JOIN `tabForecast Run` fr ON fr.name = df.forecast_run
		   AND fr.forecast_date = df.forecast_date
		  JOIN `tabItem` it ON it.name = df.item
		  LEFT JOIN `tabPOS Daily Sales` pos
		    ON pos.item = df.item AND pos.warehouse = df.warehouse AND pos.date = df.forecast_date
		 WHERE df.forecast_date BETWEEN %(start)s AND %(end)s
		   {group_filter}
		 GROUP BY df.forecast_date
		 ORDER BY df.forecast_date
		""",
		params,
		as_dict=True,
	)

	labels = [str(r.d) for r in rows]
	forecast_values = [round(float(r.forecast or 0), 2) for r in rows]
	actual_values = [round(float(r.actual or 0), 2) for r in rows]

	return {
		"labels": labels,
		"datasets": [
			{"name": "Forecast", "values": forecast_values, "chartType": "line"},
			{"name": "Actual", "values": actual_values, "chartType": "line"},
		],
	}
