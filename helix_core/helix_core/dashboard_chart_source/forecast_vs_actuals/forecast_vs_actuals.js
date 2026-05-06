frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Forecast vs Actuals"] = {
	method: "helix_core.helix_core.dashboard_chart_source.forecast_vs_actuals.forecast_vs_actuals.get",
	filters: [
		{
			fieldname: "item_group",
			label: __("Category"),
			fieldtype: "Link",
			options: "Item Group",
			default: "",
		},
	],
};
