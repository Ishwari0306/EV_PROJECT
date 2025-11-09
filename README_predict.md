# Quick: Predict EV range_km using a saved pipeline

This file shows how to use `predict_range.py` to make predictions with the retrained SVR pipeline saved in the repository.

Prerequisites
- Use the same Python environment where the models were trained (see `requirements.txt`).
- The saved pipeline `model_SVR_range_retrained.joblib` (or another `model_<Name>_range_retrained.joblib`) must be present in the repo root.

Examples

Predict on a CSV file and save results:

```powershell
python predict_range.py --model model_SVR_range_retrained.joblib --input some_new_rows.csv --output preds.csv
```

Predict on the first 5 rows (fast test):

```powershell
python predict_range.py --model model_SVR_range_retrained.joblib --input features_standard_scaled.csv --nrows 5 --output quick_preds.csv
```

Pipe CSV to the script (read from stdin) and get CSV on stdout:

```powershell
Get-Content some_new_rows.csv | python predict_range.py --model model_SVR_range_retrained.joblib
```

Notes
- Input CSV must contain the same feature columns used during training (no `range_km` column required; if provided it will be dropped).
- The saved pipeline includes preprocessing steps, so pass raw feature columns as in the training data.
- If you want a different model, pass `--model <path>`.

If you'd like, I can:
- Add a small test harness `sample_input.csv` with a few example rows (sanitized) and a short unit test.
- Create a minimal CLI wrapper that automatically picks the best model (by reading `metrics_summary_range_km.csv`).
