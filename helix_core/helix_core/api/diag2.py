import frappe
import json


@frappe.whitelist()
def dump_workspace(user="demo@helix.mx"):
	frappe.set_user(user)
	from frappe.desk.desktop import get_desktop_page

	res = get_desktop_page(json.dumps({"name": "Helix SOP"}))
	out = {"keys": list(res.keys()), "summary": {}}
	for k, v in res.items():
		entry = {"type": type(v).__name__}
		if isinstance(v, dict):
			entry["dict_keys"] = list(v.keys())
			for kk, vv in v.items():
				if isinstance(vv, list):
					entry[kk] = {"len": len(vv)}
					if vv and isinstance(vv[0], dict):
						entry[kk]["sample_keys"] = list(vv[0].keys())[:8]
						entry[kk]["names"] = [
							x.get("name") or x.get("chart_name") or x.get("label") for x in vv[:6]
						]
				else:
					entry[kk] = repr(vv)[:200]
		elif isinstance(v, list):
			entry["len"] = len(v)
			if v and isinstance(v[0], dict):
				entry["sample_keys"] = list(v[0].keys())[:8]
				entry["names"] = [x.get("name") or x.get("chart_name") or x.get("label") for x in v[:6]]
		out["summary"][k] = entry
	return out


@frappe.whitelist()
def fix_workspace_labels():
	ws = frappe.get_doc("Workspace", "Helix SOP")
	for r in ws.number_cards:
		r.label = r.number_card_name
	for r in ws.charts:
		r.label = r.chart_name
	for r in ws.shortcuts:
		if not r.label:
			r.label = r.link_to
	ws.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": True}


@frappe.whitelist()
def diagnose_setup_state():
	out = {}
	out["installed_apps"] = frappe.db.sql(
		"SELECT name, app_name, is_setup_complete FROM `tabInstalled Application`",
		as_dict=True,
	)
	out["system_settings_setup_complete"] = frappe.db.get_single_value("System Settings", "setup_complete")
	out["users"] = frappe.db.sql(
		"SELECT name, enabled, user_type, default_workspace, default_app FROM `tabUser` WHERE name IN ('Administrator','demo@helix.mx','admin@helix.mx')",
		as_dict=True,
	)
	from frappe.boot import get_bootinfo

	frappe.set_user("Administrator")
	boot = get_bootinfo()
	out["boot_setup_complete"] = boot.get("setup_complete")
	out["boot_navbar_settings_present"] = bool(boot.get("navbar_settings"))
	if boot.get("navbar_settings"):
		ns = boot["navbar_settings"]
		out["navbar_app_logo"] = ns.get("app_logo")
		out["navbar_logo_width"] = ns.get("logo_width")
		out["navbar_items_len"] = len(ns.get("settings_dropdown") or []) + len(ns.get("help_dropdown") or [])
	return out


@frappe.whitelist()
def force_setup_complete():
	frappe.db.sql("UPDATE `tabInstalled Application` SET is_setup_complete = 1")
	frappe.db.set_single_value("System Settings", "setup_complete", 1)
	frappe.db.set_single_value("System Settings", "country", "Mexico")
	frappe.db.set_single_value("System Settings", "language", "en")
	if not frappe.db.get_single_value("System Settings", "time_zone"):
		frappe.db.set_single_value("System Settings", "time_zone", "America/Monterrey")
	# This is THE one — desk.js:356 suppresses the navbar when boot.home_page == "setup-wizard"
	frappe.db.set_default("desktop:home_page", "workspace")
	frappe.db.commit()
	frappe.clear_cache()
	return diagnose_setup_state()


@frappe.whitelist()
def set_admin_landing_pages():
	for u in ("Administrator", "admin@helix.mx"):
		if frappe.db.exists("User", u):
			frappe.db.set_value("User", u, "default_workspace", "Helix SOP")
	frappe.db.commit()
	return {"ok": True}


@frappe.whitelist()
def diagnose_navbar(user="Administrator"):
	"""Probe everything that can suppress/break the top navbar for a given user."""
	frappe.set_user(user)
	from frappe.boot import get_bootinfo

	boot = get_bootinfo()

	out = {"user": user}
	# >>> CRITICAL: home_page == "setup-wizard" suppresses the navbar entirely (desk.js:356)
	out["boot_home_page"] = boot.get("home_page")
	out["boot_setup_complete"] = boot.get("setup_complete")
	out["boot_user_setup_complete"] = (boot.get("user") or {}).get("setup_complete")
	# fields the navbar template / vue navbar reads
	out["app_name"] = boot.get("app_name")
	out["app_logo_url"] = boot.get("app_logo_url") or boot.get("navbar_settings", {}).get("app_logo")
	out["sysdefaults_app_logo"] = frappe.db.get_default("app_logo_url")
	out["navbar_settings_present"] = bool(boot.get("navbar_settings"))

	# user-level
	out["user_default_workspace"] = boot.get("user", {}).get("default_workspace")
	out["user_roles"] = boot.get("user", {}).get("roles")
	out["session_user"] = boot.get("user", {}).get("name")

	# Navbar Settings doc
	ns = frappe.get_cached_doc("Navbar Settings")
	out["nbs_app_logo"] = getattr(ns, "app_logo", None)
	out["nbs_logo_width"] = getattr(ns, "logo_width", None)
	out["nbs_settings_dropdown_len"] = len(getattr(ns, "settings_dropdown", []) or [])
	out["nbs_help_dropdown_len"] = len(getattr(ns, "help_dropdown", []) or [])
	out["nbs_meta_fields"] = [df.fieldname for df in ns.meta.fields]

	# Website Settings (some templates fall back to this)
	out["ws_app_logo"] = frappe.db.get_single_value("Website Settings", "app_logo")
	out["ws_brand_html"] = frappe.db.get_single_value("Website Settings", "brand_html")

	# system_settings.disable_standard_email_footer or similar - not relevant.

	# is the logo file actually present on disk?
	import os
	logo_url = out["nbs_app_logo"] or ""
	if logo_url.startswith("/assets/"):
		logo_path = os.path.join(frappe.utils.get_bench_path(), "sites", logo_url.lstrip("/"))
		out["logo_disk_exists"] = os.path.exists(logo_path)
		out["logo_disk_path"] = logo_path
	else:
		out["logo_disk_exists"] = None
		out["logo_disk_path"] = logo_url

	return out


@frappe.whitelist()
def reset_navbar_settings():
	"""Restore Navbar Settings to a sane default with Helix branding."""
	ns = frappe.get_doc("Navbar Settings")
	ns.app_logo = "/assets/helix_branding/images/helix-logo.svg"
	ns.logo_width = 80
	# don't touch dropdowns - leave defaults
	ns.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache()
	return {"ok": True, "logo": ns.app_logo}
