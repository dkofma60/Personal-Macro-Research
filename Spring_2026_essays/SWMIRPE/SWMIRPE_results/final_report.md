# Average Elasticity Estimation Report

## Scope
This report estimates two objects for U.S. consumption categories using only local files in `Demand Elasticity`:
1. Primary target: share-weighted mean Marshallian own-price elasticity
\( \bar{\varepsilon}^M = \sum_i s_i \varepsilon_{ii}^M \)
2. Secondary target: IO-linked realized own-price elasticity approximation
\( \bar{\varepsilon}^{GE} = \sum_i s_i \tilde{\varepsilon}_{ii} \)

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
\[
w_i = \alpha_i + \sum_j \gamma_{ij} \ln p_j + \beta_i \ln\left(\frac{x}{P}\right) + Z_i'\delta + u_i
\]
with Stone index \(\ln P = \sum_k w_k \ln p_k\), estimated by weighted equation-by-equation WLS (robustness: ridge regularization).

Elasticities at weighted mean shares:
\[
\varepsilon_{ij}^M = -\mathbf{1}(i=j) + \frac{\gamma_{ij}}{w_i} - \frac{\beta_i}{w_i} w_j
\]

Preferred estimate:
- **\(\bar{\varepsilon}^M = -0.4175\)** (bootstrap 95% CI: [-2.3605, 1.1197])
- Identification quality (conservative rank): **weak**

Marshallian own elasticities:
| category | share | marshallian_own_elasticity | contribution_share_times_elasticity | ci_lower_95 | ci_upper_95 |
| --- | --- | --- | --- | --- | --- |
| food_beverages | 0.2241 | -0.2245 | -0.0503 | -1.7495 | 1.0379 |
| housing | 0.4207 | 2.1388 | 0.8998 | -2.2983 | 4.9660 |
| apparel | 0.0210 | -10.5832 | -0.2221 | -27.9706 | -2.6203 |
| transportation | 0.1444 | -1.6668 | -0.2407 | -2.5021 | -0.6020 |
| medical_care | 0.0961 | -4.2581 | -0.4093 | -9.3999 | -0.7212 |
| recreation | 0.0543 | -6.3867 | -0.3466 | -18.7395 | 5.6163 |
| education_communication | 0.0129 | -0.5619 | -0.0072 | -18.3702 | 13.8741 |
| other_goods_services | 0.0265 | -1.5491 | -0.0411 | -15.1574 | 6.1040 |

## IO-Linked Realized Elasticity Approximation
Construction:
1. Build sector requirement matrix \(L\) from `CxC_Domestic_Sector.xlsx` (2017 sector table).
2. Recover direct-requirement analogue \(A = I - L^{-1}\).
3. Propagate cost shocks via \((I-A')^{-1}\).
4. Map sector price changes to consumption categories.
5. Map induced category price vector into quantity changes using estimated Marshallian matrix.
6. Define realized own elasticity for each category:
\[
\tilde{\varepsilon}_{ii} = \frac{\Delta \ln Q_i}{\Delta \ln P_i}
\]

Preferred approximate estimate:
- **\(\bar{\varepsilon}^{GE} = -1.8036\)** (IO-linked approximation, not a fully identified full-GE object)

Realized own elasticities:
| category | share | realized_own_elasticity | contribution_share_times_realized_elasticity |
| --- | --- | --- | --- |
| food_beverages | 0.2241 | 0.2237 | 0.0501 |
| housing | 0.4207 | 0.4665 | 0.1963 |
| apparel | 0.0210 | -8.9529 | -0.1879 |
| transportation | 0.1444 | -1.6948 | -0.2448 |
| medical_care | 0.0961 | -5.1694 | -0.4969 |
| recreation | 0.0543 | -4.9939 | -0.2710 |
| education_communication | 0.0129 | -14.3672 | -0.1847 |
| other_goods_services | 0.0265 | -25.0776 | -0.6647 |

## Robustness Summary
| scenario | weighted_mean_marshallian |
| --- | --- |
| baseline_8cat_regional | -0.4175 |
| alternative_7cat_grouping | -1.4350 |
| national_only_prices | -0.4623 |
| regional_plus_rpp | -0.2711 |
| regularized_ridge | -0.4203 |
| exclude_housing | -1.2185 |
| pce_inferred_shares_weighting | -3.1762 |

## Limitations
- Public CEX geography and aggregate-category construction limit clean causal identification.
- Education/communication and other-goods/services mappings are approximate at this data granularity.
- Apparel lacks regional CPI in provided broad files; national fallback is used.
- GE object is an IO-linked propagation approximation, not an estimated structural CGE equilibrium.
