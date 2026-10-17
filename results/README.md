# Results — என்ன என்ன

| File | என்ன |
|---|---|
| `final_report.txt` / `.json` | Main run: 5m/1m × QQQ/SPY, FTMO verdict, filter ablations, risk-sensitivity curve, day statistics |
| `validation_final.txt` / `.json` | Shortlist validation: bootstrap 95% CI, quarterly stability, per-config stats |
| `validation_1m.txt` | 1-minute neighbourhood + quarterly + cost-stress (incl. the knife-edge finding) |
| `robust_5m.csv` / `robust_1m.csv` | Configs that are positive OOS on **both** QQQ and SPY (cross-instrument shortlist) |
| `sweep_QQQ_5m.csv`, `sweep_SPY_5m.csv`, `sweep_QQQ_1m.csv`, `sweep_SPY_1m.csv` | Full parameter grids (~1,500-1,700 configs each) with IS/OOS columns |
| `trades_QQQ_5m.csv` | Every trade of the shipped config on QQQ 5m (entry/exit/P&L/R/exit reason) |

Regenerate: `python backtest/sweep.py` → `python backtest/joint_analysis.py` → `python backtest/validate_final.py` → `python backtest/final_report.py`
