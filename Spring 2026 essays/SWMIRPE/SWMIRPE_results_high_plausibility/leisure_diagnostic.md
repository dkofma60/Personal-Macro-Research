# Leisure Diagnostic

## How Leisure Enters Each Block
- Top-tier QUAIDS/AIDS/LES: leisure is an explicit sixth category with `exp_leisure = leisure_hours * wage_used` and `price_leisure = wage_iv` (instrumented wage proxy).
- Jorgenson-Slesnick benchmark analogue (rank2/rank3): reuses the same top-tier full-consumption dataset and leisure construction.
- Realized GE top-tier block: uses top-tier demand system with leisure category and bridge mapping to IO sectors (`7`, `51`) during propagation.
- Grouped PADS block: uses grouped top-tier categories including leisure, so realized responses inherit leisure imputation and wage-price proxy effects.

## Quantified Influence
| model_block     |   leisure_share |   leisure_own_elasticity |   leisure_contribution |   weighted_mean_all |   weighted_mean_excl_leisure_renorm |   delta_excl_minus_all |   included_market_share_before_renorm |
|:----------------|----------------:|-------------------------:|-----------------------:|--------------------:|------------------------------------:|-----------------------:|--------------------------------------:|
| top_tier_quaids |       0.748205  |                 2.01118  |             1.50478    |            1.37983  |                           -0.496228 |             -1.87606   |                              0.251795 |
| top_tier_aids   |       0.748205  |                -0.931929 |            -0.697274   |           -0.821676 |                           -0.494061 |              0.327615  |                              0.251795 |
| top_tier_les    |       0.748205  |                -1        |            -0.748205   |           -0.993438 |                           -0.973939 |              0.0194988 |                              0.251795 |
| js_rank2        |       0.748205  |                -0.931929 |            -0.697274   |           -0.821676 |                           -0.494061 |              0.327615  |                              0.251795 |
| js_rank3        |       0.748205  |                 2.01118  |             1.50478    |            1.37983  |                           -0.496228 |             -1.87606   |                              0.251795 |
| ge_top_tier     |       0.0223572 |                -0.133315 |            -0.00298056 |           -0.826775 |                           -0.842633 |             -0.0158584 |                              0.977643 |
| ge_pads         |       0.878805  |                -0.962585 |            -0.845924   |           -1.03064  |                           -1.52409  |             -0.49345   |                              0.121195 |

## Diagnostic Readout
- Leisure share in top-tier QUAIDS: **0.748**.
- Leisure own-price elasticity sign positive in at least one block: **True**.
- Leisure sign flips across model blocks: **True**.
- Leisure elasticity range across blocks: **3.011**.

## Root Cause Conclusion
Primary issue is measurement construction, not only functional form: leisure enters with very large imputed expenditure share and wage-based price proxy; this creates high leverage in adding-up and makes top-tier weighted means extremely sensitive to wage instrument/imputation and QUAIDS curvature.
