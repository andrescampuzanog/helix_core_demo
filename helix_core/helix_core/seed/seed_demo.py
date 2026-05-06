"""Seed/reset script for the Helix demo.

Runs as: bench --site demo.helix.localhost execute helix_core.helix_core.seed.seed_demo.run

Idempotent on masters (skip-if-exists), wipes + rebuilds transactional data every run.
Deterministic via a fixed RNG seed so successive runs produce identical demos.
"""

from __future__ import annotations

import random
import time
from datetime import date, timedelta

import frappe
from frappe.utils import add_days, getdate, now, today

from helix_core.helix_core.seed.data.items import (
	CATEGORIES,
	COMPANY_ABBR,
	COMPANY_NAME,
	ITEMS_BY_CATEGORY,
	OVERSTOCK_ITEMS,
	PARENT_WAREHOUSE,
	PROMO_ITEMS,
	STOCKOUT_RISK_ITEMS,
	SUPPLIERS,
	WAREHOUSE_FACTORS,
	WAREHOUSES,
)

# ---------------------------------------------------------------------------
# Constants / config
# ---------------------------------------------------------------------------

RNG_SEED = 20260501
HISTORICAL_DAYS = 90
FORECAST_HORIZON = 14
HISTORICAL_RUNS = 14  # plus 1 active = 15 total
MODEL_VERSION = "helix-grocery-v1.2"
ADMIN_USER = "admin@helix.mx"
DEMO_USER = "demo@helix.mx"
DEMO_PASSWORD = "Helix2026!"

# Promo windows expressed as (days_back_start, days_back_end) inclusive — dates earlier in time first.
# At least one window must fall within the chart's last-14-day range so the
# "the model saw the spike" moment lands in the demo's centerpiece chart.
PROMO_WINDOWS = [(60, 54), (10, 6)]
PROMO_MULTIPLIER = 2.5

ACTUAL_NOISE_SIGMA = 0.15
FORECAST_NOISE_SIGMA = 0.08


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run():
	"""Top-level: wipe + rebuild + commit."""
	t0 = time.time()
	rng = random.Random(RNG_SEED)
	print("[helix-seed] starting…")

	wipe()
	frappe.db.commit()
	print(f"[helix-seed] wipe done ({time.time() - t0:.1f}s)")

	ensure_masters()
	frappe.db.commit()
	print(f"[helix-seed] masters done ({time.time() - t0:.1f}s)")

	# Pre-compute the deterministic baseline lattice once so POS + forecasts share it.
	baseline = _build_baseline_lattice()

	seed_pos_daily_sales(baseline, rng)
	frappe.db.commit()
	print(f"[helix-seed] POS rows done ({time.time() - t0:.1f}s)")

	seed_forecast_runs_and_forecasts(baseline, rng)
	frappe.db.commit()
	print(f"[helix-seed] forecasts done ({time.time() - t0:.1f}s)")

	seed_initial_stock(baseline)
	frappe.db.commit()
	print(f"[helix-seed] stock done ({time.time() - t0:.1f}s)")

	seed_material_requests(baseline)
	frappe.db.commit()
	print(f"[helix-seed] MRs done ({time.time() - t0:.1f}s)")

	ensure_demo_users_and_landing_page()
	frappe.db.commit()

	_ensure_setup_complete()
	frappe.db.commit()

	_print_summary(t0)


def _ensure_setup_complete():
	"""Ensure ERPNext doesn't bounce users to the setup wizard.

	Frappe v15's `is_setup_complete()` checks `tabInstalled Application.is_setup_complete = 1`
	for both `frappe` and `erpnext` (NOT `System Settings.setup_complete` — that's the v14 path).
	We force all rows to 1 on every seed so resets stay clean.
	"""
	frappe.db.sql("UPDATE `tabInstalled Application` SET is_setup_complete = 1")
	# Belt-and-braces: also write the v14 flag for any code path still reading it.
	frappe.db.set_single_value("System Settings", "setup_complete", 1)
	frappe.db.set_default("setup_complete", "1")
	# Without this, desk.js:356 sees boot.home_page == "setup-wizard" and skips
	# mounting the top navbar entirely (no logo, no search, no user menu).
	frappe.db.set_default("desktop:home_page", "workspace")
	try:
		frappe.db.set_single_value("Global Defaults", "default_company", COMPANY_NAME)
	except Exception:
		pass


# ---------------------------------------------------------------------------
# Phase 1 — wipe transactional data
# ---------------------------------------------------------------------------


def wipe():
	"""Delete custom transactional rows + cancel/delete MRs and Stock Reconciliations."""
	for dt in ("Demand Forecast", "POS Daily Sales", "Forecast Run"):
		try:
			frappe.db.sql(f"DELETE FROM `tab{dt}`")
		except Exception as e:
			print(f"[helix-seed] could not wipe {dt}: {e}")

	# Cancel + delete Helix-generated Material Requests (and any linked PRs).
	mrs = frappe.get_all(
		"Material Request",
		filters={"helix_generated": 1},
		fields=["name", "docstatus"],
	)
	for mr in mrs:
		_cancel_and_delete_mr(mr.name)

	# Cancel + delete any Helix-generated Purchase Receipts that survived
	prs = frappe.get_all("Purchase Receipt", filters={"helix_generated": 1}, fields=["name", "docstatus"])
	for pr in prs:
		_cancel_and_delete(pr.name, "Purchase Receipt")

	# Cancel + delete Stock Reconciliations on the demo company (always recreate fresh).
	if frappe.db.exists("Company", COMPANY_NAME):
		recs = frappe.get_all(
			"Stock Reconciliation",
			filters={"company": COMPANY_NAME},
			fields=["name", "docstatus"],
		)
		for rec in recs:
			_cancel_and_delete(rec.name, "Stock Reconciliation")


def _cancel_and_delete_mr(name: str):
	# Try to cancel any submitted Purchase Receipts pointing to this MR.
	prs = frappe.db.sql(
		"""SELECT DISTINCT parent FROM `tabPurchase Receipt Item` WHERE material_request = %s""",
		(name,),
	)
	for (pr_name,) in prs:
		_cancel_and_delete(pr_name, "Purchase Receipt")
	_cancel_and_delete(name, "Material Request")


def _cancel_and_delete(name: str, doctype: str):
	try:
		doc = frappe.get_doc(doctype, name)
		if doc.docstatus == 1:
			doc.cancel()
		frappe.delete_doc(doctype, name, force=True, ignore_permissions=True, delete_permanently=True)
	except Exception as e:
		print(f"[helix-seed] could not delete {doctype} {name}: {e}")


# ---------------------------------------------------------------------------
# Phase 2 — masters (idempotent)
# ---------------------------------------------------------------------------


def ensure_masters():
	_ensure_currency()
	_ensure_uoms()
	_ensure_warehouse_types()
	_ensure_company()
	_ensure_fiscal_years()
	_ensure_item_groups()
	_ensure_warehouses()
	_ensure_suppliers()
	_ensure_items()


def _ensure_fiscal_years():
	"""Cover all dates the seed will produce: 90 days back, 14 days forward."""
	for year in (2025, 2026, 2027):
		name = str(year)
		if frappe.db.exists("Fiscal Year", name):
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Fiscal Year",
					"year": name,
					"year_start_date": f"{year}-01-01",
					"year_end_date": f"{year}-12-31",
					"companies": [{"company": COMPANY_NAME}],
				}
			).insert(ignore_permissions=True)
		except Exception as e:
			print(f"[helix-seed] could not create Fiscal Year {name}: {e}")


def _ensure_warehouse_types():
	for t in ("Transit", "Stores", "Work In Progress", "Finished Goods"):
		if not frappe.db.exists("Warehouse Type", t):
			try:
				frappe.get_doc({"doctype": "Warehouse Type", "name": t}).insert(ignore_permissions=True)
			except Exception as e:
				print(f"[helix-seed] could not create Warehouse Type {t}: {e}")


def _ensure_currency():
	if not frappe.db.exists("Currency", "MXN"):
		frappe.get_doc(
			{
				"doctype": "Currency",
				"currency_name": "MXN",
				"fraction": "Centavo",
				"smallest_currency_fraction_value": 0.01,
				"symbol": "$",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)


def _ensure_uoms():
	for uom in ("Nos", "Kg", "Litre"):
		if not frappe.db.exists("UOM", uom):
			frappe.get_doc({"doctype": "UOM", "uom_name": uom, "enabled": 1}).insert(ignore_permissions=True)


def _ensure_company():
	if frappe.db.exists("Company", COMPANY_NAME):
		return
	frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": COMPANY_NAME,
			"abbr": COMPANY_ABBR,
			"default_currency": "MXN",
			"country": "Mexico",
			"create_chart_of_accounts_based_on": "Standard Template",
			"chart_of_accounts": "Standard",
		}
	).insert(ignore_permissions=True)
	frappe.db.set_default("company", COMPANY_NAME)
	frappe.db.set_single_value("Global Defaults", "default_company", COMPANY_NAME)


def _ensure_item_groups():
	if not frappe.db.exists("Item Group", "All Item Groups"):
		# ERPNext seeds this; if missing, create.
		frappe.get_doc(
			{"doctype": "Item Group", "item_group_name": "All Item Groups", "is_group": 1}
		).insert(ignore_permissions=True)
	for group_name in CATEGORIES.keys():
		if frappe.db.exists("Item Group", group_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": group_name,
				"parent_item_group": "All Item Groups",
				"is_group": 0,
			}
		).insert(ignore_permissions=True)


def _ensure_warehouses():
	# Parent group warehouse.
	if not frappe.db.exists("Warehouse", PARENT_WAREHOUSE):
		# ERPNext usually seeds this on company create, but guard anyway.
		all_w = frappe.db.exists("Warehouse", "All Warehouses")
		frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": "All Warehouses",
				"company": COMPANY_NAME,
				"is_group": 1,
				"parent_warehouse": all_w if all_w else None,
			}
		).insert(ignore_permissions=True)
	for wh in WAREHOUSES:
		full = f"{wh} - {COMPANY_ABBR}"
		if frappe.db.exists("Warehouse", full):
			continue
		frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": wh,
				"company": COMPANY_NAME,
				"parent_warehouse": PARENT_WAREHOUSE,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)


def _ensure_suppliers():
	if not frappe.db.exists("Supplier Group", "Helix Suppliers"):
		frappe.get_doc(
			{
				"doctype": "Supplier Group",
				"supplier_group_name": "Helix Suppliers",
				"parent_supplier_group": "All Supplier Groups"
				if frappe.db.exists("Supplier Group", "All Supplier Groups")
				else None,
			}
		).insert(ignore_permissions=True)
	for sup in SUPPLIERS:
		if frappe.db.exists("Supplier", sup):
			continue
		frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": sup,
				"supplier_group": "Helix Suppliers",
				"country": "Mexico",
				"supplier_type": "Company",
			}
		).insert(ignore_permissions=True)


def _ensure_items():
	default_warehouse = f"{WAREHOUSES[0]} - {COMPANY_ABBR}"
	for category, abbr in CATEGORIES.items():
		for code_suffix, name, uom, rate, supplier, _baseline in ITEMS_BY_CATEGORY[category]:
			item_code = f"ITM-{abbr}-{code_suffix}"
			at_risk = 1 if item_code in STOCKOUT_RISK_ITEMS else 0
			if frappe.db.exists("Item", item_code):
				# Refresh the at-risk flag every run so the KPI reflects current intent.
				frappe.db.set_value("Item", item_code, "helix_at_risk", at_risk, update_modified=False)
				continue
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": item_code,
					"item_name": name,
					"item_group": category,
					"stock_uom": uom,
					"is_stock_item": 1,
					"include_item_in_manufacturing": 0,
					"standard_rate": rate,
					"valuation_rate": rate * 0.6,
					"description": name,
					"helix_at_risk": at_risk,
					"item_defaults": [
						{
							"company": COMPANY_NAME,
							"default_warehouse": default_warehouse,
							"default_supplier": supplier if frappe.db.exists("Supplier", supplier) else None,
						}
					],
					"supplier_items": [{"supplier": supplier}]
					if frappe.db.exists("Supplier", supplier)
					else [],
				}
			).insert(ignore_permissions=True, ignore_mandatory=True)


# ---------------------------------------------------------------------------
# Baseline lattice — shared between POS and forecast generation
# ---------------------------------------------------------------------------


def _build_baseline_lattice():
	"""Compute deterministic per-(item,store,day) baseline demand for past 90 + future 14 days.

	Returns dict: { (item_code, warehouse_full, date_iso): base_qty }
	"""
	lattice: dict[tuple[str, str, str], float] = {}
	t = today()
	# day offset from -HISTORICAL_DAYS to +FORECAST_HORIZON, anchored at today
	for category, abbr in CATEGORIES.items():
		for code_suffix, _name, _uom, _rate, _supplier, baseline in ITEMS_BY_CATEGORY[category]:
			item_code = f"ITM-{abbr}-{code_suffix}"
			for wh in WAREHOUSES:
				full_wh = f"{wh} - {COMPANY_ABBR}"
				wh_factor = WAREHOUSE_FACTORS[wh]
				for delta in range(-HISTORICAL_DAYS, FORECAST_HORIZON + 1):
					d = add_days(t, delta)
					weekday = getdate(d).weekday()  # 0=Mon
					seasonality = _weekday_seasonality(category, weekday)
					trend = 1.0 + (delta / 365.0) * 0.10  # gentle 10%/yr trend
					promo = _promo_factor(item_code, delta)
					qty = baseline * wh_factor * seasonality * trend * promo
					lattice[(item_code, full_wh, d)] = qty
	return lattice


def _weekday_seasonality(category: str, weekday: int) -> float:
	# 0=Mon ... 5=Sat 6=Sun
	is_weekend = weekday in (5, 6)
	if category in ("Bebidas", "Congelados", "Panadería"):
		return 1.45 if is_weekend else (0.95 if weekday in (1, 2) else 1.0)
	if category == "Frutas y Verduras":
		return 1.20 if is_weekend else 0.95
	if category == "Lácteos":
		return 1.10 if is_weekend else 1.00
	# Abarrotes — flatter
	return 1.05 if is_weekend else 1.0


def _promo_factor(item_code: str, day_offset_from_today: int) -> float:
	if item_code not in PROMO_ITEMS:
		return 1.0
	# day_offset_from_today is negative for historical days (e.g. -60..-54).
	for start, end in PROMO_WINDOWS:
		# Window expressed as (days_back_start, days_back_end), older first.
		# i.e. -start..-end inclusive.
		if -start <= day_offset_from_today <= -end:
			return PROMO_MULTIPLIER
	return 1.0


# ---------------------------------------------------------------------------
# Phase 3 — POS Daily Sales (bulk insert)
# ---------------------------------------------------------------------------


def seed_pos_daily_sales(baseline: dict, rng: random.Random):
	"""Insert ~36k POS Daily Sales rows directly via raw SQL multi-row INSERT."""
	now_str = now()
	t = today()

	# Per-item rate lookup for revenue
	rates = {f"ITM-{CATEGORIES[cat]}-{c[0]}": c[3] for cat in CATEGORIES for c in ITEMS_BY_CATEGORY[cat]}

	rows = []
	for delta in range(-HISTORICAL_DAYS, 0):  # past 90 days, NOT including today
		d = add_days(t, delta)
		for category, abbr in CATEGORIES.items():
			for code_suffix, *_ in ITEMS_BY_CATEGORY[category]:
				item_code = f"ITM-{abbr}-{code_suffix}"
				for wh in WAREHOUSES:
					full_wh = f"{wh} - {COMPANY_ABBR}"
					base = baseline[(item_code, full_wh, d)]
					qty = max(0.0, base * (1.0 + rng.gauss(0, ACTUAL_NOISE_SIGMA)))
					revenue = qty * rates[item_code]
					rows.append(
						(
							frappe.generate_hash(length=16),
							now_str,
							now_str,
							"Administrator",
							"Administrator",
							0,
							0,
							item_code,
							full_wh,
							d,
							round(qty, 2),
							round(revenue, 2),
						)
					)

	_chunked_multi_insert(
		"POS Daily Sales",
		[
			"name",
			"creation",
			"modified",
			"modified_by",
			"owner",
			"docstatus",
			"idx",
			"item",
			"warehouse",
			"date",
			"qty_sold",
			"revenue",
		],
		rows,
		chunk=2000,
	)


# ---------------------------------------------------------------------------
# Phase 4 — Forecast Runs + Demand Forecasts
# ---------------------------------------------------------------------------


def seed_forecast_runs_and_forecasts(baseline: dict, rng: random.Random):
	now_str = now()
	t = today()
	# 14 historical runs (today-14 .. today-1), all Archived. 1 active = today.
	run_records = []
	for delta in range(-HISTORICAL_RUNS, 1):
		run_date = add_days(t, delta)
		status = "Active" if delta == 0 else "Archived"
		run_id = f"RUN-{run_date}-{'A01' if status == 'Active' else f'H{(-delta):02d}'}"
		run_records.append((run_id, run_date, status))

	# Insert Forecast Runs via get_doc (small count, want validation/hooks).
	for run_id, run_date, status in run_records:
		if frappe.db.exists("Forecast Run", run_id):
			continue
		frappe.get_doc(
			{
				"doctype": "Forecast Run",
				"run_id": run_id,
				"forecast_date": run_date,
				"model_version": MODEL_VERSION,
				"horizon_days": FORECAST_HORIZON,
				"status": status,
			}
		).insert(ignore_permissions=True)

	# Bulk insert Demand Forecast rows.
	rows = []
	for run_id, run_date, _status in run_records:
		# Each run forecasts run_date through run_date + (FORECAST_HORIZON-1).
		for offset in range(FORECAST_HORIZON):
			d = add_days(run_date, offset)
			day_offset_from_today = (getdate(d) - getdate(t)).days
			# Skip dates outside the lattice (shouldn't happen given our window).
			if day_offset_from_today < -HISTORICAL_DAYS or day_offset_from_today > FORECAST_HORIZON:
				continue
			for category, abbr in CATEGORIES.items():
				for code_suffix, *_ in ITEMS_BY_CATEGORY[category]:
					item_code = f"ITM-{abbr}-{code_suffix}"
					for wh in WAREHOUSES:
						full_wh = f"{wh} - {COMPANY_ABBR}"
						base = baseline[(item_code, full_wh, d)]
						forecast_qty = max(0.0, base * (1.0 + rng.gauss(0, FORECAST_NOISE_SIGMA)))
						p10 = forecast_qty * 0.85
						p90 = forecast_qty * 1.15
						valid_through = add_days(run_date, FORECAST_HORIZON - 1)
						rows.append(
							(
								frappe.generate_hash(length=16),
								now_str,
								now_str,
								"Administrator",
								"Administrator",
								0,
								0,
								run_id,
								item_code,
								full_wh,
								d,
								round(forecast_qty, 2),
								round(p10, 2),
								round(p90, 2),
								valid_through,
							)
						)

	_chunked_multi_insert(
		"Demand Forecast",
		[
			"name",
			"creation",
			"modified",
			"modified_by",
			"owner",
			"docstatus",
			"idx",
			"forecast_run",
			"item",
			"warehouse",
			"forecast_date",
			"forecast_qty",
			"p10",
			"p90",
			"valid_through_date",
		],
		rows,
		chunk=2000,
	)


# ---------------------------------------------------------------------------
# Phase 5 — Initial stock via Stock Reconciliation
# ---------------------------------------------------------------------------


def seed_initial_stock(baseline: dict):
	"""One Stock Reconciliation per warehouse, opening-stock, posted 91 days ago."""
	t = today()
	posting_date = add_days(t, -HISTORICAL_DAYS - 1)
	rates = {
		f"ITM-{CATEGORIES[cat]}-{c[0]}": c[3] for cat in CATEGORIES for c in ITEMS_BY_CATEGORY[cat]
	}

	# Days of cover policy:
	# - stockout-risk items get 1-2 days cover
	# - overstock items get 30 days cover
	# - everything else: 8 days cover
	def days_of_cover(item_code: str) -> float:
		if item_code in STOCKOUT_RISK_ITEMS:
			return 1.5
		if item_code in OVERSTOCK_ITEMS:
			return 30.0
		return 8.0

	for wh in WAREHOUSES:
		full_wh = f"{wh} - {COMPANY_ABBR}"
		# We compute target qty assuming the *active forecast's first day* is "today's daily rate".
		# For seeding stock 91 days ago, we use the same target — Frappe doesn't replay POS to compute
		# current stock; the SR sets a level and SLEs from POS deductions are per-transaction stocks.
		# For demo purposes the Bin balance after seeding should land near (cover * baseline today).
		items_rows = []
		for category, abbr in CATEGORIES.items():
			for code_suffix, _name, _uom, rate, _sup, _baseline in ITEMS_BY_CATEGORY[category]:
				item_code = f"ITM-{abbr}-{code_suffix}"
				rate_today = baseline[(item_code, full_wh, t)]
				cover = days_of_cover(item_code)
				# Add 90 days of consumption-equivalent so post-POS deductions land at the target.
				# Total opening qty = cover_target_today + sum(actuals over 90 days) approx.
				historical_consumption = sum(
					baseline[(item_code, full_wh, add_days(t, d))] for d in range(-HISTORICAL_DAYS, 0)
				)
				target_qty = cover * rate_today + historical_consumption
				items_rows.append(
					{
						"item_code": item_code,
						"warehouse": full_wh,
						"qty": round(target_qty, 2),
						"valuation_rate": round(rates[item_code] * 0.6, 2),
					}
				)

		sr = frappe.get_doc(
			{
				"doctype": "Stock Reconciliation",
				"purpose": "Opening Stock",
				"company": COMPANY_NAME,
				"posting_date": posting_date,
				"set_posting_time": 1,
				"posting_time": "00:00:00",
				"expense_account": f"Temporary Opening - {COMPANY_ABBR}",
				"items": items_rows,
			}
		)
		sr.insert(ignore_permissions=True)
		sr.submit()


# ---------------------------------------------------------------------------
# Phase 6 — Material Requests
# ---------------------------------------------------------------------------


def seed_material_requests(baseline: dict):
	"""15 MRs total, 5 each in Draft / To Receive / Received."""
	t = today()
	default_wh = f"{WAREHOUSES[0]} - {COMPANY_ABBR}"

	# Pick distinct items + suppliers from STOCKOUT_RISK_ITEMS for variety.
	risk_items = list(STOCKOUT_RISK_ITEMS)

	def mr_payload(item_code: str, schedule_date, transaction_date):
		full_wh = f"{WAREHOUSES[0]} - {COMPANY_ABBR}"
		base = baseline[(item_code, full_wh, t)]
		qty = round(max(20, base * 14), 0)  # 14-day cover request
		return {
			"doctype": "Material Request",
			"material_request_type": "Purchase",
			"company": COMPANY_NAME,
			"transaction_date": transaction_date,
			"schedule_date": schedule_date,
			"helix_generated": 1,
			"items": [
				{
					"item_code": item_code,
					"qty": qty,
					"warehouse": default_wh,
					"schedule_date": schedule_date,
				}
			],
		}

	# 5 Drafts
	for i in range(5):
		item_code = risk_items[i % len(risk_items)]
		doc = frappe.get_doc(mr_payload(item_code, add_days(t, 7), t))
		doc.insert(ignore_permissions=True)

	# 5 To Receive (submitted yesterday, awaiting receipt)
	to_receive_names = []
	for i in range(5):
		item_code = risk_items[(i + 1) % len(risk_items)]
		doc = frappe.get_doc(mr_payload(item_code, add_days(t, 5), add_days(t, -1)))
		doc.insert(ignore_permissions=True)
		doc.submit()
		to_receive_names.append(doc.name)

	# 5 Received (PR submitted, MR closed)
	for i in range(5):
		item_code = risk_items[(i + 2) % len(risk_items)]
		doc = frappe.get_doc(mr_payload(item_code, add_days(t, -2), add_days(t, -5)))
		doc.insert(ignore_permissions=True)
		doc.submit()
		_make_purchase_receipt(doc, item_code)


def _make_purchase_receipt(mr_doc, item_code: str):
	"""Create + submit a Purchase Receipt against a Material Request to flip it to Received.

	v15 doesn't expose `make_purchase_receipt` from MR (it was removed in favor of MR→PO→PR).
	For the demo, we build the PR directly and reference the MR on each item — submitting the
	PR updates `per_received` on the linked MR, flipping its status to "Received".
	"""
	default_supplier = frappe.db.get_value(
		"Item Default", {"parent": item_code, "company": COMPANY_NAME}, "default_supplier"
	)
	supplier = default_supplier or _first_existing_supplier()
	rate = frappe.db.get_value("Item", item_code, "valuation_rate") or 1.0

	pr_items = []
	for mr_item in mr_doc.items:
		pr_items.append(
			{
				"item_code": mr_item.item_code,
				"qty": mr_item.qty,
				"received_qty": mr_item.qty,
				"rejected_qty": 0,
				"rate": rate,
				"warehouse": mr_item.warehouse,
				"material_request": mr_doc.name,
				"material_request_item": mr_item.name,
				"schedule_date": mr_item.schedule_date,
				"stock_uom": frappe.db.get_value("Item", mr_item.item_code, "stock_uom") or "Nos",
				"uom": frappe.db.get_value("Item", mr_item.item_code, "stock_uom") or "Nos",
				"conversion_factor": 1.0,
			}
		)

	pr = frappe.get_doc(
		{
			"doctype": "Purchase Receipt",
			"supplier": supplier,
			"company": COMPANY_NAME,
			"posting_date": today(),
			"helix_generated": 1,
			"items": pr_items,
		}
	)
	pr.insert(ignore_permissions=True)
	pr.submit()


def _first_existing_supplier() -> str:
	for s in SUPPLIERS:
		if frappe.db.exists("Supplier", s):
			return s
	return SUPPLIERS[0]


# ---------------------------------------------------------------------------
# Phase 7 — Demo users + landing page
# ---------------------------------------------------------------------------


def ensure_demo_users_and_landing_page():
	for email, fullname, roles in [
		(ADMIN_USER, "Helix Admin", ["System Manager", "Stock Manager", "Purchase Manager"]),
		(DEMO_USER, "Helix Demo", ["Stock User", "Purchase User", "Sales User"]),
	]:
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": fullname.split(" ")[0],
					"last_name": " ".join(fullname.split(" ")[1:]) or "User",
					"send_welcome_email": 0,
					"enabled": 1,
					"new_password": DEMO_PASSWORD,
					"roles": [{"role": r} for r in roles if frappe.db.exists("Role", r)],
				}
			)
			user.insert(ignore_permissions=True)
		else:
			# Ensure roles up to date
			user = frappe.get_doc("User", email)
			existing = {r.role for r in user.roles}
			for r in roles:
				if r not in existing and frappe.db.exists("Role", r):
					user.append("roles", {"role": r})
			user.save(ignore_permissions=True)

	# Set Helix SOP as default workspace for the demo user.
	# Workspace name has no '&' so the URL slug becomes /app/helix-sop;
	# Frappe routes URLs with %26 through the website bundle, which has no desk navbar.
	ws_name = "Helix SOP" if frappe.db.exists("Workspace", "Helix SOP") else "Helix S&OP"
	if frappe.db.exists("Workspace", ws_name):
		for u in (DEMO_USER, ADMIN_USER, "Administrator"):
			if frappe.db.exists("User", u):
				frappe.db.set_value("User", u, "default_workspace", ws_name)
				frappe.db.set_value(
					"User", u, "home_settings", f'{{"workspace_visited":["{ws_name}"]}}'
				)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _chunked_multi_insert(doctype: str, fields: list[str], rows: list[tuple], chunk: int = 2000):
	"""Multi-row INSERT in chunks via frappe.db.sql (works on MariaDB and Postgres)."""
	if not rows:
		return
	col_list = ", ".join(f"`{f}`" for f in fields)
	placeholder = "(" + ", ".join(["%s"] * len(fields)) + ")"
	for i in range(0, len(rows), chunk):
		batch = rows[i : i + chunk]
		values_sql = ", ".join([placeholder] * len(batch))
		flat = [v for row in batch for v in row]
		frappe.db.sql(
			f"INSERT INTO `tab{doctype}` ({col_list}) VALUES {values_sql}",
			flat,
		)


def _print_summary(t0: float):
	pos_count = frappe.db.count("POS Daily Sales")
	df_count = frappe.db.count("Demand Forecast")
	fr_count = frappe.db.count("Forecast Run")
	mr_count = frappe.db.count("Material Request", {"helix_generated": 1})
	pr_count = frappe.db.count("Purchase Receipt", {"helix_generated": 1})
	sr_count = frappe.db.count("Stock Reconciliation", {"company": COMPANY_NAME})
	item_count = frappe.db.count("Item")
	elapsed = time.time() - t0
	print("=" * 60)
	print(f"[helix-seed] DONE in {elapsed:.1f}s")
	print(f"  Items:                  {item_count}")
	print(f"  Forecast Runs:          {fr_count}  (1 Active + {fr_count - 1} Archived)")
	print(f"  Demand Forecasts:       {df_count}")
	print(f"  POS Daily Sales:        {pos_count}")
	print(f"  Stock Reconciliations:  {sr_count}")
	print(f"  Material Requests:      {mr_count}")
	print(f"  Purchase Receipts:      {pr_count}")
	print("=" * 60)
