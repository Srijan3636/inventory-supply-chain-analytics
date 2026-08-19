# Decisions Log

Written as the project was built, not reconstructed afterward.

---

## Data source: Northwind, verified before trusting

**Decision:** Used the `pthom/northwind_psql` GitHub port
(`raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql`) rather than
assuming a URL from memory.

**Why verified, not assumed:** Searched for the actual repo, downloaded the file, and
read the real `CREATE TABLE` statements before writing any SQL against it — the
columns are lowercase snake_case (`order_date`, `units_in_stock`, `reorder_level`),
not the CamelCase originally guessed. Confirmed no hardcoded `\c northwind` or
database name in the dump — it just runs DROP/CREATE against whatever database the
connection targets, which is why `load_data.py` can point it at `inventory_analytics`
cleanly.

---

## "Days since last sale" is anchored to the dataset's own max date, not real time

**Finding:** Northwind's order data is from 1996-1998 (verified in the raw dump:
`INSERT INTO orders VALUES (10248, 'VINET', ... '1996-07-04' ...)`).

**Decision:** Every "days since X" or "recency" calculation uses
`MAX(order_date) OVER ()` (or an equivalent reference-date CTE) as "now", not
`CURRENT_DATE`. Using `CURRENT_DATE` against 1996 data would make every single
product look ~30 years stale, which is meaningless for a slow-moving-stock analysis
— everything would tie at "very stale". Anchoring to the dataset's own latest
activity date is what makes the metric actually differentiate products.

---

## No fabricated stock history — turnover uses a defensible proxy, stated explicitly

**Finding:** `products.units_in_stock` is a single current snapshot column. Northwind
has no stock-level history table — there is no way to compute "inventory turnover"
in the textbook sense (COGS / average inventory over a period) because "average
inventory over a period" does not exist in this data.

**Decision:** Defined a proxy — units sold in a trailing window (from `order_details`)
divided by current `units_in_stock` — and labelled it explicitly as
`turnover_proxy_using_current_stock` in the SQL output, not `inventory_turnover`.
The column name itself carries the caveat so it can't be quoted out of context.
Stated the limitation in the SQL comments, this file, and the README.

**Alternative rejected:** simulating a fake historical stock series to compute
"real" turnover. Rejected outright — fabricating data to make a metric look more
rigorous than the underlying data supports is the opposite of what this project
is supposed to demonstrate.

---

## "Cleaned" means verified, not just assumed — added validate_data.py

**Finding:** Northwind arrives as an already-built relational SQL dump (see the
first entry above) — there's no messy raw data to clean the way Screener exports
or yfinance data needed cleaning. Initially this meant the pipeline had no Python
data-quality step at all, which didn't match the "cleaned... records" language
used to describe this project.

**Decision:** added `validate_data.py` — 10 real checks run against the loaded
database: referential integrity across all 4 foreign-key relationships (orphaned
`order_details` rows, products pointing to missing suppliers/categories),
date-logic sanity (`shipped_date` before `order_date`, which would be impossible),
and value sanity (negative quantities, negative prices, negative stock, null
stock). All 10 passed on real data. This is what "cleaned" actually means for
this project: not that raw data was messy and got fixed, but that the claim
"this data is analysis-ready" was checked rather than assumed. Also surfaced a
real number worth knowing before building the fulfilment/lead-time queries:
21 of 830 orders (2.5%) have no `shipped_date` and are excluded from those
calculations — already handled correctly in `supplier_lead_time.sql` and
`fulfilment_rate.sql`, now confirmed and quantified rather than just assumed.

---
