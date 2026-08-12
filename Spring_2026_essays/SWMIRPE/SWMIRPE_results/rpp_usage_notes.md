# RPP Usage Notes

- RPP is annual state-level (not monthly/quarterly), so it is used only as a supplemental robustness layer.
- Baseline identification uses CPI time/region variation.
- Robustness adjustment applies RPP multipliers to CPI levels by category group:
  - goods-heavy categories: `rpp_goods`
  - housing: `0.8*rpp_housing_services + 0.2*rpp_utilities`
  - service-heavy categories: `rpp_other_services`
- Missing CEX state or missing RPP values default to multiplier 1.
