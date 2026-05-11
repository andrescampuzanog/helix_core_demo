frappe.provide("frappe.dashboards.chart_sources");
frappe.provide("frappe.widget");

(() => {
	const SOURCE_NAME = "Forecast vs Actuals";
	const DEFAULT_FORECAST_HORIZON_DAYS = 14;
	const FORECAST_HORIZON_OPTIONS = {
		"Next 2 Weeks": 14,
		"Next 4 Weeks": 28,
	};

	const get_forecast_horizon_days = (widget) => {
		const value =
			widget.selected_forecast_horizon_days ||
			widget.chart_settings?.forecast_horizon_days ||
			DEFAULT_FORECAST_HORIZON_DAYS;
		const days = Number(value);
		return Object.values(FORECAST_HORIZON_OPTIONS).includes(days)
			? days
			: DEFAULT_FORECAST_HORIZON_DAYS;
	};

	const get_forecast_horizon_label = (days) =>
		Object.keys(FORECAST_HORIZON_OPTIONS).find((label) => FORECAST_HORIZON_OPTIONS[label] === days) ||
		"Next 2 Weeks";

	const is_forecast_vs_actuals_widget = (widget) => widget.chart_doc?.source === SOURCE_NAME;

	const install_forecast_horizon_filter = () => {
		const ChartWidget = frappe.widget.widget_factory?.chart;
		if (
			!ChartWidget ||
			frappe.widget.__helix_forecast_horizon_filter_installed
		) {
			return;
		}

		const original_get_time_series_filters = ChartWidget.prototype.get_time_series_filters;
		ChartWidget.prototype.get_time_series_filters = function (...args) {
			const filters = original_get_time_series_filters.apply(this, args);
			if (!is_forecast_vs_actuals_widget(this) || this.chart_doc.type === "Heatmap") {
				return filters;
			}

			const selected_days = get_forecast_horizon_days(this);
			filters.splice(1, 0, {
				label: __(get_forecast_horizon_label(selected_days)),
				options: Object.keys(FORECAST_HORIZON_OPTIONS),
				class: "forecast-horizon-filter",
				action: (selected_item) => {
					this.selected_forecast_horizon_days = FORECAST_HORIZON_OPTIONS[selected_item];
					this.save_chart_config_for_user({
						forecast_horizon_days: this.selected_forecast_horizon_days,
					});
					this.fetch_and_update_chart();
				},
			});

			return filters;
		};

		const original_fetch = ChartWidget.prototype.fetch;
		ChartWidget.prototype.fetch = function (filters, refresh = false, args) {
			if (!is_forecast_vs_actuals_widget(this)) {
				return original_fetch.apply(this, arguments);
			}

			return frappe.xcall(this.settings.method, {
				chart_name: this.chart_doc.name,
				filters,
				refresh: refresh ? 1 : 0,
				time_interval: args?.time_interval || null,
				timespan: args?.timespan || null,
				from_date: args?.from_date || null,
				to_date: args?.to_date || null,
				heatmap_year: args?.heatmap_year || null,
				forecast_horizon_days: get_forecast_horizon_days(this),
			});
		};

		frappe.widget.__helix_forecast_horizon_filter_installed = true;
	};

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

	install_forecast_horizon_filter();
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
