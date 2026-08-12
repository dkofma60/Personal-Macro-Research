# Döpper Feasibility Notes

- Literal Döpper-style random-coefficients scanner-data demand (store-SKU-market panel with micro moments and covariance restrictions) is **not feasible** with available local data.
- Available local data are household-level CEX aggregates, broad CPI prices, annual RPP, and BEA IO tables.
- Implemented instead: a **Döpper-inspired modular diagnostic block**:
  - category-specific demand regressions,
  - heterogeneity controls (demographics, geography, time),
  - category-level comparison of price sensitivity.
