# EV Range Prediction — Retrained Models (summary)

This report summarizes the retraining run targeting `range_km` and points to saved artifacts.

## Saved model files
- `model_RandomForest_range_retrained.joblib`
- `model_GradientBoosting_range_retrained.joblib`
- `model_DecisionTree_range_retrained.joblib`
- `model_KNN_range_retrained.joblib`
- `model_SVR_range_retrained.joblib`
- `model_Ridge_range_retrained.joblib`

## Plots (in `plots_range_retrained/`)
For each model there are two plots:
- `<Model>_avp.png` — Actual vs Predicted (test set)
- `<Model>_res.png` — Residual histogram (test set)

Files created:
- `plots_range_retrained/RandomForest_avp.png`
- `plots_range_retrained/RandomForest_res.png`
- `plots_range_retrained/GradientBoosting_avp.png`
- `plots_range_retrained/GradientBoosting_res.png`
- `plots_range_retrained/DecisionTree_avp.png`
- `plots_range_retrained/DecisionTree_res.png`
- `plots_range_retrained/KNN_avp.png`
- `plots_range_retrained/KNN_res.png`
- `plots_range_retrained/SVR_avp.png`
- `plots_range_retrained/SVR_res.png`
- `plots_range_retrained/Ridge_avp.png`
- `plots_range_retrained/Ridge_res.png`

## Metrics (test set)
See `metrics_summary_range_km.csv` for machine-readable values. Key numbers:

- RandomForest: Test R² = 0.9644, RMSE = 0.188, MAE = 0.135
- GradientBoosting: Test R² = 0.9723, RMSE = 0.166, MAE = 0.124
- DecisionTree: Test R² = 0.9545, RMSE = 0.213, MAE = 0.142
- KNN: Test R² = 0.7990, RMSE = 0.447, MAE = 0.328
- SVR: Test R² = 0.9782, RMSE = 0.147, MAE = 0.116
- Ridge: Test R² = 0.9626, RMSE = 0.193, MAE = 0.155

## Observations & recommendations
- The top performers by R² on the held-out test split are `SVR`, `GradientBoosting`, and `RandomForest`.
- KNN underperformed relative to others (R² ~0.80); likely due to feature scaling / high-dimensional indicators.
- The models show very strong test performance; still verify that the test split is representative and that no leakage occurred (e.g., engineered features computed using full dataset).

Recommended next steps:
1. Embed these plots and the metrics table into `ev_model_visualization.ipynb` for interactive inspection.
2. Run learning-curve checks for the top models to ensure no hidden overfitting.
3. Compute and save feature importances for tree-based models and consider SHAP for SVR to explain predictions.
4. If you need production-ready artifacts, I can add a small `predict_range.py` script that loads the best pipeline and predicts on new rows.

If you want, I can now embed the plots and the summary table into the existing notebook and add a final cell with recommendations.


## Explainability artifacts

The following additional explainability plots were generated and saved to `plots_range_retrained/`:

- `GradientBoosting_shap_bar.png` — SHAP feature importance (bar) for the GradientBoosting model
- `GradientBoosting_shap_summary.png` — SHAP summary plot (beeswarm) for GradientBoosting
- `SVR_permutation_importances.png` — Permutation importance bar chart for SVR (test set)

These complement the per-model AVP/residual plots and help explain which features drive `range_km` predictions.

## Nested cross-validation (robust generalization)

Nested CV was run for selected top models (outer 5-fold with inner GridSearchCV). Key nested-R² means (outer folds):

- SVR: nested R² mean ≈ 0.9482 ± 0.0327
- GradientBoosting: nested R² mean ≈ 0.9705 ± 0.0051

See `metrics_nested_cv.csv` for the full fold-level results.

## Next steps completed

- Installed `shap` into the project venv and generated the SHAP plots above.
- Saved all explainability plots under `plots_range_retrained/`.
