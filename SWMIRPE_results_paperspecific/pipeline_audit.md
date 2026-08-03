# Pipeline Audit (Old Run)

## Old Category System
- Primary estimation used one 8-category system:
  `food_beverages`, `housing`, `apparel`, `transportation`, `medical_care`, `recreation`, `education_communication`, `other_goods_services`.

## Old Estimation Method
- LA/AIDS-like share equations estimated equation-by-equation with WLS.
- Restrictions (adding-up/homogeneity/symmetry) were imposed by post-estimation projection.
- Single demand block only; no explicit Shojaeddini QUAIDS/LES hierarchy.

## Old IO / Realized Elasticity Method
- Built a category-to-sector mapping using BEA sector PCE weights and candidate-sector rules.
- Used domestic requirements matrix to propagate shocks.
- Realized elasticity computed from propagated prices fed into estimated demand matrix.
- No explicit bridge-matrix accounting architecture with discrepancy handling.

## Old Baseline Results
- Old weighted Marshallian mean: **-0.417473**
- Old weighted realized GE approximation: **-1.803557**

## Main Weaknesses in Old Pipeline
- No explicit top-tier full-consumption (with leisure) block as primary estimate.
- No explicit QUAIDS / AIDS / LES hierarchy with comparative reporting.
- No Jorgenson-Slesnick rank-2/rank-3 exact-aggregation benchmark block.
- No Döpper-inspired modular diagnostic block.
- Bridge logic for IO propagation was practical but not explicitly documented in Inforum/IdLIFT bridge notation.
- Durable flow and leisure treatment were limited.

## What Is Preserved
- Core CEX/CPI/RPP/IO parsing and harmonization scaffold.
- 8-category system and prior outputs as baseline comparators.
- Existing reproducible output architecture and robust file generation.

## What Is Replaced / Upgraded
- New paper-specific hierarchy:
  - Shojaeddini-style top-tier full-consumption system with leisure (QUAIDS/AIDS/LES).
  - Jorgenson-Slesnick rank-2/rank-3 translog analogue benchmark.
  - Döpper-inspired modular diagnostics (explicitly not random-coefficients scanner replication).
  - Inforum/IdLIFT-style bridge matrix + IO propagation with documented accounting approximations.
