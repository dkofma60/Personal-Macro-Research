# Price Construction Notes

## Baseline Sources
- CPI broad-category panel from prior harmonization scaffold (`results/cpi_category_panel.parquet`).
- RPP state-level annual components (`results/rpp_clean.csv`) for optional enhancement.

## 8-category Prices
- Direct CPI category assignment by region-quarter.
- Optional RPP scaling:
  - goods-heavy categories: `rpp_goods`
  - housing: `0.8*rpp_housing_services + 0.2*rpp_utilities`
  - service-heavy categories: `rpp_other_services`

## Top-tier Prices (Shojaeddini-style analogue)
- `non_durables`: Geary aggregate from food/apparel/other-goods prices.
- `consumer_services`: Geary aggregate from medical/recreation/education-communication prices.
- `utilities_public_services`: housing CPI scaled by utility-vs-housing RPP ratio where available.
- `housing`, `transportation`: mapped directly from broad CPI categories.
- `leisure`: instrumented after-tax wage index.

## Geary / Geary-Khamis Analogue
For aggregate category g composed of subitems i:
\[
P_g = \frac{\sum_i E_i}{\sum_i E_i / P_i}
\]
This preserves multilateral aggregation logic at available data granularity.

## Geography
- State-level matching is used when available (`STATE` non-missing).
- If state detail is unavailable, region-time structure is retained.
