# Synth: market-share EDA

Exploratory analysis of a synthetic market-share dataset (4 manufacturers × 4 product tiers × 51 states × 78 months) prepared for a Business Analytics Developer application.

- **Findings, traps, follow-up answers:** [REPORT.md](REPORT.md)
- **Interactive dashboard:** [`dashboard/index.html`](dashboard/index.html). Download it and open it in a browser.
- **Tableau Public version:** [`tableau/Four-Brand Share Monitor.twbx`](tableau/) (generated, not yet opened in Tableau) or build it yourself with [`tableau/BUILD_GUIDE.md`](tableau/BUILD_GUIDE.md)
- **Code:** `analysis/`
  - `eda.py`: EDA
  - `further_analysis.py`: follow-up questions
  - `dq_checks.py`: data-quality guards
  - `build_dashboard.py`: dashboard and Tableau data
  - `build_tableau_workbook.py`: Tableau workbook
- **Data:** `data/market_share_synthetic.csv`
