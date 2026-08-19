"""
Generate a Power BI Project (.pbip) with a real semantic model. See the
sibling script in financial-investment-analytics/scripts/generate_pbip.py
for the full design rationale (TMSL not TMDL, programmatic not hand-typed,
etc.) — same approach, this project's tables/relationships/measures.

Usage: py -3.10 scripts/generate_pbip.py
"""
import json
import uuid
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
EXPORTS_DIR = ROOT / "exports"
DASHBOARD_DIR = ROOT / "dashboard"
PROJECT_NAME = "Inventory Supply Chain Analytics"

TABLES = [
    "dim_product", "dim_supplier", "fulfilment_rate",
    "inventory_turnover", "slow_moving_stock", "supplier_lead_time",
]

RELATIONSHIPS = [
    ("inventory_turnover", "product_id", "dim_product", "product_id"),
    ("slow_moving_stock", "product_id", "dim_product", "product_id"),
    ("supplier_lead_time", "supplier_id", "dim_supplier", "supplier_id"),
]

MEASURES = {
    "inventory_turnover": {
        "Avg Turnover Proxy": "AVERAGE(inventory_turnover[turnover_proxy_using_current_stock])",
        "Total Units Sold": "SUM(inventory_turnover[total_units_sold])",
    },
    "slow_moving_stock": {
        "Slow Moving Product Count":
            "CALCULATE(COUNTROWS(slow_moving_stock), slow_moving_stock[is_slow_moving] = TRUE)",
        "Slow Moving Stock Value":
            "CALCULATE(SUMX(slow_moving_stock, slow_moving_stock[units_in_stock]), "
            "slow_moving_stock[is_slow_moving] = TRUE)",
        "Avg Days Since Last Sale": "AVERAGE(slow_moving_stock[days_since_last_sale])",
    },
    "supplier_lead_time": {
        "Avg Lead Time Days": "AVERAGE(supplier_lead_time[avg_lead_time_days])",
        "Avg Late Delivery %": "AVERAGE(supplier_lead_time[late_delivery_pct])",
        "Fastest Supplier":
            "CALCULATE(SELECTEDVALUE(supplier_lead_time[company_name]), "
            "supplier_lead_time[rank_by_fastest_avg_lead_time] = 1)",
    },
}


def pandas_dtype_to_tmsl(dtype):
    if pd.api.types.is_bool_dtype(dtype):
        return "boolean", "type logical"
    if pd.api.types.is_integer_dtype(dtype):
        return "int64", "Int64.Type"
    if pd.api.types.is_float_dtype(dtype):
        return "double", "type number"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "dateTime", "type date"
    return "string", "type text"


def guess_and_parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if df[col].dtype == object and "date" in col.lower():
            try:
                parsed = pd.to_datetime(df[col])
                if parsed.notna().all():
                    df[col] = parsed
            except (ValueError, TypeError):
                pass
    return df


def build_table(csv_path: Path) -> dict:
    df = pd.read_csv(csv_path)
    df = guess_and_parse_dates(df)
    table_name = csv_path.stem

    columns, m_type_casts = [], []
    for col in df.columns:
        tmsl_type, m_cast = pandas_dtype_to_tmsl(df[col].dtype)
        columns.append({
            "name": col,
            "dataType": tmsl_type,
            "sourceColumn": col,
            "lineageTag": str(uuid.uuid4()),
            "summarizeBy": "sum" if tmsl_type in ("int64", "double") else "none",
            "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}],
        })
        m_type_casts.append(f'{{"{col}", {m_cast}}}')

    csv_abs_path = str(csv_path.resolve()).replace("\\", "\\\\")
    m_expression = (
        f'let\n'
        f'    Source = Csv.Document(File.Contents("{csv_abs_path}"),'
        f'[Delimiter=",", Columns={len(df.columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n'
        f'    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n'
        f'    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",'
        f'{{{", ".join(m_type_casts)}}})\n'
        f'in\n'
        f'    #"Changed Type"'
    )

    table = {
        "name": table_name,
        "lineageTag": str(uuid.uuid4()),
        "columns": columns,
        "partitions": [{"name": table_name, "mode": "import",
                         "source": {"type": "m", "expression": m_expression}}],
    }
    if table_name in MEASURES:
        table["measures"] = [
            {"name": mname, "expression": mexpr, "lineageTag": str(uuid.uuid4())}
            for mname, mexpr in MEASURES[table_name].items()
        ]
    return table


def build_model_bim() -> dict:
    tables = [build_table(EXPORTS_DIR / f"{t}.csv") for t in TABLES]
    relationships = [
        {"name": str(uuid.uuid4()), "fromTable": ft, "fromColumn": fc,
         "toTable": tt, "toColumn": tc, "crossFilteringBehavior": "bothDirections"}
        for ft, fc, tt, tc in RELATIONSHIPS
    ]
    return {
        "name": "Model",
        "compatibilityLevel": 1567,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": tables,
            "relationships": relationships,
            "annotations": [
                {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
                {"name": "PBI_QueryOrder", "value": json.dumps(TABLES)},
            ],
        },
    }


def write_pbip():
    DASHBOARD_DIR.mkdir(exist_ok=True)
    sm_dir = DASHBOARD_DIR / f"{PROJECT_NAME}.SemanticModel"
    report_dir = DASHBOARD_DIR / f"{PROJECT_NAME}.Report"
    sm_dir.mkdir(exist_ok=True)
    (report_dir / "definition").mkdir(parents=True, exist_ok=True)

    pbip = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{PROJECT_NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    }
    (DASHBOARD_DIR / f"{PROJECT_NAME}.pbip").write_text(json.dumps(pbip, indent=2))

    (sm_dir / "definition.pbism").write_text(json.dumps({"version": "4.2", "settings": {}}, indent=2))
    (sm_dir / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": PROJECT_NAME},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid4())},
    }, indent=2))
    (sm_dir / "model.bim").write_text(json.dumps(build_model_bim(), indent=2))

    (report_dir / "definition.pbir").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{PROJECT_NAME}.SemanticModel"}},
    }, indent=2))
    (report_dir / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": PROJECT_NAME},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid4())},
    }, indent=2))
    (report_dir / "definition" / "report.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.2.0/schema.json",
        "themeCollection": {}, "layoutOptimization": "None",
    }, indent=2))

    print(f"Generated PBIP at: {DASHBOARD_DIR / f'{PROJECT_NAME}.pbip'}")
    print(f"Tables: {TABLES}")


if __name__ == "__main__":
    write_pbip()
