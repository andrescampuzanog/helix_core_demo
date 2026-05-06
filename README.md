# Helix Core

Demand Forecasting & S&OP demo data + workspace for the Helix demo.

## What's inside

- **3 DocTypes**: `Forecast Run`, `Demand Forecast`, `POS Daily Sales`
- **Custom Fields**: `helix_generated` on Material Request and Purchase Receipt
- **Seed script** (`helix_core.seed.seed_demo.run`) — wipes and rebuilds all demo data, idempotent on masters
- **Workspace** "Helix S&OP" with 4 number cards, forecast-vs-actuals chart, MR shortcut
- **Forecast Detail** Script Report
- **Forecast vs Actuals** Dashboard Chart with category filter

## Reset / re-seed

```bash
bench --site demo.helix.localhost execute helix_core.helix_core.seed.seed_demo.run
```
Target: <60s. Wipes transactional data, leaves masters intact.

## Demo flow

Login at http://localhost:8000/ as `demo@helix.mx` / `Helix2026!` → lands on the
**Helix S&OP** workspace. KPI cards top, **Forecast vs Actuals** chart middle (try the
**Bebidas** filter to see the model tracking through the seeded promo spike), MR list
+ Forecast Detail report at the bottom.
# helix_core_demo
