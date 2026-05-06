import frappe
import json


@frappe.whitelist()
def workspace_state():
	out = {}
	out["workspaces"] = frappe.get_all(
		"Workspace",
		filters={"name": ["like", "%elix%"]},
		fields=["name", "label", "title", "public", "for_user", "module"],
	)
	wsname = "Helix SOP" if frappe.db.exists("Workspace", "Helix SOP") else "Helix S&OP"
	if frappe.db.exists("Workspace", wsname):
		ws = frappe.get_doc("Workspace", wsname)
		out["target_ws"] = wsname
		out["number_cards"] = [{"label": r.label, "card": r.number_card_name} for r in ws.number_cards]
		out["charts"] = [{"label": r.label, "chart": r.chart_name} for r in ws.charts]
		out["roles"] = [r.role for r in ws.roles]
		out["public"] = ws.public
		out["for_user"] = ws.for_user
	return out


@frappe.whitelist()
def workspace_blocks():
	ws = frappe.get_doc("Workspace", "Helix SOP" if frappe.db.exists("Workspace", "Helix SOP") else "Helix S&OP")
	out = {"len_content": len(ws.content), "blocks": [], "parse_error": None}
	try:
		parsed = json.loads(ws.content)
		for b in parsed:
			t = b.get("type")
			d = b.get("data", {})
			ref = (
				d.get("number_card_name")
				or d.get("chart_name")
				or d.get("shortcut_name")
				or d.get("card_name")
				or str(d.get("text", ""))[:40]
			)
			out["blocks"].append(f"{t}: {ref}")
	except Exception as e:
		out["parse_error"] = str(e)
	return out


@frappe.whitelist()
def rename_workspace_to_sop():
	"""Rename 'Helix S&OP' workspace to 'Helix SOP' so the URL has no & character.

	The display label/title remain 'Helix S&OP'. The route becomes /app/helix-sop.
	"""
	if frappe.db.exists("Workspace", "Helix S&OP") and not frappe.db.exists("Workspace", "Helix SOP"):
		frappe.rename_doc("Workspace", "Helix S&OP", "Helix SOP", force=True, ignore_permissions=True)

	ws = frappe.get_doc("Workspace", "Helix SOP")
	ws.label = "Helix S&OP"
	ws.title = "Helix S&OP"
	ws.public = 1
	ws.save(ignore_permissions=True)

	# Update demo user landing page
	frappe.db.set_value("User", "demo@helix.mx", "default_workspace", "Helix SOP")
	frappe.db.commit()

	return {
		"renamed_to": ws.name,
		"label": ws.label,
		"demo_default_workspace": frappe.db.get_value("User", "demo@helix.mx", "default_workspace"),
	}
