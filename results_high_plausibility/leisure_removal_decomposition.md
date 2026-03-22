# Leisure Removal Decomposition

| object      |   baseline_with_leisure |   direct_removal_effect |   share_renormalization_effect |   reestimate_without_leisure_effect |   io_knockon_effect_memo |   final_after_step3 |   total_change_vs_baseline |
|:------------|------------------------:|------------------------:|-------------------------------:|------------------------------------:|-------------------------:|--------------------:|---------------------------:|
| marshallian |                1.37983  |              -1.50478   |                      -0.37128  |                           -0.445726 |              -0.00672199 |           -0.941954 |                  -2.32178  |
| realized_ge |               -0.268702 |               0.0997471 |                      -0.502048 |                           -0.277673 |              -0.00672199 |           -0.948676 |                  -0.679974 |

## Notes
- Step 1 removes leisure contribution mechanically (no renormalization yet).
- Step 2 renormalizes shares over non-leisure categories.
- Step 3 uses re-estimated no-leisure AIDS demand system.
- `io_knockon_effect_memo` reports additional realized-vs-marshallian shift after no-leisure re-estimation.
