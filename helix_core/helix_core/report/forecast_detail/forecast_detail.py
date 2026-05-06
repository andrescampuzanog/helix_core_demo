"""Forecast Detail — joins Demand Forecast (active run) with yesterday's POS actuals.

Filterable by Item Group and Warehouse. Returns columns for Forecast Qty, p10, p90,
Yesterday's Actual, and Variance %.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, today


def execute(filters=None):
	filters = filters or {}
	columns = _get_columns()
	data = _get_data(filters)
	return columns, data


def _get_columns():
	return [
		{"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 220},
		{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 140},
		{"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 200},
		{"label": _("Forecast Date"), "fieldname": "forecast_date", "fieldtype": "Date", "width": 110},
		{"label": _("Forecast Qty"), "fieldname": "forecast_qty", "fieldtype": "Float", "width": 110},
		{"label": _("p10"), "fieldname": "p10", "fieldtype": "Float", "width": 90},
		{"label": _("p90"), "fieldname": "p90", "fieldtype": "Float", "width": 90},
		{"label": _("Yesterday's Actual"), "fieldname": "yesterday_actual", "fieldtype": "Float", "width": 130},
		{"label": _("Variance %"), "fieldname": "variance_pct", "fieldtype": "Percent", "width": 100},
	]


def _get_data(filters):
	yesterday = add_days(today(), -1)
	conditions = ["fr.status = 'Active'"]
	params = {"yesterday": yesterday}

	if filters.get("item_group"):
		conditions.append("it.item_group = %(item_group)s")
		params["item_group"] = filters["item_group"]
	if filters.get("warehouse"):
		conditions.append("df.warehouse = %(warehouse)s")
		params["warehouse"] = filters["warehouse"]

	where_sql = " AND ".join(conditions)

	rows = frappe.db.sql(
		f"""
		SELECT df.item AS item,
		       it.item_group AS item_group,
		       df.warehouse AS warehouse,
		       df.forecast_date AS forecast_date,
		       df.forecast_qty AS forecast_qty,
		       df.p10 AS p10,
		       df.p90 AS p90,
		       (
		          SELECT pos.qty_sold FROM `tabPOS Daily Sales` pos
		           WHERE pos.item = df.item AND pos.warehouse = df.warehouse
		             AND pos.date = %(yesterday)s
		           LIMIT 1
		       ) AS yesterday_actual
		  FROM `tabDemand Forecast` df
		  JOIN `tabForecast Run` fr ON fr.name = df.forecast_run
		  JOIN `tabItem` it ON it.name = df.item
		 WHERE {where_sql}
		 ORDER BY df.forecast_date, df.item, df.warehouse
		""",
		params,
		as_dict=True,
	)

	for r in rows:
		actual = r.get("yesterday_actual") or 0
		forecast = r.get("forecast_qty") or 0
		if actual:
			r["variance_pct"] = round(((forecast - actual) / actual) * 100.0, 1)
		else:
			r["variance_pct"] = None
	return rows
