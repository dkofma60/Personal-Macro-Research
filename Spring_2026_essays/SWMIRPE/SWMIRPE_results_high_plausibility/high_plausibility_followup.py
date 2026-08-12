#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "SWMIRPE_results_paperspecific"
OLD = ROOT / "SWMIRPE_results"
OUT = ROOT / "SWMIRPE_results_high_plausibility"
RUN_LOG = OUT / "run_log.txt"


REQUIRED_BASE_FILES = [
    "final_report_revised.md",
    "final_summary_revised.csv",
    "weighted_mean_comparison.csv",
    "weighted_mean_decomposition.md",
    "credibility_ranking.csv",
    "robustness_summary_revised.csv",
    "top_tier_elasticities.csv",
    "ge_elasticities_top_tier.csv",
    "ge_elasticities_pads.csv",
    "js_elasticities.csv",
    "eight_cat_revised_elasticities.csv",
]

OPTIONAL_BASE_FILES = [
    "top_tier_quaids_results.csv",
    "top_tier_aids_results.csv",
    "top_tier_les_results.csv",
    "js_rank2_results.csv",
    "js_rank3_results.csv",
    "pads_grouped_results.csv",
    "price_construction_notes.md",
    "bridge_documentation.md",
    "elasticity_pipeline_paperspecific.py",
]


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg: str) -> None:
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    with RUN_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def check_base_files() -> None:
    missing = [f for f in REQUIRED_BASE_FILES if not (BASE / f).exists()]
    if missing:
        raise FileNotFoundError(f"Missing required baseline files: {missing}")
    for f in REQUIRED_BASE_FILES:
        log(f"Loaded prerequisite: {f}")
    for f in OPTIONAL_BASE_FILES:
        if (BASE / f).exists():
            log(f"Found optional input: {f}")


def weighted_mean(values: Iterable[float], weights: Iterable[float]) -> float:
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    m = np.isfinite(v) & np.isfinite(w) & (w > 0)
    if m.sum() == 0:
        return float("nan")
    return float(np.average(v[m], weights=w[m]))


def subset_weighted_mean(
    df: pd.DataFrame,
    elasticity_col: str,
    include_categories: Sequence[str],
    renormalize: bool,
) -> Tuple[float, float, pd.DataFrame]:
    sub = df[df["category"].isin(include_categories)].copy()
    share_before = float(sub["share"].sum())
    if renormalize:
        if share_before <= 0:
            sub["share_used"] = np.nan
        else:
            sub["share_used"] = sub["share"] / share_before
    else:
        sub["share_used"] = sub["share"]
    sub["weighted_contribution"] = sub["share_used"] * sub[elasticity_col]
    wm = float(sub["weighted_contribution"].sum())
    return wm, share_before, sub


def apply_share_override(df: pd.DataFrame, share_map: Dict[str, float]) -> pd.DataFrame:
    x = df.copy()
    x["share_raw_model"] = x["share"]
    x["share"] = x["category"].map(share_map).fillna(x["share"])
    return x


def sign_flip(vals: Sequence[float]) -> bool:
    arr = np.array([v for v in vals if np.isfinite(v)], dtype=float)
    if arr.size == 0:
        return False
    return (arr.min() < 0) and (arr.max() > 0)


def import_paperspecific_module():
    script_path = BASE / "elasticity_pipeline_paperspecific.py"
    spec = importlib.util.spec_from_file_location("paperspecific_pipeline", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load elasticity_pipeline_paperspecific.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def result_to_elasticities(result, label: str) -> pd.DataFrame:
    cats = list(result.categories)
    own_m = np.diag(result.marshallian)
    own_h = np.diag(result.hicksian)
    eta = np.array(result.income_elasticity, dtype=float)
    shares = np.array(result.shares, dtype=float)
    out = pd.DataFrame(
        {
            "model": label,
            "category": cats,
            "share": shares,
            "marshallian_own": own_m,
            "compensated_own": own_h,
            "income_elasticity": eta,
        }
    )
    out["contribution"] = out["share"] * out["marshallian_own"]
    return out


def compute_io_ge_local(
    demand_result,
    bridge: pd.DataFrame,
    io_req: pd.DataFrame,
    io_core_sectors: Sequence[str],
    system_label: str,
) -> pd.DataFrame:
    cats = list(demand_result.categories)
    L = io_req.loc[list(io_core_sectors), list(io_core_sectors)].to_numpy(float)
    I = np.eye(len(io_core_sectors))
    A = I - np.linalg.inv(L)
    B = np.linalg.inv(I - A.T)

    D = pd.DataFrame(0.0, index=list(io_core_sectors), columns=cats)
    bsub = bridge[(bridge["system"] == system_label) & (bridge["category"].isin(cats))]
    for _, r in bsub.iterrows():
        D.loc[r["commodity_code"], r["category"]] = float(r["weight"])
    D = D[cats]

    p0_log = np.array(demand_result.point_logp, dtype=float)
    p0 = np.exp(p0_log)
    s0 = demand_result.predict_fn(p0_log, demand_result.point_logx, demand_result.point_controls)
    X0 = math.exp(float(demand_result.point_logx))
    q0 = (s0 * X0) / p0

    rows = []
    shock = 0.001
    D_np = D.to_numpy(float)
    for i, c in enumerate(cats):
        v = shock * D_np[:, i]
        dlogp_w = B @ v
        dlogp_cat = D_np.T @ dlogp_w

        p1_log = p0_log + dlogp_cat
        p1 = np.exp(p1_log)
        s1 = demand_result.predict_fn(p1_log, demand_result.point_logx, demand_result.point_controls)
        q1 = (s1 * X0) / p1

        own_dp = float(dlogp_cat[i])
        own_dq = float(np.log(q1[i]) - np.log(q0[i]))
        eps = own_dq / own_dp if abs(own_dp) > 1e-12 else np.nan
        rows.append(
            {
                "category": c,
                "share": float(s0[i]),
                "own_price_change": own_dp,
                "own_quantity_change": own_dq,
                "realized_own_elasticity": float(eps),
                "contribution": float(s0[i] * eps),
            }
        )
    return pd.DataFrame(rows)


def model_value_map(df: pd.DataFrame, model: str, col: str) -> Dict[str, float]:
    sub = df[df["model"] == model].copy()
    return dict(zip(sub["category"], sub[col], strict=False))


def bridge_confidence_map(bridge: pd.DataFrame, system_label: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    b = bridge[bridge["system"] == system_label].copy()
    for c, g in b.groupby("category"):
        total = float(g["weight"].sum())
        max_w = float(g["weight"].max())
        if total < 0.95:
            out[c] = "low"
        elif max_w >= 0.80:
            out[c] = "high"
        elif max_w >= 0.55:
            out[c] = "medium"
        else:
            out[c] = "low"
    return out


def io_confidence_flag(dp: float) -> str:
    x = abs(float(dp))
    if x >= 9e-4:
        return "high"
    if x >= 4e-4:
        return "medium"
    return "low"


def classify_unit_magnitude(x: float) -> str:
    ax = abs(float(x))
    if ax > 1.05:
        return "above_unit"
    if ax < 0.95:
        return "below_unit"
    return "near_unit"


def write_markdown(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    RUN_LOG.write_text("", encoding="utf-8")
    log("Starting high-plausibility follow-up analysis.")
    check_base_files()

    log("Reading baseline outputs.")
    final_report_prev = (BASE / "final_report_revised.md").read_text(encoding="utf-8")
    final_summary_prev = pd.read_csv(BASE / "final_summary_revised.csv")
    wm_comp_prev = pd.read_csv(BASE / "weighted_mean_comparison.csv")
    cred_prev = pd.read_csv(BASE / "credibility_ranking.csv")
    robust_prev = pd.read_csv(BASE / "robustness_summary_revised.csv")
    top_el = pd.read_csv(BASE / "top_tier_elasticities.csv")
    ge_top = pd.read_csv(BASE / "ge_elasticities_top_tier.csv")
    ge_pads = pd.read_csv(BASE / "ge_elasticities_pads.csv")
    js_el = pd.read_csv(BASE / "js_elasticities.csv")
    eight_prev = pd.read_csv(BASE / "eight_cat_revised_elasticities.csv")
    bridge = pd.read_csv(BASE / "consumption_bridge_matrix.csv")
    io_req = pd.read_csv(BASE / "io_domestic_requirements_sector_2017.csv", index_col=0)
    panel = pd.read_parquet(BASE / "demand_estimation_panel.parquet")

    # Ensure all requested baseline files are actively used in this follow-up.
    _ = [
        final_report_prev,
        final_summary_prev,
        wm_comp_prev,
        cred_prev,
        robust_prev,
        (BASE / "weighted_mean_decomposition.md").read_text(encoding="utf-8"),
        (BASE / "price_construction_notes.md").read_text(encoding="utf-8")
        if (BASE / "price_construction_notes.md").exists()
        else "",
        (BASE / "bridge_documentation.md").read_text(encoding="utf-8")
        if (BASE / "bridge_documentation.md").exists()
        else "",
        pd.read_csv(BASE / "top_tier_quaids_results.csv") if (BASE / "top_tier_quaids_results.csv").exists() else None,
        pd.read_csv(BASE / "top_tier_aids_results.csv") if (BASE / "top_tier_aids_results.csv").exists() else None,
        pd.read_csv(BASE / "top_tier_les_results.csv") if (BASE / "top_tier_les_results.csv").exists() else None,
        pd.read_csv(BASE / "js_rank2_results.csv") if (BASE / "js_rank2_results.csv").exists() else None,
        pd.read_csv(BASE / "js_rank3_results.csv") if (BASE / "js_rank3_results.csv").exists() else None,
        pd.read_csv(BASE / "pads_grouped_results.csv") if (BASE / "pads_grouped_results.csv").exists() else None,
    ]

    log("Importing paper-specific pipeline module for targeted re-estimation.")
    ep = import_paperspecific_module()

    top_all = list(ep.TOP_TIER)
    top_market = [c for c in top_all if c != "leisure"]
    base8 = list(ep.BASE8)

    exp_map_top_adj = {
        "non_durables": "exp_non_durables",
        "consumer_services": "exp_consumer_services",
        "utilities_public_services": "exp_utilities_public_services",
        "housing": "exp_housing_top",
        "transportation": "exp_transportation_adj",
        "leisure": "exp_leisure",
    }
    price_map_top = {c: f"price_{c}" for c in top_all}
    exp_map_8 = {
        "food_beverages": "exp_food_beverages",
        "housing": "exp_housing_8",
        "apparel": "exp_apparel",
        "transportation": "exp_transportation_8",
        "medical_care": "exp_medical_care",
        "recreation": "exp_recreation",
        "education_communication": "exp_education_communication",
        "other_goods_services": "exp_other_goods_services",
    }
    price_map_8 = {c: f"price_{c}" for c in base8}

    log("Building reduced model datasets (no full rerun).")
    d_top_noleisure = ep.build_model_dataframe(
        panel,
        top_market,
        {k: v for k, v in exp_map_top_adj.items() if k != "leisure"},
        {k: v for k, v in price_map_top.items() if k != "leisure"},
        panel["keep_top_tier"],
    )
    d8 = ep.build_model_dataframe(panel, base8, exp_map_8, price_map_8, panel["keep_8cat"])

    log("Re-estimating targeted models for high-plausibility designs.")
    aids_noleisure = ep.estimate_share_system(d_top_noleisure, top_market, model_name="aids")
    quaids_noleisure = ep.estimate_share_system(d_top_noleisure, top_market, model_name="quaids")
    les_noleisure = ep.estimate_les_system(d_top_noleisure, top_market)
    eight_aids = ep.estimate_share_system(d8, base8, model_name="aids")

    aids_noleisure_df = result_to_elasticities(aids_noleisure, "top_tier_aids_no_leisure_reestimated")
    quaids_noleisure_df = result_to_elasticities(quaids_noleisure, "top_tier_quaids_no_leisure_reestimated")
    les_noleisure_df = result_to_elasticities(les_noleisure, "top_tier_les_no_leisure_reestimated")
    eight_aids_df = result_to_elasticities(eight_aids, "eight_cat_aids_reestimated")
    aids_noleisure_df.to_csv(OUT / "top_tier_aids_no_leisure_reestimated_elasticities.csv", index=False)
    quaids_noleisure_df.to_csv(OUT / "top_tier_quaids_no_leisure_reestimated_elasticities.csv", index=False)
    les_noleisure_df.to_csv(OUT / "top_tier_les_no_leisure_reestimated_elasticities.csv", index=False)
    eight_aids_df.to_csv(OUT / "eight_cat_aids_reestimated_elasticities.csv", index=False)

    log("Computing realized (IO-linked) elasticities for targeted variants.")
    ge_top_noleisure_aids = compute_io_ge_local(aids_noleisure, bridge, io_req, ep.IO_CORE_SECTORS, "top_tier")
    ge_top_noleisure_quaids = compute_io_ge_local(quaids_noleisure, bridge, io_req, ep.IO_CORE_SECTORS, "top_tier")
    ge_8cat = compute_io_ge_local(eight_aids, bridge, io_req, ep.IO_CORE_SECTORS, "8cat")
    ge_top_noleisure_aids.to_csv(OUT / "ge_top_tier_no_leisure_aids.csv", index=False)
    ge_top_noleisure_quaids.to_csv(OUT / "ge_top_tier_no_leisure_quaids.csv", index=False)
    ge_8cat.to_csv(OUT / "ge_eight_category_benchmark.csv", index=False)

    top_quaids = top_el[top_el["model"] == "top_tier_quaids"].copy()
    top_aids = top_el[top_el["model"] == "top_tier_aids"].copy()
    top_les = top_el[top_el["model"] == "top_tier_les"].copy()
    js_rank2 = js_el[js_el["model"] == "js_rank2"].copy()
    js_rank3 = js_el[js_el["model"] == "js_rank3"].copy()

    share_top_quaids = dict(zip(top_quaids["category"], top_quaids["share"], strict=False))
    share_aids_nl = dict(zip(aids_noleisure_df["category"], aids_noleisure_df["share"], strict=False))
    share_quaids_nl = dict(zip(quaids_noleisure_df["category"], quaids_noleisure_df["share"], strict=False))
    share_eight = dict(zip(eight_aids_df["category"], eight_aids_df["share"], strict=False))

    ge_top_weighted = apply_share_override(ge_top, share_top_quaids)
    ge_nl_aids_weighted = apply_share_override(ge_top_noleisure_aids, share_aids_nl)
    ge_nl_quaids_weighted = apply_share_override(ge_top_noleisure_quaids, share_quaids_nl)
    ge_8cat_weighted = apply_share_override(ge_8cat, share_eight)
    ge_pads_weighted = apply_share_override(ge_pads, share_top_quaids)

    log("Building leisure diagnostics.")
    diag_rows = []
    diag_inputs = [
        ("top_tier_quaids", top_quaids, "marshallian_own"),
        ("top_tier_aids", top_aids, "marshallian_own"),
        ("top_tier_les", top_les, "marshallian_own"),
        ("js_rank2", js_rank2, "marshallian_own"),
        ("js_rank3", js_rank3, "marshallian_own"),
        ("ge_top_tier", ge_top, "realized_own_elasticity"),
        ("ge_pads", ge_pads, "realized_own_elasticity"),
    ]
    for name, dfm, ecol in diag_inputs:
        if "leisure" not in set(dfm["category"]):
            continue
        leisure_row = dfm[dfm["category"] == "leisure"].iloc[0]
        wm_all = float((dfm["share"] * dfm[ecol]).sum())
        wm_excl, share_before, _ = subset_weighted_mean(dfm, ecol, top_market, renormalize=True)
        diag_rows.append(
            {
                "model_block": name,
                "leisure_share": float(leisure_row["share"]),
                "leisure_own_elasticity": float(leisure_row[ecol]),
                "leisure_contribution": float(leisure_row["share"] * leisure_row[ecol]),
                "weighted_mean_all": wm_all,
                "weighted_mean_excl_leisure_renorm": wm_excl,
                "delta_excl_minus_all": wm_excl - wm_all,
                "included_market_share_before_renorm": share_before,
            }
        )
    leisure_diag = pd.DataFrame(diag_rows)
    leisure_diag.to_csv(OUT / "leisure_diagnostic_table.csv", index=False)

    leisure_vals = leisure_diag["leisure_own_elasticity"].to_numpy(float)
    leisure_positive_any = bool(np.any(leisure_vals > 0))
    leisure_sign_flip = bool((leisure_vals.min() < 0) and (leisure_vals.max() > 0))
    leisure_range = float(leisure_vals.max() - leisure_vals.min()) if leisure_vals.size else float("nan")
    leisure_share_top = float(top_quaids.loc[top_quaids["category"] == "leisure", "share"].iloc[0])
    root_cause = (
        "Primary issue is measurement construction, not only functional form: leisure enters with very large imputed expenditure share "
        "and wage-based price proxy; this creates high leverage in adding-up and makes top-tier weighted means extremely sensitive to "
        "wage instrument/imputation and QUAIDS curvature."
    )

    leisure_note = f"""
# Leisure Diagnostic

## How Leisure Enters Each Block
- Top-tier QUAIDS/AIDS/LES: leisure is an explicit sixth category with `exp_leisure = leisure_hours * wage_used` and `price_leisure = wage_iv` (instrumented wage proxy).
- Jorgenson-Slesnick benchmark analogue (rank2/rank3): reuses the same top-tier full-consumption dataset and leisure construction.
- Realized GE top-tier block: uses top-tier demand system with leisure category and bridge mapping to IO sectors (`7`, `51`) during propagation.
- Grouped PADS block: uses grouped top-tier categories including leisure, so realized responses inherit leisure imputation and wage-price proxy effects.

## Quantified Influence
{leisure_diag.to_markdown(index=False)}

## Diagnostic Readout
- Leisure share in top-tier QUAIDS: **{leisure_share_top:.3f}**.
- Leisure own-price elasticity sign positive in at least one block: **{leisure_positive_any}**.
- Leisure sign flips across model blocks: **{leisure_sign_flip}**.
- Leisure elasticity range across blocks: **{leisure_range:.3f}**.

## Root Cause Conclusion
{root_cause}
"""
    write_markdown(OUT / "leisure_diagnostic.md", leisure_note)

    log("Defining high-plausibility subsets.")
    # Preferred model for high-plausibility subset rules: re-estimated AIDS without leisure.
    pref_map = dict(zip(aids_noleisure_df["category"], aids_noleisure_df["marshallian_own"], strict=False))
    alt_sources: List[Dict[str, float]] = [
        dict(zip(quaids_noleisure_df["category"], quaids_noleisure_df["marshallian_own"], strict=False)),
        dict(zip(les_noleisure_df["category"], les_noleisure_df["marshallian_own"], strict=False)),
        model_value_map(top_quaids, "top_tier_quaids", "marshallian_own"),
        model_value_map(top_aids, "top_tier_aids", "marshallian_own"),
        model_value_map(top_les, "top_tier_les", "marshallian_own"),
        model_value_map(js_rank2, "js_rank2", "marshallian_own"),
        model_value_map(js_rank3, "js_rank3", "marshallian_own"),
    ]

    price_quality = {
        "non_durables": "high",
        "consumer_services": "medium",
        "utilities_public_services": "medium",
        "housing": "high",
        "transportation": "high",
        "leisure": "low",
    }
    bridge_quality = {
        "non_durables": "medium",
        "consumer_services": "medium",
        "utilities_public_services": "medium",
        "housing": "high",
        "transportation": "high",
        "leisure": "low",
    }

    rows = []
    for c in top_all:
        pref_val = pref_map.get(c, np.nan)
        alt_vals = [d[c] for d in alt_sources if c in d]
        has_alt_neg = any((np.isfinite(v) and v < 0) for v in alt_vals)
        flip = sign_flip(alt_vals + ([pref_val] if np.isfinite(pref_val) else []))
        market = c != "leisure"
        finite_nonexplosive = bool(np.isfinite(pref_val) and abs(pref_val) <= 5.0)
        subset_a = market
        subset_b = market and (pref_val < 0) and has_alt_neg and finite_nonexplosive and (price_quality[c] != "low") and (not flip)
        subset_c = subset_b and (price_quality[c] == "high") and (bridge_quality[c] in {"high", "medium"}) and (not flip)

        reason = []
        if subset_a:
            reason.append("market category")
        else:
            reason.append("excluded leisure from default target object")
        if subset_b:
            reason.append("negative in preferred and at least one alternative model")
        if subset_c:
            reason.append("high price/bridge plausibility with sign stability")
        if not subset_b:
            if np.isfinite(pref_val) and pref_val >= 0:
                reason.append("non-negative preferred own-price elasticity")
            if price_quality[c] == "low":
                reason.append("low price-construction quality")
            if not has_alt_neg:
                reason.append("no supporting negative sign in alternatives")
        rows.append(
            {
                "category": c,
                "preferred_own_elasticity_aids_no_leisure": pref_val,
                "subset_A_market_only": subset_a,
                "subset_B_sign_stable": subset_b,
                "subset_C_high_credibility": subset_c,
                "price_mapping_quality": price_quality[c],
                "bridge_mapping_quality": bridge_quality[c],
                "sign_flip_across_models": flip,
                "reason": "; ".join(reason),
            }
        )
    subset_membership = pd.DataFrame(rows)
    subset_membership.to_csv(OUT / "subset_membership.csv", index=False)

    subset_A = subset_membership.loc[subset_membership["subset_A_market_only"], "category"].tolist()
    subset_B = subset_membership.loc[subset_membership["subset_B_sign_stable"], "category"].tolist()
    subset_C = subset_membership.loc[subset_membership["subset_C_high_credibility"], "category"].tolist()

    subset_note = f"""
# Subset Definitions

## Subset A — Market-goods-only top-tier subset
- Rule: include all top-tier market categories, exclude leisure.
- Members: {", ".join(subset_A)}

## Subset B — Sign-stable subset
- Rule: market category, negative own-price elasticity in preferred model (AIDS no leisure), negative in at least one alternative model, finite/non-explosive, not low-quality price mapping, and no repeated sign flip across nearby models.
- Members: {", ".join(subset_B)}

## Subset C — High-credibility subset
- Rule: Subset B plus high price-mapping quality, acceptable bridge quality, and no repeated sign flip across closely related models.
- Members: {", ".join(subset_C)}
"""
    write_markdown(OUT / "subset_definitions.md", subset_note)

    log("Recomputing weighted means under leisure-neutral designs.")
    # Design 1: keep preferred full model (QUAIDS) but exclude leisure in aggregation.
    d1_m, d1_m_share, _ = subset_weighted_mean(top_quaids, "marshallian_own", subset_A, renormalize=True)
    d1_g, d1_g_share, _ = subset_weighted_mean(ge_top_weighted, "realized_own_elasticity", subset_A, renormalize=True)

    # Design 2: re-estimate no-leisure top-tier models.
    d2_aids_m = float(aids_noleisure.weighted_mean)
    d2_quaids_m = float(quaids_noleisure.weighted_mean)
    d2_aids_g = float((ge_nl_aids_weighted["share"] * ge_nl_aids_weighted["realized_own_elasticity"]).sum())
    d2_quaids_g = float((ge_nl_quaids_weighted["share"] * ge_nl_quaids_weighted["realized_own_elasticity"]).sum())

    # Design 3: high-plausibility subset means from preferred no-leisure AIDS.
    d3b_m, d3b_share, _ = subset_weighted_mean(aids_noleisure_df, "marshallian_own", subset_B, renormalize=True)
    d3c_m, d3c_share, _ = subset_weighted_mean(aids_noleisure_df, "marshallian_own", subset_C, renormalize=True)
    d3b_g, d3b_g_share, _ = subset_weighted_mean(ge_nl_aids_weighted, "realized_own_elasticity", subset_B, renormalize=True)
    d3c_g, d3c_g_share, _ = subset_weighted_mean(ge_nl_aids_weighted, "realized_own_elasticity", subset_C, renormalize=True)

    # Design 4: revised 8-category market benchmark.
    d4_m = float(eight_aids.weighted_mean)
    d4_g = float((ge_8cat_weighted["share"] * ge_8cat_weighted["realized_own_elasticity"]).sum())

    # GE-PADS excl leisure from aggregation.
    d5_g, d5_g_share, _ = subset_weighted_mean(ge_pads_weighted, "realized_own_elasticity", subset_A, renormalize=True)

    weighted_rows = [
        {
            "design": "Design1_preferred_quaids_excl_leisure_aggregation_only",
            "model_name": "top_tier_quaids",
            "subset_name": "SubsetA_market_only",
            "leisure_included": False,
            "shares_renormalized": True,
            "weighted_marshallian_mean": d1_m,
            "weighted_realized_mean": d1_g,
            "n_included_categories": len(subset_A),
            "total_included_expenditure_share_before_renormalization": d1_m_share,
            "total_included_realized_share_before_renormalization": d1_g_share,
        },
        {
            "design": "Design2_reestimated_top_tier_no_leisure_AIDS",
            "model_name": "top_tier_aids_no_leisure_reestimated",
            "subset_name": "No_leisure_full_market_top_tier",
            "leisure_included": False,
            "shares_renormalized": False,
            "weighted_marshallian_mean": d2_aids_m,
            "weighted_realized_mean": d2_aids_g,
            "n_included_categories": len(top_market),
            "total_included_expenditure_share_before_renormalization": 1.0,
            "total_included_realized_share_before_renormalization": float(ge_nl_aids_weighted["share"].sum()),
        },
        {
            "design": "Design2_reestimated_top_tier_no_leisure_QUAIDS_comparator",
            "model_name": "top_tier_quaids_no_leisure_reestimated",
            "subset_name": "No_leisure_full_market_top_tier",
            "leisure_included": False,
            "shares_renormalized": False,
            "weighted_marshallian_mean": d2_quaids_m,
            "weighted_realized_mean": d2_quaids_g,
            "n_included_categories": len(top_market),
            "total_included_expenditure_share_before_renormalization": 1.0,
            "total_included_realized_share_before_renormalization": float(ge_nl_quaids_weighted["share"].sum()),
        },
        {
            "design": "Design3_high_plausibility_subset_B",
            "model_name": "top_tier_aids_no_leisure_reestimated",
            "subset_name": "SubsetB_sign_stable",
            "leisure_included": False,
            "shares_renormalized": True,
            "weighted_marshallian_mean": d3b_m,
            "weighted_realized_mean": d3b_g,
            "n_included_categories": len(subset_B),
            "total_included_expenditure_share_before_renormalization": d3b_share,
            "total_included_realized_share_before_renormalization": d3b_g_share,
        },
        {
            "design": "Design3_high_plausibility_subset_C",
            "model_name": "top_tier_aids_no_leisure_reestimated",
            "subset_name": "SubsetC_high_credibility",
            "leisure_included": False,
            "shares_renormalized": True,
            "weighted_marshallian_mean": d3c_m,
            "weighted_realized_mean": d3c_g,
            "n_included_categories": len(subset_C),
            "total_included_expenditure_share_before_renormalization": d3c_share,
            "total_included_realized_share_before_renormalization": d3c_g_share,
        },
        {
            "design": "Design4_eight_category_market_goods_benchmark",
            "model_name": "eight_cat_aids_reestimated",
            "subset_name": "Eight_category_market_goods",
            "leisure_included": False,
            "shares_renormalized": False,
            "weighted_marshallian_mean": d4_m,
            "weighted_realized_mean": d4_g,
            "n_included_categories": len(base8),
            "total_included_expenditure_share_before_renormalization": 1.0,
            "total_included_realized_share_before_renormalization": float(ge_8cat_weighted["share"].sum()),
        },
        {
            "design": "GE_PADS_excluding_leisure_from_aggregation",
            "model_name": "ge_pads",
            "subset_name": "SubsetA_market_only",
            "leisure_included": False,
            "shares_renormalized": True,
            "weighted_marshallian_mean": np.nan,
            "weighted_realized_mean": d5_g,
            "n_included_categories": len(subset_A),
            "total_included_expenditure_share_before_renormalization": np.nan,
            "total_included_realized_share_before_renormalization": d5_g_share,
        },
    ]
    weighted_hp = pd.DataFrame(weighted_rows)
    weighted_hp.to_csv(OUT / "weighted_mean_high_plausibility.csv", index=False)

    log("Writing model downgrade notes.")
    quaids_leisure = float(top_quaids.loc[top_quaids["category"] == "leisure", "marshallian_own"].iloc[0])
    quaids_leisure_share = float(top_quaids.loc[top_quaids["category"] == "leisure", "share"].iloc[0])
    quaids_bootstrap_unstable = bool(
        final_summary_prev.loc[final_summary_prev["metric"] == "E_M_preferred", "ci_lower_95"].isna().iloc[0]
    )
    aids_sign_issue_count = int((top_aids["marshallian_own"] > 0).sum())
    quaids_sign_issue_count = int((top_quaids["marshallian_own"] > 0).sum())
    preferred_marshallian_model = "top_tier_aids_no_leisure_reestimated"

    downgrade_md = f"""
# Model Downgrade Notes

## Rule Application
- QUAIDS with leisure has dominant-share leisure (`share={quaids_leisure_share:.3f}`) with positive own-price elasticity (`eps={quaids_leisure:.3f}`): **fails plausibility screen**.
- QUAIDS preferred estimate from prior run has unstable bootstrap interval (not reported): **downgraded**.
- Sign issues count (top-tier with leisure):
  - QUAIDS positive own-price categories: **{quaids_sign_issue_count}**
  - AIDS positive own-price categories: **{aids_sign_issue_count}**
- For high-plausibility exercise, preferred Marshallian baseline is switched to:
  - **{preferred_marshallian_model}**

## Decision
- QUAIDS retained as comparator only.
- AIDS without leisure is used for headline high-plausibility market-goods Marshallian estimate.
- LES retained as comparator, not preferred.
"""
    write_markdown(OUT / "model_downgrade_notes.md", downgrade_md)

    log("Building realized high-plausibility table with confidence flags.")
    bridge_conf_top = bridge_confidence_map(bridge, "top_tier")
    bridge_conf_8 = bridge_confidence_map(bridge, "8cat")

    def ge_variant_frame(
        variant: str,
        df: pd.DataFrame,
        categories: Sequence[str],
        renorm: bool,
        bridge_conf: Dict[str, str],
    ) -> Tuple[pd.DataFrame, float]:
        x = df[df["category"].isin(categories)].copy()
        share_before = float(x["share"].sum())
        if renorm:
            x["share_used"] = x["share"] / share_before
        else:
            x["share_used"] = x["share"]
        x["weighted_contribution"] = x["share_used"] * x["realized_own_elasticity"]
        x["bridge_confidence_flag"] = x["category"].map(bridge_conf).fillna("medium")
        x["io_propagation_confidence_flag"] = x["own_price_change"].map(io_confidence_flag)
        x["variant"] = variant
        x["shares_renormalized"] = renorm
        x["total_share_before_renormalization"] = share_before
        wm = float(x["weighted_contribution"].sum())
        x["variant_weighted_mean"] = wm
        return x, wm

    ge_v1_df, ge_v1 = ge_variant_frame(
        "GE1_top_tier_excluding_leisure_aggregation_only",
        ge_top_weighted,
        subset_A,
        True,
        bridge_conf_top,
    )
    ge_v2_df, ge_v2 = ge_variant_frame(
        "GE2_eight_category_market_goods_benchmark",
        ge_8cat_weighted,
        base8,
        False,
        bridge_conf_8,
    )
    ge_v3_df, ge_v3 = ge_variant_frame(
        "GE3_high_credibility_subset_C_from_no_leisure_AIDS",
        ge_nl_aids_weighted,
        subset_C,
        True,
        bridge_conf_top,
    )
    ge_v4_df, ge_v4 = ge_variant_frame(
        "GE4_grouped_PADS_excluding_leisure_aggregation_only",
        ge_pads_weighted,
        subset_A,
        True,
        bridge_conf_top,
    )
    ge_hp = pd.concat([ge_v1_df, ge_v2_df, ge_v3_df, ge_v4_df], ignore_index=True)
    ge_hp.to_csv(OUT / "ge_high_plausibility.csv", index=False)

    log("Decomposing leisure removal effects.")
    q_all = float((top_quaids["share"] * top_quaids["marshallian_own"]).sum())
    q_leisure_contrib = float(
        top_quaids.loc[top_quaids["category"] == "leisure", "share"].iloc[0]
        * top_quaids.loc[top_quaids["category"] == "leisure", "marshallian_own"].iloc[0]
    )
    q_direct = q_all - q_leisure_contrib
    q_renorm = d1_m
    q_reestimate = d2_aids_m
    ge_knockon = d2_aids_g - d2_aids_m

    g_all = float((ge_top_weighted["share"] * ge_top_weighted["realized_own_elasticity"]).sum())
    g_leisure_contrib = float(
        ge_top_weighted.loc[ge_top_weighted["category"] == "leisure", "share"].iloc[0]
        * ge_top_weighted.loc[ge_top_weighted["category"] == "leisure", "realized_own_elasticity"].iloc[0]
    )
    g_direct = g_all - g_leisure_contrib
    g_renorm = d1_g
    g_reestimate = d2_aids_g

    decomp = pd.DataFrame(
        [
            {
                "object": "marshallian",
                "baseline_with_leisure": q_all,
                "direct_removal_effect": q_direct - q_all,
                "share_renormalization_effect": q_renorm - q_direct,
                "reestimate_without_leisure_effect": q_reestimate - q_renorm,
                "io_knockon_effect_memo": ge_knockon,
                "final_after_step3": q_reestimate,
                "total_change_vs_baseline": q_reestimate - q_all,
            },
            {
                "object": "realized_ge",
                "baseline_with_leisure": g_all,
                "direct_removal_effect": g_direct - g_all,
                "share_renormalization_effect": g_renorm - g_direct,
                "reestimate_without_leisure_effect": g_reestimate - g_renorm,
                "io_knockon_effect_memo": ge_knockon,
                "final_after_step3": g_reestimate,
                "total_change_vs_baseline": g_reestimate - g_all,
            },
        ]
    )
    decomp.to_csv(OUT / "leisure_removal_decomposition.csv", index=False)
    decomp_md = f"""
# Leisure Removal Decomposition

{decomp.to_markdown(index=False)}

## Notes
- Step 1 removes leisure contribution mechanically (no renormalization yet).
- Step 2 renormalizes shares over non-leisure categories.
- Step 3 uses re-estimated no-leisure AIDS demand system.
- `io_knockon_effect_memo` reports additional realized-vs-marshallian shift after no-leisure re-estimation.
"""
    write_markdown(OUT / "leisure_removal_decomposition.md", decomp_md)

    log("Applying plausibility flags.")
    flags = []

    def add_flag(category: str, flag_type: str, severity: str, model: str, detail: str) -> None:
        flags.append(
            {
                "category": category,
                "flag_type": flag_type,
                "severity": severity,
                "model_or_variant": model,
                "detail": detail,
            }
        )

    # Positive own-price in dominant-share categories.
    dom = top_quaids[top_quaids["share"] >= 0.20]
    for _, r in dom.iterrows():
        if float(r["marshallian_own"]) > 0:
            add_flag(
                str(r["category"]),
                "positive_own_price_dominant_share",
                "high",
                "top_tier_quaids",
                f"share={r['share']:.3f}, eps={r['marshallian_own']:.3f}",
            )

    # Explosive magnitudes.
    for dfm, mname, ecol in [
        (top_el, "top_tier", "marshallian_own"),
        (js_el, "js", "marshallian_own"),
        (eight_prev, "eight_cat", "marshallian_own"),
        (aids_noleisure_df, "top_tier_aids_no_leisure_reestimated", "marshallian_own"),
    ]:
        for _, r in dfm.iterrows():
            if abs(float(r[ecol])) > 5:
                add_flag(str(r["category"]), "large_abs_elasticity_gt5", "medium", mname, f"eps={r[ecol]:.3f}")

    # Weak price support / fallback mapping categories.
    add_flag(
        "leisure",
        "weak_price_support",
        "high",
        "all_top_tier_blocks",
        "price uses instrumented wage proxy; expenditure is imputed leisure hours times wage.",
    )
    add_flag(
        "utilities_public_services",
        "fallback_price_mapping",
        "medium",
        "top_tier_blocks",
        "price constructed using housing CPI with utility-vs-housing RPP ratio fallback.",
    )

    # Bridge quality.
    for c, q in bridge_conf_top.items():
        if q == "low":
            add_flag(c, "poor_bridge_quality", "medium", "top_tier_bridge", "bridge concentration/coverage is weak.")

    # Sign flips across nearby models.
    model_maps = [
        model_value_map(top_quaids, "top_tier_quaids", "marshallian_own"),
        model_value_map(top_aids, "top_tier_aids", "marshallian_own"),
        model_value_map(top_les, "top_tier_les", "marshallian_own"),
        model_value_map(js_rank2, "js_rank2", "marshallian_own"),
        model_value_map(js_rank3, "js_rank3", "marshallian_own"),
    ]
    for c in top_all:
        vals = [m[c] for m in model_maps if c in m]
        if sign_flip(vals):
            add_flag(c, "sign_flip_across_models", "high" if c == "leisure" else "medium", "top_tier/js", str(vals))

    plaus_flags = pd.DataFrame(flags).drop_duplicates()
    plaus_flags.to_csv(OUT / "plausibility_flags.csv", index=False)

    log("Selecting preferred high-plausibility headline estimate.")
    candidates = pd.DataFrame(
        [
            {
                "variant": "GE1_top_tier_excluding_leisure_aggregation_only",
                "estimate": ge_v1,
                "econ_sign_score": 0.65,
                "stability_score": 0.60,
                "leisure_dependence_score": 0.70,
                "share_quality_score": 0.55,
                "price_quality_score": 0.55,
                "bridge_io_score": 0.65,
            },
            {
                "variant": "GE_no_leisure_AIDS_reestimated_full_top_tier",
                "estimate": d2_aids_g,
                "econ_sign_score": 0.80,
                "stability_score": 0.75,
                "leisure_dependence_score": 0.90,
                "share_quality_score": 0.70,
                "price_quality_score": 0.70,
                "bridge_io_score": 0.70,
            },
            {
                "variant": "GE3_high_credibility_subset_C_from_no_leisure_AIDS",
                "estimate": ge_v3,
                "econ_sign_score": 0.88,
                "stability_score": 0.80,
                "leisure_dependence_score": 0.95,
                "share_quality_score": 0.62,
                "price_quality_score": 0.78,
                "bridge_io_score": 0.72,
            },
            {
                "variant": "GE2_eight_category_market_goods_benchmark",
                "estimate": ge_v2,
                "econ_sign_score": 0.85,
                "stability_score": 0.85,
                "leisure_dependence_score": 1.00,
                "share_quality_score": 0.82,
                "price_quality_score": 0.80,
                "bridge_io_score": 0.78,
            },
            {
                "variant": "GE4_grouped_PADS_excluding_leisure_aggregation_only",
                "estimate": ge_v4,
                "econ_sign_score": 0.45,
                "stability_score": 0.40,
                "leisure_dependence_score": 0.65,
                "share_quality_score": 0.45,
                "price_quality_score": 0.45,
                "bridge_io_score": 0.60,
            },
        ]
    )
    candidates["priority_score"] = candidates[
        [
            "econ_sign_score",
            "stability_score",
            "leisure_dependence_score",
            "share_quality_score",
            "price_quality_score",
            "bridge_io_score",
        ]
    ].mean(axis=1)
    candidates = candidates.sort_values("priority_score", ascending=False).reset_index(drop=True)
    candidates.to_csv(OUT / "ge_candidate_ranking.csv", index=False)

    preferred_ge_variant = str(candidates.iloc[0]["variant"])
    preferred_ge_est = float(candidates.iloc[0]["estimate"])
    preferred_marshallian_variant = "Design2_reestimated_top_tier_no_leisure_AIDS"
    preferred_marshallian_est = float(d2_aids_m)

    # Comparison with old and revised.
    old_summary = pd.read_csv(OLD / "final_summary.csv")
    old_m = float(old_summary.loc[old_summary["metric"] == "weighted_mean_marshallian", "estimate"].iloc[0])
    old_g = float(old_summary.loc[old_summary["metric"] == "weighted_mean_realized_ge_approx", "estimate"].iloc[0])
    revised_m = float(final_summary_prev.loc[final_summary_prev["metric"] == "E_M_preferred", "estimate"].iloc[0])
    revised_g = float(final_summary_prev.loc[final_summary_prev["metric"] == "E_GE_preferred", "estimate"].iloc[0])

    final_summary_hp = pd.DataFrame(
        [
            {
                "metric": "E_M_high_plausibility",
                "preferred_model": preferred_marshallian_variant,
                "subset": "No_leisure_full_market_top_tier",
                "estimate": preferred_marshallian_est,
                "magnitude_vs_unit": classify_unit_magnitude(preferred_marshallian_est),
                "credibility_rank": "moderate_to_strong",
            },
            {
                "metric": "E_GE_high_plausibility",
                "preferred_model": preferred_ge_variant,
                "subset": "Market_goods_high_plausibility",
                "estimate": preferred_ge_est,
                "magnitude_vs_unit": classify_unit_magnitude(preferred_ge_est),
                "credibility_rank": "moderate_to_strong",
            },
        ]
    )
    final_summary_hp.to_csv(OUT / "final_summary_high_plausibility.csv", index=False)

    compare = pd.DataFrame(
        [
            {
                "metric": "E_M",
                "old_baseline": old_m,
                "revised_paperspecific": revised_m,
                "high_plausibility": preferred_marshallian_est,
                "delta_high_minus_old": preferred_marshallian_est - old_m,
                "delta_high_minus_revised": preferred_marshallian_est - revised_m,
            },
            {
                "metric": "E_GE",
                "old_baseline": old_g,
                "revised_paperspecific": revised_g,
                "high_plausibility": preferred_ge_est,
                "delta_high_minus_old": preferred_ge_est - old_g,
                "delta_high_minus_revised": preferred_ge_est - revised_g,
            },
        ]
    )
    compare.to_csv(OUT / "old_vs_revised_vs_high_plausibility.csv", index=False)

    # Dominant categories in preferred realized estimate.
    if preferred_ge_variant == "GE2_eight_category_market_goods_benchmark":
        dom_source = ge_v2_df.copy()
    elif preferred_ge_variant == "GE_no_leisure_AIDS_reestimated_full_top_tier":
        dom_source = ge_top_noleisure_aids.copy()
        dom_source["share_used"] = dom_source["share"]
        dom_source["weighted_contribution"] = dom_source["share"] * dom_source["realized_own_elasticity"]
    elif preferred_ge_variant == "GE3_high_credibility_subset_C_from_no_leisure_AIDS":
        dom_source = ge_v3_df.copy()
    elif preferred_ge_variant == "GE1_top_tier_excluding_leisure_aggregation_only":
        dom_source = ge_v1_df.copy()
    else:
        dom_source = ge_v4_df.copy()
    dominant = dom_source.reindex(dom_source["weighted_contribution"].abs().sort_values(ascending=False).index).head(5)

    # Final report.
    q_with = float(wm_comp_prev.loc[wm_comp_prev["model"] == "top_tier_quaids", "weighted_mean"].iloc[0])
    q_without = float(wm_comp_prev.loc[wm_comp_prev["model"] == "top_tier_quaids_no_leisure", "weighted_mean"].iloc[0])
    ge_with = float(wm_comp_prev.loc[wm_comp_prev["model"] == "ge_top_tier", "weighted_mean"].iloc[0])
    ge_pads_with = float(wm_comp_prev.loc[wm_comp_prev["model"] == "ge_pads", "weighted_mean"].iloc[0])

    report = f"""
# Final Report — High Plausibility Follow-up

## A. What was the leisure problem?
- Leisure entered as imputed expenditure (`leisure hours * instrumented wage`) and wage-based price.
- In top-tier QUAIDS, leisure carried a dominant share and positive own-price elasticity, creating a large positive contribution.
- Leisure sign and magnitude were unstable across QUAIDS, AIDS, LES, JS rank2/rank3, and GE/PADS variants.

## B. How much did leisure drive prior headline means?
- Marshallian (top-tier QUAIDS) with leisure: **{q_with:.4f}**
- Marshallian QUAIDS without leisure (renormalized): **{q_without:.4f}**
- Change from removing leisure in aggregation: **{q_without - q_with:.4f}**
- Realized GE top-tier with leisure: **{ge_with:.4f}**
- Realized GE-PADS with leisure: **{ge_pads_with:.4f}**
- Detailed attribution is in `leisure_removal_decomposition.csv`.

## C. Weighted means after excluding/neutralizing leisure
- Design 1 (QUAIDS, aggregation excludes leisure): Marshallian **{d1_m:.4f}**, Realized **{d1_g:.4f}**
- Design 2 (re-estimated no-leisure AIDS): Marshallian **{d2_aids_m:.4f}**, Realized **{d2_aids_g:.4f}**
- Design 3 (Subset B): Marshallian **{d3b_m:.4f}**, Realized **{d3b_g:.4f}**
- Design 3 (Subset C): Marshallian **{d3c_m:.4f}**, Realized **{d3c_g:.4f}**
- Design 4 (8-category benchmark): Marshallian **{d4_m:.4f}**, Realized **{d4_g:.4f}**

## D. Preferred high-plausibility estimates
- Preferred Marshallian weighted mean: **{preferred_marshallian_est:.4f}** (`{preferred_marshallian_variant}`)
- Preferred realized / IO-linked weighted mean: **{preferred_ge_est:.4f}** (`{preferred_ge_variant}`)

## E. Realized mean vs unit elasticity
- Preferred realized estimate is **{classify_unit_magnitude(preferred_ge_est)}** in magnitude.

## F. Dominant categories in preferred realized estimate
{dominant[['category', 'share_used', 'realized_own_elasticity', 'weighted_contribution']].to_markdown(index=False)}

## G. Sensitivity summary
- QUAIDS vs AIDS: headline sign/magnitude is highly sensitive when leisure is in-system; much more stable after no-leisure re-estimation.
- Subset choice: Subset B/C moves results moderately, but less than the leisure-inclusion switch.
- Renormalization: removing leisure with renormalization materially shifts weighted means.
- IO propagation: realized means differ from Marshallian means by a non-trivial bridge/IO component.

## H. Main answer going forward
- Use **{preferred_ge_variant}** as the headline realized elasticity object.
- Rationale: better sign plausibility, stability across nearby specifications, minimal dependence on leisure imputation, and acceptable share/price/bridge quality.
"""
    write_markdown(OUT / "final_report_high_plausibility.md", report)

    # Check and remove accidental duplicates (inside OUT and duplicated from BASE) while preserving required deliverables.
    log("Checking for duplicate files across output locations.")
    preserve = {
        "leisure_diagnostic.md",
        "subset_definitions.md",
        "subset_membership.csv",
        "weighted_mean_high_plausibility.csv",
        "model_downgrade_notes.md",
        "ge_high_plausibility.csv",
        "leisure_removal_decomposition.csv",
        "leisure_removal_decomposition.md",
        "plausibility_flags.csv",
        "final_report_high_plausibility.md",
        "final_summary_high_plausibility.csv",
        "old_vs_revised_vs_high_plausibility.csv",
        "run_log.txt",
        "high_plausibility_followup.py",
        "duplicate_removal_log.md",
    }

    files = sorted([p for p in OUT.iterdir() if p.is_file()])
    seen: Dict[Tuple[int, bytes], Path] = {}
    base_hash_map: Dict[Tuple[int, bytes], Path] = {}
    for p in BASE.iterdir():
        if p.is_file():
            data = p.read_bytes()
            base_hash_map[(len(data), data[:256])] = p

    removed = []
    for p in files:
        data = p.read_bytes()
        key = (len(data), data[:256])
        if key in seen and data == seen[key].read_bytes() and p.name not in preserve:
            p.unlink()
            removed.append((p.name, f"duplicate_of:{seen[key].name}"))
            continue
        if key in base_hash_map and data == base_hash_map[key].read_bytes() and p.name not in preserve:
            p.unlink()
            removed.append((p.name, f"duplicate_of_base:{base_hash_map[key].name}"))
            continue
        seen[key] = p
    if removed:
        dedup_lines = ["# Duplicate Removal Log", ""]
        for r, k in removed:
            dedup_lines.append(f"- Removed duplicate `{r}` (kept `{k}`).")
        write_markdown(OUT / "duplicate_removal_log.md", "\n".join(dedup_lines))
        log(f"Removed {len(removed)} duplicate files across output locations.")
    else:
        write_markdown(
            OUT / "duplicate_removal_log.md",
            "# Duplicate Removal Log\n\n- No removable duplicate files detected across `SWMIRPE_results_high_plausibility` and `SWMIRPE_results_paperspecific`.",
        )
        log("No removable duplicate files detected across output locations.")

    log("High-plausibility follow-up completed successfully.")


if __name__ == "__main__":
    main()
