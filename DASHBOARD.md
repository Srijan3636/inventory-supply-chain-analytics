# Power BI Dashboard — Build Guide

Every field name below is the exact column name in `exports/*.csv`.

## 1. Connect

**Get Data** → **Text/CSV** → import all 6 files from `exports/`:
`dim_product.csv`, `dim_supplier.csv`, `fulfilment_rate.csv`,
`inventory_turnover.csv`, `slow_moving_stock.csv`, `supplier_lead_time.csv`.

(Alternative: PostgreSQL, server `localhost:5432`, database
`inventory_analytics` — same as the other project.)

## 2. Relationships (Model view)

- `dim_product[product_id]` → `inventory_turnover[product_id]`
- `dim_product[product_id]` → `slow_moving_stock[product_id]`
- `dim_supplier[supplier_id]` → `supplier_lead_time[supplier_id]`

`fulfilment_rate.csv` is a standalone summary table (4 rows, one per delay
bucket) — no relationship needed, use it directly.

## 3. DAX measures

On `inventory_turnover`:
```dax
Avg Turnover Proxy = AVERAGE(inventory_turnover[turnover_proxy_using_current_stock])

Total Units Sold = SUM(inventory_turnover[total_units_sold])
```

On `slow_moving_stock`:
```dax
Slow Moving Product Count =
CALCULATE(COUNTROWS(slow_moving_stock), slow_moving_stock[is_slow_moving] = TRUE)

Slow Moving Stock Value =
CALCULATE(
    SUMX(slow_moving_stock, slow_moving_stock[units_in_stock]),
    slow_moving_stock[is_slow_moving] = TRUE
)

Avg Days Since Last Sale = AVERAGE(slow_moving_stock[days_since_last_sale])
```

On `supplier_lead_time`:
```dax
Avg Lead Time Days = AVERAGE(supplier_lead_time[avg_lead_time_days])

Avg Late Delivery % = AVERAGE(supplier_lead_time[late_delivery_pct])

Fastest Supplier =
CALCULATE(
    SELECTEDVALUE(supplier_lead_time[company_name]),
    supplier_lead_time[rank_by_fastest_avg_lead_time] = 1
)
```

## 4. Pages

**Page 1 — Inventory Health**
- Cards: `Slow Moving Product Count`, `Avg Days Since Last Sale`,
  `Avg Turnover Proxy`
- Bar chart: `slow_moving_stock[product_name]` on axis (filter visual to
  `is_slow_moving = TRUE`), `days_since_last_sale` on values, sorted descending
- Pie or donut: `slow_moving_stock[abc_class]` by count of products

**Page 2 — Supplier Performance**
- Table: `supplier_lead_time[company_name]`, `country`, `avg_lead_time_days`,
  `late_delivery_pct`, `orders_supplied` — sort by `avg_lead_time_days` ascending
- Bar chart: `company_name` on axis, `late_delivery_pct` on values (highlights
  which suppliers are actually unreliable, not just slow)
- Card: `Fastest Supplier`

**Page 3 — Fulfilment**
- Bar chart directly on `fulfilment_rate`: `delay_bucket` on axis (this table
  is already ordered logically in the SQL, but Power BI may re-sort
  alphabetically — right-click the axis field → **Sort by column** if needed,
  or add a manual sort-order column), `pct_of_orders` on values
- Card: sum of `order_count` where `delay_bucket = "On time or early"` divided
  by total (or just display the row directly from the table — it's already
  computed as `pct_of_orders`)

## 5. Formatting

Same as the other project: pick a non-default theme, format `_pct` fields as
percentages, format `total_revenue` with currency/K abbreviation.

## 6. Save and screenshot

Save as `.pbix` in `dashboard/` (gitignored). Screenshot each page into
`dashboard/screenshots/` for the README.
