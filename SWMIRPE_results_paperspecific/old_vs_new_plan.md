# Old vs New Plan

1. Reuse old data-cleaning and harmonization outputs where valid (`cex_clean`, `cpi_category_panel`, `rpp_clean`).
2. Rebuild household dataset with added variables needed for paper-specific blocks:
   - utilities, vehicle purchases, wage/hour fields, adults/children counts.
3. Construct paper-specific category systems in parallel:
   - Shojaeddini top-tier 6 categories (with leisure).
   - Legacy 8-category system.
   - Döpper-inspired modular finer categories.
4. Build top-tier leisure and durable-service-flow proxies:
   - after-tax hourly wage proxy + instrumented wage fallback.
   - transportation durable-flow adjustment from vehicle purchase variables.
5. Estimate demand hierarchy:
   - QUAIDS (primary), AIDS, LES on top-tier full consumption.
   - Jorgenson-Slesnick rank-2/rank-3 analogue benchmark.
   - Döpper-inspired modular reduced-form diagnostics.
6. Build Inforum/IdLIFT-style bridge matrix D and IO propagation mechanics.
7. Produce two realized-elasticity variants:
   - GE-1: top-tier demand + bridge + IO.
   - GE-2: grouped PADS-style demand + bridge + IO.
8. Generate decompositions, credibility ranking, old-vs-new comparison, final revised report, and PDF.
