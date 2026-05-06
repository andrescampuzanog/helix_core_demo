app_name = "helix_core"
app_title = "Helix Core"
app_publisher = "Helix"
app_description = "Helix Demand Forecasting & S&OP — DocTypes, seed data, workspace"
app_email = "demo@helix.mx"
app_license = "mit"

required_apps = ["erpnext"]

fixtures = [
	{
		"doctype": "Custom Field",
		"filters": [
			[
				"name",
				"in",
				[
					"Material Request-helix_generated",
					"Purchase Receipt-helix_generated",
					"Item-helix_at_risk",
				],
			]
		],
	}
]
