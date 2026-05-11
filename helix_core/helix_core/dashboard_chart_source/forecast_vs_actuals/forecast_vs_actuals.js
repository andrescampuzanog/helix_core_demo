frappe.provide("frappe.dashboards.chart_sources");
frappe.provide("frappe.widget");

(() => {
	const install_actual_tail_trim = () => {
		if (frappe.__helix_forecast_tail_trim_installed || !frappe.utils?.make_chart) return;

		const original_make_chart = frappe.utils.make_chart;
		frappe.utils.make_chart = function (parent, chart_args) {
			const chart = original_make_chart.apply(this, arguments);

			if (typeof chart_args?.data?.actual_end_index === "number") {
				trim_forecast_actual_tail(chart, chart_args.data);
				const original_update = chart.update?.bind(chart);
				if (original_update && !chart.__helix_forecast_update_wrapped) {
					chart.update = (data) => {
						const result = original_update(data);
						trim_forecast_actual_tail(chart, data);
						return result;
					};
					chart.__helix_forecast_update_wrapped = true;
				}
			}

			return chart;
		};

		frappe.__helix_forecast_tail_trim_installed = true;
	};

	const trim_forecast_actual_tail = (chart, data) => {
		if (!chart || typeof data?.actual_end_index !== "number") {
			return;
		}

		const trim = () => trim_actual_tail(chart, data.actual_end_index, data.labels || []);
		requestAnimationFrame(trim);
		setTimeout(trim, 450);
	};

	const trim_actual_tail = (chart, actual_end_index, labels) => {
		if (!chart?.drawArea || actual_end_index < 0 || !labels.length) return;

		const actual_layer = chart.drawArea.querySelector(".dataset-line.dataset-1");
		const actual_path = actual_layer?.querySelector(".line-graph-path");
		const x_positions = chart.state?.xAxis?.positions || [];
		const y_positions = chart.state?.datasets?.[1]?.yPositions || [];
		const last_index = Math.min(actual_end_index, x_positions.length - 1, y_positions.length - 1);

		if (!actual_layer || !actual_path || last_index < 0) return;

		if (actual_end_index >= labels.length - 1) {
			actual_layer.querySelectorAll("[data-point-index]").forEach((point) => {
				point.style.display = "";
			});
			return;
		}

		const points = [];
		for (let index = 0; index <= last_index; index += 1) {
			points.push(`${x_positions[index]},${y_positions[index]}`);
		}

		actual_path.setAttribute("d", `M${points.join("L")}`);

		actual_layer.querySelectorAll("[data-point-index]").forEach((point) => {
			const point_index = Number(point.getAttribute("data-point-index"));
			point.style.display = point_index > actual_end_index ? "none" : "";
		});
	};

	install_actual_tail_trim();
})();

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
