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

after_install = [
    "helix_core.helix_core.module_visibility.apply_module_visibility",
    "helix_core.helix_core.seed.seed_demo.run"
]

after_migrate = [
    "helix_core.helix_core.module_visibility.apply_module_visibility",
    "helix_core.helix_core.seed.seed_demo.after_migrate"
]
