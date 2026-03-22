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
