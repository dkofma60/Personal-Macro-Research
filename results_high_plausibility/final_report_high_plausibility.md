# Final Report — High Plausibility Follow-up

## A. What was the leisure problem?
- Leisure entered as imputed expenditure (`leisure hours * instrumented wage`) and wage-based price.
- In top-tier QUAIDS, leisure carried a dominant share and positive own-price elasticity, creating a large positive contribution.
- Leisure sign and magnitude were unstable across QUAIDS, AIDS, LES, JS rank2/rank3, and GE/PADS variants.

## B. How much did leisure drive prior headline means?
- Marshallian (top-tier QUAIDS) with leisure: **1.3798**
- Marshallian QUAIDS without leisure (renormalized): **-0.9400**
- Change from removing leisure in aggregation: **-2.3198**
- Realized GE top-tier with leisure: **-0.8268**
- Realized GE-PADS with leisure: **-1.0306**
- Detailed attribution is in `leisure_removal_decomposition.csv`.

## C. Weighted means after excluding/neutralizing leisure
- Design 1 (QUAIDS, aggregation excludes leisure): Marshallian **-0.4962**, Realized **-0.6710**
- Design 2 (re-estimated no-leisure AIDS): Marshallian **-0.9420**, Realized **-0.9487**
- Design 3 (Subset B): Marshallian **-0.9688**, Realized **-0.9734**
- Design 3 (Subset C): Marshallian **-0.9664**, Realized **-0.9700**
- Design 4 (8-category benchmark): Marshallian **-1.0078**, Realized **-0.9544**

## D. Preferred high-plausibility estimates
- Preferred Marshallian weighted mean: **-0.9420** (`Design2_reestimated_top_tier_no_leisure_AIDS`)
- Preferred realized / IO-linked weighted mean: **-0.9544** (`GE2_eight_category_market_goods_benchmark`)

## E. Realized mean vs unit elasticity
- Preferred realized estimate is **near_unit** in magnitude.

## F. Dominant categories in preferred realized estimate
| category       |   share_used |   realized_own_elasticity |   weighted_contribution |
|:---------------|-------------:|--------------------------:|------------------------:|
| housing        |    0.42034   |                 -0.890353 |              -0.374251  |
| food_beverages |    0.224251  |                 -1.01883  |              -0.228473  |
| medical_care   |    0.0963196 |                 -1.68747  |              -0.162537  |
| transportation |    0.144423  |                 -0.792461 |              -0.11445   |
| apparel        |    0.0209958 |                 -1.59607  |              -0.0335108 |

## G. Sensitivity summary
- QUAIDS vs AIDS: headline sign/magnitude is highly sensitive when leisure is in-system; much more stable after no-leisure re-estimation.
- Subset choice: Subset B/C moves results moderately, but less than the leisure-inclusion switch.
- Renormalization: removing leisure with renormalization materially shifts weighted means.
- IO propagation: realized means differ from Marshallian means by a non-trivial bridge/IO component.

## H. Main answer going forward
- Use **GE2_eight_category_market_goods_benchmark** as the headline realized elasticity object.
- Rationale: better sign plausibility, stability across nearby specifications, minimal dependence on leisure imputation, and acceptable share/price/bridge quality.
