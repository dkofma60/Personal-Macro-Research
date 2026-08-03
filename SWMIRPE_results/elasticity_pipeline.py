#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import Ridge


ROOT = Path("/Users/danie/Personal-Macro-Research")
DATA_DIR = ROOT / "Demand Elasticity"
RESULTS_DIR = ROOT / "results"


BASE_CATEGORIES = [
    "food_beverages",
    "housing",
    "apparel",
    "transportation",
    "medical_care",
    "recreation",
    "education_communication",
    "other_goods_services",
]


CPI_ITEM_MAP = {
    "food_beverages": "SAF",
    "housing": "SAH",
    "apparel": "SA311",
    "transportation": "SAT",
    "medical_care": "SAM",
    "recreation": "SAR",
    "education_communication": "SAE",
    "other_goods_services": "SAG",
}


CPI_FILE_MAP = {
    "SAF": "cu.data.11.USFoodBeverage",
    "SAH": "cu.data.12.USHousing",
    "SA311": "cu.data.13.USApparel",
    "SAT": "cu.data.14.USTransportation",
    "SAM": "cu.data.15.USMedical",
    "SAR": "cu.data.16.USRecreation",
    "SAE": "cu.data.17.USEducationAndCommunication",
    "SAG": "cu.data.18.USOtherGoodsAndServices",
}


REGION_TO_AREA = {
    1: "0100",  # Northeast
    2: "0200",  # Midwest
    3: "0300",  # South
    4: "0400",  # West
}


IO_CANDIDATE_MAP = {
    "food_beverages": ["11", "31G", "42", "44RT", "7"],
    "housing": ["22", "23", "FIRE", "81"],
    "apparel": ["31G", "42", "44RT"],
    "transportation": ["21", "44RT", "48TW"],
    "medical_care": ["6"],
    "recreation": ["7", "51"],
    "education_communication": ["51", "6", "PROF"],
    "other_goods_services": ["81", "FIRE", "PROF"],
}


IO_CORE_SECTORS = [
    "11",
    "21",
    "22",
    "23",
    "31G",
    "42",
    "44RT",
    "48TW",
    "51",
    "FIRE",
    "PROF",
    "6",
    "7",
    "81",
    "G",
]


def log(msg: str) -> None:
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


def weighted_mean(x: Iterable[float], w: Iterable[float]) -> float:
    xa = np.asarray(x, dtype=float)
    wa = np.asarray(w, dtype=float)
    mask = np.isfinite(xa) & np.isfinite(wa) & (wa > 0)
    if mask.sum() == 0:
        return float("nan")
    return float(np.average(xa[mask], weights=wa[mask]))


def safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def infer_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".csv"}:
        return "csv"
    if suffix in {".txt"}:
        return "text"
    if suffix in {".xlsx", ".xls"}:
        return "excel"
    if suffix in {".ipynb"}:
        return "notebook"
    if suffix in {".md"}:
        return "markdown"
    if suffix in {".png", ".jpg", ".jpeg"}:
        return "image"
    return suffix[1:] if suffix else "unknown"


def inspect_structure(path: Path) -> str:
    try:
        ftype = infer_type(path)
        if ftype == "csv":
            if path.name == "RPP_Table.csv":
                header = pd.read_csv(path, skiprows=3, nrows=0)
            else:
                header = pd.read_csv(path, nrows=0)
            cols = [str(c).strip() for c in header.columns.tolist()]
            preview = "|".join(cols[:10])
            tail = "|..." if len(cols) > 10 else ""
            return f"columns={len(cols)}:{preview}{tail}"
        if ftype == "text":
            if path.name.startswith("cu."):
                header = pd.read_csv(path, sep="\t", nrows=0)
                cols = [str(c).strip() for c in header.columns.tolist()]
                preview = "|".join(cols[:10])
                tail = "|..." if len(cols) > 10 else ""
                return f"columns={len(cols)}:{preview}{tail}"
            with path.open("r", errors="ignore") as f:
                first = f.readline().strip()
            return f"text_head={first[:120]}"
        if ftype == "excel":
            xls = pd.ExcelFile(path)
            sheets = xls.sheet_names
            preview = "|".join(sheets[:8])
            tail = "|..." if len(sheets) > 8 else ""
            return f"sheets={len(sheets)}:{preview}{tail}"
        if ftype == "notebook":
            with path.open("r", encoding="utf-8") as f:
                nb = json.load(f)
            n_cells = len(nb.get("cells", []))
            return f"cells={n_cells}"
        return ""
    except Exception as exc:
        return f"unreadable:{type(exc).__name__}"


def create_file_inventory() -> pd.DataFrame:
    log("Building recursive file inventory.")
    records = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part.startswith(".git") for part in rel.parts):
            continue
        if any(part.startswith(".venv") for part in rel.parts):
            continue
        records.append(
            {
                "file_path": str(rel),
                "inferred_type": infer_type(path),
                "size_bytes": path.stat().st_size,
                "structure": inspect_structure(path),
            }
        )
    inv = pd.DataFrame(records).sort_values("file_path").reset_index(drop=True)
    inv.to_csv(RESULTS_DIR / "file_inventory.csv", index=False)
    return inv


def write_data_notes() -> None:
    log("Writing data notes.")
    notes = textwrap.dedent(
        """
        # Data Notes

        ## CPI (`cu.*`)
        - `cu.series`, `cu.item`, and `cu.area` are metadata tables that decode CPI series ids.
        - Category files `cu.data.11` to `cu.data.18` contain monthly CPI values (`series_id`, `year`, `period`, `value`).
        - Usable broad categories align directly with Food & beverages, Housing, Apparel, Transportation, Medical care, Recreation, Education & communication, and Other goods & services.

        ## CEX Interview (`intrvw13` ... `intrvw17`)
        - The `FMLI` interview files contain household identifiers, interview month/year, survey weights (`FINLWT21`), geography (`REGION`, `STATE`), demographics, and broad quarterly spending aggregates (`FOODPQ`, `HOUSPQ`, `TRANSPQ`, etc.).
        - Overlapping quarterly bridge files across annual folders create duplicates; latest-release records are retained by deduplicating on (`NEWID`, `QINTRVYR`, `QINTRVMO`) using the newest source folder.
        - Expenditure-line folders (`expn*`) were inspected, but the broad-category aggregates already exist in `FMLI`, which is the most defensible route for this target.

        ## RPP (`RPP_Table.csv`)
        - BEA state-level annual Regional Price Parities with line codes for all items, goods, housing services, utilities, and other services.
        - Used as robustness-only cross-sectional price shifters where CEX state is available; not used as baseline identification.

        ## BEA Input-Output
        - `TOTAL AND DOMESTIC REQUIREMENTS/CxC_Domestic_Sector.xlsx` provides sector-level domestic requirements coefficients (used as a Leontief-style propagation object).
        - `SUPPLY-USE/Use_Sector.xlsx` provides sector-level personal consumption expenditure values (`F010`) used to calibrate category-to-sector mapping weights.
        """
    ).strip()
    (RESULTS_DIR / "data_notes.md").write_text(notes + "\n", encoding="utf-8")


def build_category_crosswalk() -> pd.DataFrame:
    log("Building category crosswalk.")
    rows = [
        {
            "category": "food_beverages",
            "cex_components": "FOODPQ + ALCBEVPQ",
            "cpi_item_code": "SAF",
            "rpp_proxy": "RPP goods (line 2)",
            "io_candidate_sectors": "11|31G|42|44RT|7",
            "notes": "CEX has separate food and alcohol aggregates; combined to match CPI food & beverages.",
        },
        {
            "category": "housing",
            "cex_components": "HOUSPQ",
            "cpi_item_code": "SAH",
            "rpp_proxy": "0.8*housing services (line 3) + 0.2*utilities (line 4)",
            "io_candidate_sectors": "22|23|FIRE|81",
            "notes": "Housing includes utilities and shelter-related outlays.",
        },
        {
            "category": "apparel",
            "cex_components": "APPARPQ",
            "cpi_item_code": "SA311",
            "rpp_proxy": "RPP goods (line 2)",
            "io_candidate_sectors": "31G|42|44RT",
            "notes": "Regional CPI is unavailable for this item in the provided metadata; national series is used as fallback.",
        },
        {
            "category": "transportation",
            "cex_components": "TRANSPQ",
            "cpi_item_code": "SAT",
            "rpp_proxy": "RPP goods (line 2)",
            "io_candidate_sectors": "21|44RT|48TW",
            "notes": "Aggregates vehicle-related goods and transport services.",
        },
        {
            "category": "medical_care",
            "cex_components": "HEALTHPQ",
            "cpi_item_code": "SAM",
            "rpp_proxy": "RPP other services (line 5)",
            "io_candidate_sectors": "6",
            "notes": "Direct mapping to medical-care CPI and BEA education/health sector.",
        },
        {
            "category": "recreation",
            "cex_components": "ENTERTPQ + OTHENTPQ",
            "cpi_item_code": "SAR",
            "rpp_proxy": "RPP other services (line 5)",
            "io_candidate_sectors": "7|51",
            "notes": "CEX entertainment aggregates are combined for recreation.",
        },
        {
            "category": "education_communication",
            "cex_components": "EDUCAPQ",
            "cpi_item_code": "SAE",
            "rpp_proxy": "RPP other services (line 5)",
            "io_candidate_sectors": "51|6|PROF",
            "notes": "CEX communication detail is limited in FMLI aggregate variables; education aggregate used as closest broad proxy.",
        },
        {
            "category": "other_goods_services",
            "cex_components": "PERSCAPQ + TOBACCPQ + MISCPQ",
            "cpi_item_code": "SAG",
            "rpp_proxy": "RPP other services (line 5)",
            "io_candidate_sectors": "81|FIRE|PROF",
            "notes": "Constructed as residual broad personal/miscellaneous category in FMLI aggregates.",
        },
    ]
    crosswalk = pd.DataFrame(rows)
    crosswalk.to_csv(RESULTS_DIR / "category_crosswalk.csv", index=False)
    return crosswalk


def read_csv_with_available_columns(path: Path, requested_cols: List[str]) -> pd.DataFrame:
    header = pd.read_csv(path, nrows=0, low_memory=False)
    available = [c for c in requested_cols if c in header.columns]
    df = pd.read_csv(path, usecols=available, low_memory=False)
    for col in requested_cols:
        if col not in df.columns:
            df[col] = np.nan
    return df[requested_cols]


def process_cex() -> pd.DataFrame:
    log("Processing CEX FMLI files.")
    requested_cols = [
        "NEWID",
        "QINTRVYR",
        "QINTRVMO",
        "FINLWT21",
        "REGION",
        "STATE",
        "BLS_URBN",
        "FAM_SIZE",
        "AGE_REF",
        "EDUC_REF",
        "TOTEXPPQ",
        "FOODPQ",
        "ALCBEVPQ",
        "HOUSPQ",
        "APPARPQ",
        "TRANSPQ",
        "HEALTHPQ",
        "ENTERTPQ",
        "OTHENTPQ",
        "EDUCAPQ",
        "PERSCAPQ",
        "TOBACCPQ",
        "MISCPQ",
    ]
    parts = []
    for yy in range(13, 18):
        folder = DATA_DIR / f"intrvw{yy}" / f"intrvw{yy}"
        fmli_paths = sorted(folder.glob("fmli*.csv"))
        for path in fmli_paths:
            df = read_csv_with_available_columns(path, requested_cols)
            df["source_release"] = yy
            df["source_file"] = path.name
            parts.append(df)
    raw = pd.concat(parts, ignore_index=True)

    numeric_cols = [c for c in requested_cols if c != "NEWID"]
    for col in numeric_cols:
        raw[col] = safe_numeric(raw[col])
    raw["NEWID"] = safe_numeric(raw["NEWID"])

    raw = raw[(raw["QINTRVYR"] >= 2013) & (raw["QINTRVYR"] <= 2017)].copy()
    raw = raw.sort_values(["NEWID", "QINTRVYR", "QINTRVMO", "source_release"])
    raw = raw.drop_duplicates(["NEWID", "QINTRVYR", "QINTRVMO"], keep="last").copy()

    raw["year"] = raw["QINTRVYR"].astype(int)
    raw["month"] = raw["QINTRVMO"].astype(int)
    raw["quarter"] = ((raw["month"] - 1) // 3 + 1).astype(int)

    # Conservative treatment: negative expenditures are set to zero to keep category shares interpretable.
    raw["exp_food_beverages"] = (
        raw["FOODPQ"].fillna(0.0) + raw["ALCBEVPQ"].fillna(0.0)
    ).clip(lower=0.0)
    raw["exp_housing"] = raw["HOUSPQ"].fillna(0.0).clip(lower=0.0)
    raw["exp_apparel"] = raw["APPARPQ"].fillna(0.0).clip(lower=0.0)
    raw["exp_transportation"] = raw["TRANSPQ"].fillna(0.0).clip(lower=0.0)
    raw["exp_medical_care"] = raw["HEALTHPQ"].fillna(0.0).clip(lower=0.0)
    raw["exp_recreation"] = (
        raw["ENTERTPQ"].fillna(0.0) + raw["OTHENTPQ"].fillna(0.0)
    ).clip(lower=0.0)
    raw["exp_education_communication"] = raw["EDUCAPQ"].fillna(0.0).clip(lower=0.0)
    raw["exp_other_goods_services"] = (
        raw["PERSCAPQ"].fillna(0.0)
        + raw["TOBACCPQ"].fillna(0.0)
        + raw["MISCPQ"].fillna(0.0)
    ).clip(lower=0.0)

    exp_cols = [f"exp_{c}" for c in BASE_CATEGORIES]
    raw["total_expenditure"] = raw[exp_cols].sum(axis=1)
    raw["sample_weight"] = raw["FINLWT21"].fillna(0.0)

    raw = raw[(raw["sample_weight"] > 0) & (raw["total_expenditure"] > 0)].copy()
    raw["household_id"] = raw["NEWID"].astype("Int64")
    raw["region"] = raw["REGION"].round().astype("Int64")
    raw["state"] = raw["STATE"].round().astype("Int64")
    raw["bls_urbn"] = raw["BLS_URBN"]
    raw["fam_size"] = raw["FAM_SIZE"]
    raw["age_ref"] = raw["AGE_REF"]
    raw["educ_ref"] = raw["EDUC_REF"]
    raw["period"] = raw["year"].astype(str) + "Q" + raw["quarter"].astype(str)

    for c in BASE_CATEGORIES:
        raw[f"share_{c}"] = raw[f"exp_{c}"] / raw["total_expenditure"]

    keep_cols = [
        "household_id",
        "year",
        "quarter",
        "month",
        "period",
        "region",
        "state",
        "sample_weight",
        "total_expenditure",
        "TOTEXPPQ",
        "fam_size",
        "age_ref",
        "educ_ref",
        "bls_urbn",
        "source_release",
        "source_file",
    ] + exp_cols + [f"share_{c}" for c in BASE_CATEGORIES]
    cex = raw[keep_cols].copy()

    cex.to_parquet(RESULTS_DIR / "cex_clean.parquet", index=False)

    share_rows = []
    for c in BASE_CATEGORIES:
        s = weighted_mean(cex[f"share_{c}"], cex["sample_weight"])
        x = weighted_mean(cex[f"exp_{c}"], cex["sample_weight"])
        share_rows.append(
            {
                "category": c,
                "weighted_share": s,
                "weighted_quarterly_expenditure": x,
            }
        )
    share_df = pd.DataFrame(share_rows)
    share_df["weighted_share_sum"] = share_df["weighted_share"].sum()
    share_df.to_csv(RESULTS_DIR / "cex_category_shares.csv", index=False)
    return cex


def read_cpi_meta(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def process_cpi() -> Tuple[pd.DataFrame, pd.DataFrame]:
    log("Processing CPI metadata and category panels.")
    series = read_cpi_meta(DATA_DIR / "cu.series")
    item = read_cpi_meta(DATA_DIR / "cu.item")
    area = read_cpi_meta(DATA_DIR / "cu.area")

    series = series[
        series["series_id"].str.startswith("CUUR")
        & series["seasonal"].eq("U")
        & series["periodicity_code"].eq("R")
    ].copy()

    series = series.merge(item[["item_code", "item_name"]], on="item_code", how="left")
    series = series.merge(area[["area_code", "area_name"]], on="area_code", how="left")

    selected_rows = []
    for category, item_code in CPI_ITEM_MAP.items():
        for area_code in ["0000", "0100", "0200", "0300", "0400"]:
            s = series[
                (series["item_code"] == item_code) & (series["area_code"] == area_code)
            ].copy()
            fallback = False
            if s.empty and area_code != "0000":
                s = series[
                    (series["item_code"] == item_code) & (series["area_code"] == "0000")
                ].copy()
                fallback = True
            if s.empty:
                continue
            s = s.sort_values(["end_year", "begin_year", "series_id"], ascending=False).head(1)
            row = s.iloc[0].to_dict()
            row["category"] = category
            row["requested_area_code"] = area_code
            row["fallback_to_national"] = fallback
            selected_rows.append(row)
    cpi_series_used = pd.DataFrame(selected_rows)
    cpi_series_used.to_csv(RESULTS_DIR / "cpi_series_used.csv", index=False)

    data_parts = []
    for item_code, filename in CPI_FILE_MAP.items():
        df = pd.read_csv(DATA_DIR / filename, sep="\t", dtype=str)
        df.columns = [c.strip() for c in df.columns]
        for c in df.columns:
            df[c] = df[c].astype(str).str.strip()
        df["item_code"] = item_code
        data_parts.append(df)
    cpi_data = pd.concat(data_parts, ignore_index=True)
    cpi_data["year"] = safe_numeric(cpi_data["year"])
    cpi_data["month"] = safe_numeric(cpi_data["period"].str.replace("M", "", regex=False))
    cpi_data["value"] = safe_numeric(cpi_data["value"])
    cpi_data = cpi_data[
        cpi_data["year"].between(2013, 2017)
        & cpi_data["month"].between(1, 12)
        & cpi_data["value"].notna()
    ].copy()
    cpi_data["quarter"] = ((cpi_data["month"] - 1) // 3 + 1).astype(int)

    sel = cpi_series_used[["category", "requested_area_code", "series_id"]].copy()
    merged = cpi_data.merge(sel, on="series_id", how="inner")
    merged["region"] = merged["requested_area_code"].map(
        {"0000": 0, "0100": 1, "0200": 2, "0300": 3, "0400": 4}
    )
    panel = (
        merged.groupby(["category", "region", "year", "quarter"], as_index=False)["value"]
        .mean()
        .rename(columns={"value": "cpi_value"})
    )

    idx = pd.MultiIndex.from_product(
        [
            BASE_CATEGORIES,
            [0, 1, 2, 3, 4],
            [2013, 2014, 2015, 2016, 2017],
            [1, 2, 3, 4],
        ],
        names=["category", "region", "year", "quarter"],
    )
    panel = panel.set_index(["category", "region", "year", "quarter"]).reindex(idx).reset_index()

    # Fill missing regional category values with national values.
    nat = panel[panel["region"] == 0][["category", "year", "quarter", "cpi_value"]].rename(
        columns={"cpi_value": "nat_cpi"}
    )
    panel = panel.merge(nat, on=["category", "year", "quarter"], how="left")
    panel["cpi_value"] = panel["cpi_value"].fillna(panel["nat_cpi"])
    panel = panel.drop(columns=["nat_cpi"])

    base = panel[(panel["region"] == 0) & (panel["year"] == 2013) & (panel["quarter"] == 1)][
        ["category", "cpi_value"]
    ].set_index("category")["cpi_value"]
    panel["base_cpi_2013q1"] = panel["category"].map(base)
    panel["price_index"] = panel["cpi_value"] / panel["base_cpi_2013q1"] * 100.0
    panel["log_price"] = np.log(panel["price_index"])
    panel.to_parquet(RESULTS_DIR / "cpi_category_panel.parquet", index=False)
    return panel, cpi_series_used


def process_rpp() -> pd.DataFrame:
    log("Processing RPP table.")
    rpp = pd.read_csv(DATA_DIR / "RPP_Table.csv", skiprows=3)
    rpp["GeoFIPS"] = rpp["GeoFIPS"].astype(str).str.zfill(5)
    rpp["state"] = (safe_numeric(rpp["GeoFIPS"]) // 1000).astype("Int64")
    rpp["LineCode"] = safe_numeric(rpp["LineCode"]).astype("Int64")
    year_cols = [c for c in rpp.columns if c.isdigit()]
    long = rpp.melt(
        id_vars=["GeoFIPS", "GeoName", "LineCode", "Description", "state"],
        value_vars=year_cols,
        var_name="year",
        value_name="rpp_value",
    )
    long["year"] = safe_numeric(long["year"]).astype("Int64")
    long["rpp_value"] = safe_numeric(long["rpp_value"])
    long = long[
        long["year"].between(2013, 2017)
        & long["LineCode"].isin([1, 2, 3, 4, 5])
        & long["rpp_value"].notna()
    ].copy()

    line_name = {
        1: "rpp_all_items",
        2: "rpp_goods",
        3: "rpp_housing_services",
        4: "rpp_utilities",
        5: "rpp_other_services",
    }
    long["line_name"] = long["LineCode"].map(line_name)
    wide = (
        long.pivot_table(
            index=["state", "GeoName", "year"],
            columns="line_name",
            values="rpp_value",
            aggfunc="first",
        )
        .reset_index()
        .rename(columns={"GeoName": "state_name"})
    )
    wide.to_csv(RESULTS_DIR / "rpp_clean.csv", index=False)

    notes = textwrap.dedent(
        """
        # RPP Usage Notes

        - RPP is annual state-level (not monthly/quarterly), so it is used only as a supplemental robustness layer.
        - Baseline identification uses CPI time/region variation.
        - Robustness adjustment applies RPP multipliers to CPI levels by category group:
          - goods-heavy categories: `rpp_goods`
          - housing: `0.8*rpp_housing_services + 0.2*rpp_utilities`
          - service-heavy categories: `rpp_other_services`
        - Missing CEX state or missing RPP values default to multiplier 1.
        """
    ).strip()
    (RESULTS_DIR / "rpp_usage_notes.md").write_text(notes + "\n", encoding="utf-8")
    return wide


def merge_cex_prices(
    cex: pd.DataFrame,
    cpi_panel: pd.DataFrame,
    price_mode: str = "regional",
    use_rpp: bool = False,
    rpp: pd.DataFrame | None = None,
) -> pd.DataFrame:
    work = cex.copy()
    panel = cpi_panel.copy()

    if price_mode == "regional":
        price = panel[panel["region"].isin([1, 2, 3, 4])].copy()
        wide = price.pivot_table(
            index=["year", "quarter", "region"],
            columns="category",
            values="price_index",
            aggfunc="first",
        )
        wide.columns = [f"price_{c}" for c in wide.columns]
        wide = wide.reset_index()
        merged = work.merge(wide, on=["year", "quarter", "region"], how="left")
    elif price_mode == "national":
        price = panel[panel["region"] == 0].copy()
        wide = price.pivot_table(
            index=["year", "quarter"],
            columns="category",
            values="price_index",
            aggfunc="first",
        )
        wide.columns = [f"price_{c}" for c in wide.columns]
        wide = wide.reset_index()
        merged = work.merge(wide, on=["year", "quarter"], how="left")
    else:
        raise ValueError("price_mode must be 'regional' or 'national'")

    if use_rpp and rpp is not None:
        rpp_cols = [
            "state",
            "year",
            "rpp_goods",
            "rpp_housing_services",
            "rpp_utilities",
            "rpp_other_services",
            "rpp_all_items",
        ]
        rpp2 = rpp[rpp_cols].copy()
        merged = merged.merge(rpp2, on=["state", "year"], how="left")

        merged["mult_food_beverages"] = merged["rpp_goods"] / 100.0
        merged["mult_housing"] = (
            0.8 * merged["rpp_housing_services"] + 0.2 * merged["rpp_utilities"]
        ) / 100.0
        merged["mult_apparel"] = merged["rpp_goods"] / 100.0
        merged["mult_transportation"] = merged["rpp_goods"] / 100.0
        merged["mult_medical_care"] = merged["rpp_other_services"] / 100.0
        merged["mult_recreation"] = merged["rpp_other_services"] / 100.0
        merged["mult_education_communication"] = merged["rpp_other_services"] / 100.0
        merged["mult_other_goods_services"] = merged["rpp_other_services"] / 100.0

        for c in BASE_CATEGORIES:
            mult_col = f"mult_{c}"
            merged[mult_col] = merged[mult_col].fillna(1.0)
            merged[f"price_{c}"] = merged[f"price_{c}"] * merged[mult_col]

    for c in BASE_CATEGORIES:
        merged[f"logp_{c}"] = np.log(merged[f"price_{c}"])
    return merged


def apply_grouping(
    df: pd.DataFrame, groups: Dict[str, List[str]], weight_col: str = "sample_weight"
) -> pd.DataFrame:
    out = df.copy()
    for new_cat, components in groups.items():
        exp_cols = [f"exp_{c}" for c in components]
        out[f"exp_{new_cat}"] = out[exp_cols].sum(axis=1)

        if len(components) == 1:
            out[f"logp_{new_cat}"] = out[f"logp_{components[0]}"]
        else:
            comp_weights = []
            for c in components:
                comp_weights.append(weighted_mean(out[f"exp_{c}"], out[weight_col]))
            comp_weights = np.asarray(comp_weights, dtype=float)
            if np.nansum(comp_weights) <= 0:
                comp_weights = np.repeat(1.0 / len(components), len(components))
            else:
                comp_weights = comp_weights / np.nansum(comp_weights)
            combo = np.zeros(len(out))
            for w, c in zip(comp_weights, components):
                combo = combo + w * out[f"logp_{c}"].to_numpy()
            out[f"logp_{new_cat}"] = combo
    return out


@dataclass
class DemandResult:
    categories: List[str]
    shares: np.ndarray
    beta: np.ndarray
    gamma: np.ndarray
    elasticity_matrix: np.ndarray
    weighted_mean: float
    table: pd.DataFrame
    design_rank: str


def estimate_demand_system(
    df: pd.DataFrame,
    categories: List[str],
    weight_col: str = "sample_weight",
    regularized: bool = False,
) -> DemandResult:
    work = df.copy()
    exp_cols = [f"exp_{c}" for c in categories]
    logp_cols = [f"logp_{c}" for c in categories]

    work["total_model_exp"] = work[exp_cols].sum(axis=1)
    for c in categories:
        work[f"share_{c}"] = work[f"exp_{c}"] / work["total_model_exp"]

    valid = (
        work["total_model_exp"].gt(0)
        & work[weight_col].gt(0)
        & work[logp_cols].notna().all(axis=1)
        & work[[f"share_{c}" for c in categories]].notna().all(axis=1)
    )
    work = work[valid].copy()

    stone = np.zeros(len(work))
    for c in categories:
        stone = stone + work[f"share_{c}"].to_numpy() * work[f"logp_{c}"].to_numpy()
    work["ln_real_exp"] = np.log(work["total_model_exp"]) - stone

    work["fam_size"] = safe_numeric(work["fam_size"]).fillna(safe_numeric(work["fam_size"]).median())
    work["age_ref"] = safe_numeric(work["age_ref"]).fillna(safe_numeric(work["age_ref"]).median())
    work["urban"] = (safe_numeric(work["bls_urbn"]).fillna(1) == 1).astype(float)
    work["log_fam_size"] = np.log(work["fam_size"].clip(lower=1))
    work["region"] = safe_numeric(work["region"]).fillna(1).astype(int)
    work["year"] = safe_numeric(work["year"]).astype(int)

    X = pd.DataFrame(index=work.index)
    for c in categories:
        X[f"logp_{c}"] = work[f"logp_{c}"]
    X["ln_real_exp"] = work["ln_real_exp"]
    X["log_fam_size"] = work["log_fam_size"]
    X["age_ref"] = work["age_ref"]
    X["urban"] = work["urban"]

    year_d = pd.get_dummies(work["year"], prefix="year", drop_first=True, dtype=float)
    region_d = pd.get_dummies(work["region"], prefix="region", drop_first=True, dtype=float)
    X = pd.concat([X, year_d, region_d], axis=1)
    X = X.astype(float)

    w = work[weight_col].to_numpy(dtype=float)
    y_cols = [f"share_{c}" for c in categories]
    n = len(categories)
    gamma = np.zeros((n, n))
    beta = np.zeros(n)

    for i, c in enumerate(categories[:-1]):
        y = work[f"share_{c}"].to_numpy(dtype=float)
        if regularized:
            ridge = Ridge(alpha=5.0, fit_intercept=True)
            ridge.fit(X, y, sample_weight=w)
            coef = pd.Series(ridge.coef_, index=X.columns)
            intercept = ridge.intercept_
        else:
            X_sm = sm.add_constant(X, has_constant="add")
            fit = sm.WLS(y, X_sm, weights=w).fit()
            coef = fit.params.drop("const")
            intercept = float(fit.params["const"])
        _ = intercept
        for j, cj in enumerate(categories):
            gamma[i, j] = float(coef.get(f"logp_{cj}", 0.0))
        beta[i] = float(coef.get("ln_real_exp", 0.0))

    # Adding-up restrictions for the omitted equation.
    gamma[-1, :] = -gamma[:-1, :].sum(axis=0)
    beta[-1] = -beta[:-1].sum()

    # Enforce homogeneity and symmetry by projection.
    g = gamma.copy()
    for _ in range(12):
        g = 0.5 * (g + g.T)
        g = g - g.mean(axis=1, keepdims=True)
        g = g - g.mean(axis=0, keepdims=True)
    gamma = g

    shares = np.array(
        [weighted_mean(work[f"share_{c}"], work[weight_col]) for c in categories],
        dtype=float,
    )
    shares = shares / shares.sum()

    eps = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            delta = 1.0 if i == j else 0.0
            eps[i, j] = (
                -delta
                + gamma[i, j] / shares[i]
                - (beta[i] / shares[i]) * shares[j]
            )

    own = np.diag(eps)
    contrib = shares * own
    weighted_mean_eps = float(np.sum(contrib))

    table = pd.DataFrame(
        {
            "category": categories,
            "share": shares,
            "marshallian_own_elasticity": own,
            "contribution_share_times_elasticity": contrib,
            "beta": beta,
            "gamma_ii": np.diag(gamma),
        }
    )

    # A conservative strength rating based on independent price cells and price variation.
    cell = (
        work["year"].astype(str)
        + "Q"
        + work["quarter"].astype(str)
        + "R"
        + work["region"].astype(str)
    )
    n_cells = cell.nunique()
    median_price_sd = float(np.median([work[f"logp_{c}"].std() for c in categories]))
    if n_cells >= 60 and median_price_sd >= 0.02:
        design_rank = "moderate"
    elif n_cells >= 40 and median_price_sd >= 0.01:
        design_rank = "weak_to_moderate"
    else:
        design_rank = "weak"

    return DemandResult(
        categories=categories,
        shares=shares,
        beta=beta,
        gamma=gamma,
        elasticity_matrix=eps,
        weighted_mean=weighted_mean_eps,
        table=table,
        design_rank=design_rank,
    )


def bootstrap_demand(
    df: pd.DataFrame,
    categories: List[str],
    n_boot: int = 40,
    seed: int = 42,
    regularized: bool = False,
) -> Tuple[np.ndarray, pd.DataFrame]:
    log(f"Bootstrapping demand system ({n_boot} reps).")
    work = df.copy()
    work["cluster"] = (
        work["year"].astype(str)
        + "Q"
        + work["quarter"].astype(str)
        + "R"
        + work["region"].astype(str)
    )
    clusters = work["cluster"].dropna().unique()
    rng = np.random.default_rng(seed)
    means = []
    own_rows = []

    for b in range(n_boot):
        draw = rng.choice(clusters, size=len(clusters), replace=True)
        mult = pd.Series(draw).value_counts()
        boot = work.merge(mult.rename("mult"), left_on="cluster", right_index=True, how="left")
        boot["boot_weight"] = boot["sample_weight"] * boot["mult"].fillna(0.0)
        boot = boot[boot["boot_weight"] > 0].copy()
        est = estimate_demand_system(
            boot,
            categories=categories,
            weight_col="boot_weight",
            regularized=regularized,
        )
        means.append(est.weighted_mean)
        own_rows.append(est.table.set_index("category")["marshallian_own_elasticity"])
        if (b + 1) % 10 == 0:
            log(f"Bootstrap {b + 1}/{n_boot} complete.")

    own_df = pd.DataFrame(own_rows)
    return np.asarray(means, dtype=float), own_df


def parse_bea_table(path: Path, sheet: str = "2017") -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet, header=None)
    first_col = raw.iloc[:, 0].astype(str).str.strip()
    header_idx = first_col[first_col.isin(["IOCode", "Code"])].index[0]
    code_row = raw.iloc[header_idx - 1].tolist()
    data = raw.iloc[header_idx + 1 :].copy()

    cols = []
    for j, c in enumerate(code_row):
        c = "" if pd.isna(c) else str(c).strip()
        if j == 0:
            cols.append("row_code")
        elif j == 1:
            cols.append("row_name")
        else:
            cols.append(c if c else f"col_{j}")
    data.columns = cols
    data["row_code"] = data["row_code"].astype(str).str.strip()
    data["row_name"] = data["row_name"].astype(str).str.strip()
    data = data[data["row_code"].notna() & data["row_code"].ne("")].copy()
    for c in data.columns[2:]:
        s = data[c].astype(str).str.replace(",", "", regex=False).str.strip()
        s = s.replace({"...": np.nan, "nan": np.nan, "": np.nan})
        data[c] = pd.to_numeric(s, errors="coerce")
    return data


def build_io_objects() -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    log("Building IO matrices and sector PCE vector.")
    req = parse_bea_table(DATA_DIR / "TOTAL AND DOMESTIC REQUIREMENTS" / "CxC_Domestic_Sector.xlsx")
    req = req[req["row_code"].isin(IO_CORE_SECTORS)].copy()
    req = req.set_index("row_code")
    L = req[IO_CORE_SECTORS].fillna(0.0)

    use = parse_bea_table(DATA_DIR / "SUPPLY-USE" / "Use_Sector.xlsx")
    use = use[use["row_code"].isin(IO_CORE_SECTORS)].copy()
    use = use.set_index("row_code")
    pce = use["F010"].fillna(0.0)
    sector_names = use["row_name"]
    return L, pce, sector_names


def build_io_mapping(
    categories: List[str], pce: pd.Series, sector_names: pd.Series
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    rows = []
    W = pd.DataFrame(0.0, index=categories, columns=IO_CORE_SECTORS)
    for c in categories:
        candidates = [s for s in IO_CANDIDATE_MAP[c] if s in IO_CORE_SECTORS]
        vals = np.array([max(float(pce.get(s, 0.0)), 0.0) for s in candidates], dtype=float)
        if vals.sum() <= 0:
            vals = np.ones(len(candidates), dtype=float)
        weights = vals / vals.sum()
        for sec, w in zip(candidates, weights):
            W.loc[c, sec] = w
            rows.append(
                {
                    "category": c,
                    "io_code": sec,
                    "io_name": sector_names.get(sec, ""),
                    "mapping_weight": w,
                    "sector_pce_value": float(pce.get(sec, np.nan)),
                }
            )
    mapping_df = pd.DataFrame(rows)
    mapping_df.to_csv(RESULTS_DIR / "io_mapping.csv", index=False)

    sector_share = pce.reindex(IO_CORE_SECTORS).fillna(0.0).to_numpy(dtype=float)
    if sector_share.sum() <= 0:
        sector_share = np.repeat(1.0 / len(sector_share), len(sector_share))
    else:
        sector_share = sector_share / sector_share.sum()
    pce_cat_raw = W.to_numpy() @ sector_share
    pce_cat_share = pce_cat_raw / pce_cat_raw.sum()
    pce_share_df = pd.DataFrame({"category": categories, "pce_inferred_share": pce_cat_share})
    return mapping_df, W, pce_share_df["pce_inferred_share"].to_numpy()


def compute_ge_realized(
    demand: DemandResult,
    L: pd.DataFrame,
    W: pd.DataFrame,
) -> pd.DataFrame:
    log("Computing IO-linked realized elasticities.")
    Lm = L.to_numpy(dtype=float)
    I = np.eye(Lm.shape[0])
    A = I - np.linalg.inv(Lm)
    B = np.linalg.inv(I - A.T)

    E = demand.elasticity_matrix
    shares = demand.shares
    categories = demand.categories
    Wm = W.loc[categories, L.columns].to_numpy(dtype=float)
    rows = []

    for i, c in enumerate(categories):
        v = 0.01 * Wm[i, :]  # 1% category-linked sectoral cost shock
        dps = B @ v
        dpc = Wm @ dps
        dlnq = E @ dpc
        own_price_change = float(dpc[i])
        own_qty_change = float(dlnq[i])
        if abs(own_price_change) < 1e-12:
            realized = np.nan
        else:
            realized = own_qty_change / own_price_change
        rows.append(
            {
                "category": c,
                "share": shares[i],
                "realized_own_elasticity": realized,
                "own_price_change": own_price_change,
                "own_quantity_change": own_qty_change,
                "contribution_share_times_realized_elasticity": shares[i] * realized,
            }
        )
    ge = pd.DataFrame(rows)
    return ge


def run_robustness(
    cex: pd.DataFrame,
    cpi_panel: pd.DataFrame,
    rpp_clean: pd.DataFrame,
    base_demand: DemandResult,
    pce_shares: np.ndarray,
) -> pd.DataFrame:
    log("Running robustness checks.")
    rows = []

    # 1. Baseline 8-category regional
    rows.append(
        {
            "scenario": "baseline_8cat_regional",
            "weighted_mean_marshallian": base_demand.weighted_mean,
            "notes": "Unregularized WLS, regional CPI (with apparel national fallback), no RPP.",
        }
    )

    # 2. Alternative broader grouping (merge education_communication + other_goods_services)
    merged = merge_cex_prices(cex, cpi_panel, price_mode="regional", use_rpp=False, rpp=rpp_clean)
    groups_alt = {
        "food_beverages": ["food_beverages"],
        "housing": ["housing"],
        "apparel": ["apparel"],
        "transportation": ["transportation"],
        "medical_care": ["medical_care"],
        "recreation": ["recreation"],
        "education_other": ["education_communication", "other_goods_services"],
    }
    grouped = apply_grouping(merged, groups_alt)
    alt_cats = list(groups_alt.keys())
    alt_est = estimate_demand_system(grouped, alt_cats, regularized=False)
    rows.append(
        {
            "scenario": "alternative_7cat_grouping",
            "weighted_mean_marshallian": alt_est.weighted_mean,
            "notes": "Merged education/communication with other goods/services.",
        }
    )

    # 3. National-only price variation
    nat_df = merge_cex_prices(cex, cpi_panel, price_mode="national", use_rpp=False, rpp=rpp_clean)
    nat_est = estimate_demand_system(nat_df, BASE_CATEGORIES, regularized=False)
    rows.append(
        {
            "scenario": "national_only_prices",
            "weighted_mean_marshallian": nat_est.weighted_mean,
            "notes": "All households assigned national CPI prices.",
        }
    )

    # 4. Regional + RPP supplemental prices
    rpp_df = merge_cex_prices(cex, cpi_panel, price_mode="regional", use_rpp=True, rpp=rpp_clean)
    rpp_est = estimate_demand_system(rpp_df, BASE_CATEGORIES, regularized=False)
    rows.append(
        {
            "scenario": "regional_plus_rpp",
            "weighted_mean_marshallian": rpp_est.weighted_mean,
            "notes": "Regional CPI plus state-year RPP multipliers.",
        }
    )

    # 5. Regularized estimator
    reg_est = estimate_demand_system(merged, BASE_CATEGORIES, regularized=True)
    rows.append(
        {
            "scenario": "regularized_ridge",
            "weighted_mean_marshallian": reg_est.weighted_mean,
            "notes": "Ridge (alpha=5) share-equation estimation.",
        }
    )

    # 6. Excluding housing
    no_housing_groups = {c: [c] for c in BASE_CATEGORIES if c != "housing"}
    no_housing_df = apply_grouping(merged, no_housing_groups)
    no_housing_cats = list(no_housing_groups.keys())
    no_housing_est = estimate_demand_system(no_housing_df, no_housing_cats, regularized=False)
    rows.append(
        {
            "scenario": "exclude_housing",
            "weighted_mean_marshallian": no_housing_est.weighted_mean,
            "notes": "Demand system re-estimated without housing category.",
        }
    )

    # 7. CEX shares vs inferred PCE-like shares
    own = base_demand.table.set_index("category").loc[BASE_CATEGORIES, "marshallian_own_elasticity"].to_numpy()
    pce_weighted = float(np.sum(pce_shares * own))
    rows.append(
        {
            "scenario": "pce_inferred_shares_weighting",
            "weighted_mean_marshallian": pce_weighted,
            "notes": "Uses inferred PCE-style shares from IO mapping instead of CEX shares.",
        }
    )

    robust = pd.DataFrame(rows)
    robust.to_csv(RESULTS_DIR / "robustness_summary.csv", index=False)
    return robust


def markdown_table(df: pd.DataFrame, float_fmt: str = ".4f") -> str:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].map(lambda x: f"{x:{float_fmt}}" if pd.notna(x) else "")
    headers = "| " + " | ".join(out.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(out.columns)) + " |"
    rows = ["| " + " | ".join(map(str, row)) + " |" for row in out.to_numpy()]
    return "\n".join([headers, sep] + rows)


def render_pdf(markdown_text: str, out_path: Path) -> bool:
    try:
        lines = markdown_text.splitlines()
        line_chunks = []
        chunk = []
        for line in lines:
            wrapped = textwrap.wrap(line, width=110) if line else [""]
            for sub in wrapped:
                chunk.append(sub)
                if len(chunk) >= 52:
                    line_chunks.append(chunk)
                    chunk = []
        if chunk:
            line_chunks.append(chunk)

        from matplotlib.backends.backend_pdf import PdfPages

        with PdfPages(out_path) as pdf:
            for c in line_chunks:
                fig = plt.figure(figsize=(8.5, 11))
                ax = fig.add_axes([0.04, 0.04, 0.92, 0.92])
                ax.axis("off")
                ax.text(
                    0.0,
                    1.0,
                    "\n".join(c),
                    va="top",
                    ha="left",
                    family="monospace",
                    fontsize=8.5,
                )
                pdf.savefig(fig)
                plt.close(fig)
        return True
    except Exception as exc:
        log(f"PDF render failed: {exc}")
        return False


def write_final_report(
    marshallian_table: pd.DataFrame,
    ge_table: pd.DataFrame,
    robust: pd.DataFrame,
    bar_m: float,
    bar_m_ci: Tuple[float, float],
    bar_ge: float,
    final_rank: str,
) -> str:
    top_robust = robust[["scenario", "weighted_mean_marshallian"]].copy()
    md = textwrap.dedent(
        f"""
        # Average Elasticity Estimation Report

        ## Scope
        This report estimates two objects for U.S. consumption categories using only local files in `Demand Elasticity`:
        1. Primary target: share-weighted mean Marshallian own-price elasticity
           \\( \\bar{{\\varepsilon}}^M = \\sum_i s_i \\varepsilon_{{ii}}^M \\)
        2. Secondary target: IO-linked realized own-price elasticity approximation
           \\( \\bar{{\\varepsilon}}^{{GE}} = \\sum_i s_i \\tilde{{\\varepsilon}}_{{ii}} \\)

        ## What Was Estimable
        - **Estimable directly**: broad CEX category expenditures, CPI broad-category price indices, and BEA sector IO requirements.
        - **Not fully identifiable**: a full structural GE/CGE model and exact paper-specific implementations (Jorgenson-Slesnick / Shojaeddini / Döpper / Inforum-LIFT) from local files alone.
        - **Implemented closest defensible approximation**:
          - LA/AIDS-style broad demand system with adding-up and post-estimation homogeneity/symmetry projection.
          - IO-linked propagation using BEA domestic requirements matrix and sector-to-category mapping.

        ## Category Definitions
        See `results/category_crosswalk.csv` for exact mappings and assumptions.

        ## Marshallian Demand Estimation
        Estimated share equations:
        \\[
        w_i = \\alpha_i + \\sum_j \\gamma_{{ij}} \\ln p_j + \\beta_i \\ln\\left(\\frac{{x}}{{P}}\\right) + Z_i'\\delta + u_i
        \\]
        with Stone index \\(\\ln P = \\sum_k w_k \\ln p_k\\), estimated by weighted equation-by-equation WLS (robustness: ridge regularization).

        Elasticities at weighted mean shares:
        \\[
        \\varepsilon_{{ij}}^M = -\\mathbf{{1}}(i=j) + \\frac{{\\gamma_{{ij}}}}{{w_i}} - \\frac{{\\beta_i}}{{w_i}} w_j
        \\]

        Preferred estimate:
        - **\\(\\bar{{\\varepsilon}}^M = {bar_m:.4f}\\)** (bootstrap 95% CI: [{bar_m_ci[0]:.4f}, {bar_m_ci[1]:.4f}])
        - Identification quality (conservative rank): **{final_rank}**

        Marshallian own elasticities:
        {markdown_table(marshallian_table[["category", "share", "marshallian_own_elasticity", "contribution_share_times_elasticity", "ci_lower_95", "ci_upper_95"]])}

        ## IO-Linked Realized Elasticity Approximation
        Construction:
        1. Build sector requirement matrix \\(L\\) from `CxC_Domestic_Sector.xlsx` (2017 sector table).
        2. Recover direct-requirement analogue \\(A = I - L^{{-1}}\\).
        3. Propagate cost shocks via \\((I-A')^{{-1}}\\).
        4. Map sector price changes to consumption categories.
        5. Map induced category price vector into quantity changes using estimated Marshallian matrix.
        6. Define realized own elasticity for each category:
           \\[
           \\tilde{{\\varepsilon}}_{{ii}} = \\frac{{\\Delta \\ln Q_i}}{{\\Delta \\ln P_i}}
           \\]

        Preferred approximate estimate:
        - **\\(\\bar{{\\varepsilon}}^{{GE}} = {bar_ge:.4f}\\)** (IO-linked approximation, not a fully identified full-GE object)

        Realized own elasticities:
        {markdown_table(ge_table[["category", "share", "realized_own_elasticity", "contribution_share_times_realized_elasticity"]])}

        ## Robustness Summary
        {markdown_table(top_robust)}

        ## Limitations
        - Public CEX geography and aggregate-category construction limit clean causal identification.
        - Education/communication and other-goods/services mappings are approximate at this data granularity.
        - Apparel lacks regional CPI in provided broad files; national fallback is used.
        - GE object is an IO-linked propagation approximation, not an estimated structural CGE equilibrium.
        """
    ).strip()
    md = "\n".join(line.lstrip() for line in md.splitlines())

    (RESULTS_DIR / "final_report.md").write_text(md + "\n", encoding="utf-8")
    return md


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    log("Starting full elasticity pipeline.")

    _ = create_file_inventory()
    write_data_notes()
    _ = build_category_crosswalk()

    cex = process_cex()
    cpi_panel, _ = process_cpi()
    rpp_clean = process_rpp()

    baseline_df = merge_cex_prices(cex, cpi_panel, price_mode="regional", use_rpp=False, rpp=rpp_clean)
    baseline_df.to_parquet(RESULTS_DIR / "demand_estimation_panel.parquet", index=False)
    baseline_demand = estimate_demand_system(baseline_df, BASE_CATEGORIES, regularized=False)

    boot_means, boot_own = bootstrap_demand(
        baseline_df,
        BASE_CATEGORIES,
        n_boot=40,
        seed=20260314,
        regularized=False,
    )
    ci_low = float(np.nanpercentile(boot_means, 2.5))
    ci_high = float(np.nanpercentile(boot_means, 97.5))
    final_rank = baseline_demand.design_rank
    if (ci_low < 0 < ci_high) or ((ci_high - ci_low) > 1.5):
        final_rank = "weak"

    mar = baseline_demand.table.copy()
    mar["ci_lower_95"] = mar["category"].map(boot_own.quantile(0.025).to_dict())
    mar["ci_upper_95"] = mar["category"].map(boot_own.quantile(0.975).to_dict())
    mar.to_csv(RESULTS_DIR / "marshallian_elasticities.csv", index=False)
    (RESULTS_DIR / "marshallian_weighted_mean.txt").write_text(
        (
            f"weighted_mean_marshallian={baseline_demand.weighted_mean:.6f}\n"
            f"bootstrap_ci_95=[{ci_low:.6f},{ci_high:.6f}]\n"
            f"identification_rank={final_rank}\n"
        ),
        encoding="utf-8",
    )

    L, pce, sector_names = build_io_objects()
    L.to_csv(RESULTS_DIR / "io_domestic_requirements_sector_2017.csv")
    _, W, pce_shares = build_io_mapping(BASE_CATEGORIES, pce, sector_names)
    ge = compute_ge_realized(baseline_demand, L, W)
    bar_ge = float(ge["contribution_share_times_realized_elasticity"].sum())
    ge.to_csv(RESULTS_DIR / "ge_elasticities.csv", index=False)
    (RESULTS_DIR / "ge_weighted_mean.txt").write_text(
        f"weighted_mean_ge_approx={bar_ge:.6f}\n",
        encoding="utf-8",
    )

    robust = run_robustness(cex, cpi_panel, rpp_clean, baseline_demand, pce_shares)

    summary = pd.DataFrame(
        [
            {
                "metric": "weighted_mean_marshallian",
                "estimate": baseline_demand.weighted_mean,
                "ci_lower_95": ci_low,
                "ci_upper_95": ci_high,
                "identification_rank": final_rank,
                "object_status": "estimated_from_local_data",
            },
            {
                "metric": "weighted_mean_realized_ge_approx",
                "estimate": bar_ge,
                "ci_lower_95": np.nan,
                "ci_upper_95": np.nan,
                "identification_rank": "approximation",
                "object_status": "io_linked_approximation",
            },
        ]
    )
    summary.to_csv(RESULTS_DIR / "final_summary.csv", index=False)

    report_md = write_final_report(
        marshallian_table=mar,
        ge_table=ge,
        robust=robust,
        bar_m=baseline_demand.weighted_mean,
        bar_m_ci=(ci_low, ci_high),
        bar_ge=bar_ge,
        final_rank=final_rank,
    )
    pdf_ok = render_pdf(report_md, RESULTS_DIR / "final_report.pdf")
    if pdf_ok:
        log("Rendered final_report.pdf.")
    else:
        log("Could not render final_report.pdf.")

    log("Pipeline completed.")


if __name__ == "__main__":
    main()
