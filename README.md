# Inventory & Supply Chain Analytics

**In plain English:** this project takes a real (if old — 1996-98) retail
order dataset and answers practical operations questions: which products
are sitting unsold, which suppliers deliver late, and how reliable is
delivery overall. Every result below came from actually running the code —
nothing here is made up or illustrative.

**Current status:** the data, database, and analysis are fully built and
working. The Power BI **dashboard is not built yet** — what exists is the
underlying data model (tables and formulas Power BI can read), not the actual
charts. See "What's in this repo" below for exactly what that means.

## What's in this repo — a map, in plain words

| Folder / file | What it actually is |
|---|---|
| **README.md** (this file) | Start here. What the project does and what it found |
| **scripts/** | Python programs that download and load the data |
| **sql/** | The actual database questions (queries), written in SQL |
| **exports/** | The query results, saved as spreadsheet-style CSV files |
| **dashboard/** | Power BI data-model files (see status note above — no charts yet) |
| **DASHBOARD.md** | Step-by-step instructions to finish building the visual dashboard |
| **DECISIONS.md** | A log of tricky decisions made while building this, and why |
| **QUESTIONS.md** | Practice interview questions about this project, with honest answers |

If you only read one section below, read **Findings** — it's the actual
output of this project in plain numbers.

## Data source

[Northwind](https://github.com/pthom/northwind_psql), the classic
relational-database sample dataset — 830 orders, 2,155 order line items, 77
products, 29 suppliers, spanning 1996-1998. Verified all 4 foreign-key
relationships and value ranges before analysis (`scripts/validate_data.py`,
10/10 checks pass — see DECISIONS.md).

## Reproduce it yourself

```bash
py -3.10 -m pip install -r requirements.txt
cp .env.example .env   # fill in your Postgres password
py -3.10 scripts/download_northwind.py   # or manually save the dump to data/raw/
py -3.10 scripts/load_data.py            # creates DB, loads the dump
py -3.10 scripts/validate_data.py        # 10 data-quality checks
py -3.10 scripts/export_data.py          # runs all 4 analysis queries
```

Then see `DASHBOARD.md` for the Power BI build guide.

## Findings

- **95.4% of orders ship on time or early.** The remaining 4.6% splits into
  3.5% just 1-7 days late, and only 0.6% (5 orders total) more than two weeks
  late — fulfilment is broadly reliable across this dataset
- **Fastest supplier: Lyngbysild** (Denmark) — 6.3-day average lead time,
  2.7% late-delivery rate, across 37 orders
- **Slowest supplier: Karkki Oy** (Finland) — 10.2-day average lead time,
  4.6% late-delivery rate
- **3 of 77 products (3.9%) flagged as slow-moving** — hasn't sold in 90+ days
  while still holding stock. Small in absolute count, but exactly the kind of
  thing this analysis is built to surface before it becomes a bigger problem

## Two honest scope decisions

**"Inventory turnover" is a proxy, not the textbook metric.** Northwind has a
single current `units_in_stock` snapshot per product — no historical stock
levels, so true turnover (COGS ÷ average inventory over a period) isn't
computable from this data. The output column is named
`turnover_proxy_using_current_stock`, not `inventory_turnover`, specifically
so the caveat travels with the number if this file is read out of context.
Full reasoning in DECISIONS.md.

**"Days since last sale" is anchored to the dataset's own latest order date
(1998-05-06), not `CURRENT_DATE`.** This is 1996-98 data — using today's date
would make every product look ~30 years stale and destroy the metric's ability
to differentiate anything.

## Limitations

- Northwind is a small (~830 orders), widely-used teaching dataset — stated
  plainly rather than presented as production-scale data
- No real inventory-turnover metric is possible without historical stock
  levels (see above) — the proxy is useful but should be named as what it is
- Data is from 1996-98; findings describe patterns in this specific dataset,
  not current supply-chain conditions

## Project structure

```
scripts/          load_data.py, validate_data.py, export_data.py
sql/analysis/      4 analysis queries, one per question
exports/           Power BI-ready CSVs
dashboard/         Power BI file (build it yourself — see DASHBOARD.md)
DECISIONS.md       every non-obvious choice and why
QUESTIONS.md       interview questions with honest answers
```
