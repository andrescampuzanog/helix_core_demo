from __future__ import annotations

import frappe
# all modules here - erpnext > modules.txt

HIDDEN_MODULES = {
	"Accounts",
	"Projects",
	"Setup",
	"Manufacturing",
	"Support",
	"Utilities",
	"Assets",
	"Portal",
	"Maintenance",
	"Regional",
	"ERPNext Integrations",
	"Quality Management",
	"Communication",
	"Loan Management",
	"Telephony",
	"Bulk Transaction",
	"E-commerce",
	"Subcontracting",
	"EDI",
	"Website",
	# Frappe v15 sidebar workspaces that are visible in this bench.
	"Automation",
	"Integrations",
	"CRM"
}

# Internal domain marker used by Helix to hide module-linked records.
HELIX_HIDDEN_DOMAIN = "Helix Hidden"

# Doctypes where `module` + `restrict_to_domain` are used to control visibility.
DOMAIN_RESTRICTED_DOCTYPES = ("Module Def", "DocType", "Page", "Report", "Workspace")


def apply_module_visibility() -> None:
	"""Apply Helix module visibility settings across ERPNext module-linked records."""
	hidden_modules = _normalized_hidden_modules()
	_ensure_hidden_domain()

	# Hide/unhide workspace tiles tied to each module.
	_sync_workspace_hidden_flag(hidden_modules)

	# Restrict/unrestrict module-linked records to keep hidden modules out of UI/navigation.
	for doctype in DOMAIN_RESTRICTED_DOCTYPES:
		_sync_domain_restriction(doctype, hidden_modules)

	frappe.clear_cache()


def _normalized_hidden_modules() -> set[str]:
	"""Validate module names against existing Module Def records and normalize input."""
	if not HIDDEN_MODULES:
		return set()

	existing_modules = set(frappe.get_all("Module Def", pluck="name"))
	normalized = {module.strip() for module in HIDDEN_MODULES if module and module.strip()}

	invalid = normalized - existing_modules
	if invalid:
		frappe.log_error(
			title="Helix Module Visibility",
			message=(
				"Unknown module(s) in HIDDEN_MODULES: "
				+ ", ".join(sorted(invalid))
				+ "\nValid modules are loaded from Module Def."
			),
		)

	return normalized & existing_modules


def _ensure_hidden_domain() -> None:
	if not frappe.db.exists("Domain", HELIX_HIDDEN_DOMAIN):
		frappe.get_doc({"doctype": "Domain", "domain": HELIX_HIDDEN_DOMAIN}).insert(
			ignore_permissions=True
		)


def _sync_workspace_hidden_flag(hidden_modules: set[str]) -> None:
	workspaces = frappe.get_all(
		"Workspace",
		filters={"ifnull(module, '')": ("!=", "")},
		fields=["name", "module", "is_hidden"],
	)

	for workspace in workspaces:
		should_hide = 1 if workspace.module in hidden_modules else 0
		if cint(workspace.is_hidden) != should_hide:
			frappe.db.set_value("Workspace", workspace.name, "is_hidden", should_hide, update_modified=False)


def _sync_domain_restriction(doctype: str, hidden_modules: set[str]) -> None:
	meta = frappe.get_meta(doctype)
	if not meta.has_field("module") or not meta.has_field("restrict_to_domain"):
		return

	records = frappe.get_all(
		doctype,
		filters={"ifnull(module, '')": ("!=", "")},
		fields=["name", "module", "restrict_to_domain"],
	)

	for record in records:
		if record.module in hidden_modules:
			if record.restrict_to_domain != HELIX_HIDDEN_DOMAIN:
				frappe.db.set_value(
					doctype,
					record.name,
					"restrict_to_domain",
					HELIX_HIDDEN_DOMAIN,
					update_modified=False,
				)
		else:
			# Only clear the restriction if it was set by Helix.
			if record.restrict_to_domain == HELIX_HIDDEN_DOMAIN:
				frappe.db.set_value(doctype, record.name, "restrict_to_domain", "", update_modified=False)


def cint(value) -> int:
	try:
		return int(value or 0)
	except Exception:
		return 0
