# Bridge Documentation

## Objective
Reconstruct a consumption bridge matrix **D** in the Inforum/IdLIFT spirit using available local BEA files.

## Construction
- Rows: BEA sector commodities (`IO_CORE_SECTORS`).
- Columns: consumer categories (8-category and top-tier systems).
- Within each category, candidate sectors are chosen using documented concordance logic.
- Weights are allocated proportionally to BEA sector PCE values (`Use_Sector.xlsx`, `F010`), then normalized so each column sums to 1.

## Bridge Equations
Forward mapping (category demand to commodities):
\[
C = D J
\]
Reverse price mapping (commodity prices to category prices):
\[
p_J = D' p_w
\]

## Limitations
- This is a reduced-dimension bridge reconstruction (15 sectors), not a full Inforum 97x92 bridge.
- Column normalization is exact; row controls are approximate due limited local detail.
- Discrepancy handling follows wp01004 guidance in reduced form (explicitly documented in IO notes).
