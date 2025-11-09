## EV Range Prediction Project — Summary of work so far

This README summarizes all the preprocessing, feature engineering, modeling, and diagnostic work performed on the `electric_vehicles_spec_2025` dataset in this workspace.

Location: `C:\Users\asus\OneDrive\Desktop\AICTE_EV_PROJECT`

### High-level goal
- Build a supervised regression pipeline to predict vehicle driving range (target column `range_km`) from vehicle specification fields.

### What I changed / implemented (chronological)
1. Environment and CSV load fixes
   - Fixed a FileNotFound issue by auto-detecting the CSV in the workspace (original file was `electric_vehicles_spec_2025.csv.csv`).
   - Added an environment-check cell that prints `sys.executable` and installs missing Python packages in the running kernel when required.

2. Data cleaning and preprocessing
   - Cleaned column names: stripped, lowercased, replaced spaces with `_`, removed non-word characters.
   - Dropped exact duplicate rows.
   - Trimmed whitespace in string/object columns.
   - Converted object-like columns to numeric when majority of sample values parse as numeric (removed commas, percent signs before parsing).
   - Numeric NaN filling: median imputation (or 0 if a column was entirely NaN).
   - Categorical NaN filling: most frequent value (mode) or `'Unknown'` if entirely missing.
   - Saved cleaned dataset as `electric_vehicles_spec_2025_cleaned.csv`.

3. Feature engineering & scaling
   - Identified numeric and categorical columns.
   - One-hot encoded low-cardinality categorical columns (cardinality < 30).
   - Frequency-encoded high-cardinality categorical columns (e.g., `brand`, `model`, `source_url`) for ML pipeline.
   - Scaled numeric features with StandardScaler and MinMaxScaler and saved both versions of the feature matrix:
     - `features_standard_scaled.csv`
     - `features_minmax_scaled.csv`
   - Saved scalers: `scaler_standard.joblib`, `scaler_minmax.joblib`.

4. Reusable sklearn pipeline
   - Built a ColumnTransformer pipeline that:
     - imputes numeric features (median) and standard-scales them,
     - imputes categorical features and one-hot-encodes low-cardinality columns,
     - frequency-encodes high-cardinality columns before scaling.
   - Split into train/test (80/20) and saved:
     - `X_train_preprocessed.csv`, `X_test_preprocessed.csv`, `y_train.csv`, `y_test.csv`.
   - Saved the pipeline object as `preprocessor_pipeline.joblib`.

5. Diagnostics and baselines
   - Printed target (`range_km`) summary statistics: mean ≈ 393 km, median ≈ 398 km, std ≈ 103 km, min 135, max 685.
   - Computed correlations: `battery_capacity_kwh` had the highest correlation with `range_km` (~0.88).
   - Baseline 5-fold CV results (using preprocessor):
     - Linear Regression: R² ≈ 0.948, RMSE ≈ 23.2 km (mean)
     - RandomForest (n_estimators=200): R² ≈ 0.961, RMSE ≈ 20.3 km (mean)
   - RandomForest feature importance (top): `battery_capacity_kwh` dominated (~80% importance), then `height_mm`, then `efficiency_wh_per_km`.

6. Model training cell added
   - Added a notebook cell that trains and evaluates these models (CV + holdout test):
     - LinearRegression, DecisionTree, RandomForest, GradientBoosting, XGBoost, SVR, KNN.
   - The cell will save each fitted model as `model_<Name>.joblib` and write `model_comparison_results.csv` with metrics.

7. Hyperparameter tuning (planned / in-progress)
   - I added the plan and can run randomized/grid search for RandomForest, XGBoost and GradientBoosting to improve test RMSE and persist the best models as `model_<Name>_tuned.joblib` and a CSV `tuned_models_results.csv`.

### Files / artifacts created (paths relative to project root)
- `electric_vehicles_spec_2025_cleaned.csv` — cleaned dataset used for modeling.
- `features_standard_scaled.csv` — feature matrix with StandardScaler applied.
- `features_minmax_scaled.csv` — feature matrix with MinMaxScaler applied.
- `scaler_standard.joblib`, `scaler_minmax.joblib` — scaler objects for reuse.
- `preprocessor_pipeline.joblib` — sklearn ColumnTransformer preprocessing pipeline.
- `X_train_preprocessed.csv`, `X_test_preprocessed.csv`, `y_train.csv`, `y_test.csv` — preprocessed train/test splits.
- `model_<Name>.joblib` (for each model trained by the model cell) — saved fitted models.
- `model_comparison_results.csv` — model metrics CSV produced by the comparison cell.

### Quick reproduction / how to run
1. Open `ev_project.ipynb` in VS Code or JupyterLab and run cells in order. Cells are written to be idempotent and install missing packages when needed.

2. If you prefer to run from a terminal, ensure the environment has the necessary packages. Example for the project venv (Windows PowerShell):

```powershell
C:\Users\asus\OneDrive\Desktop\AICTE_EV_PROJECT\.venv\Scripts\python.exe -m pip install --upgrade pip
C:\Users\asus\OneDrive\Desktop\AICTE_EV_PROJECT\.venv\Scripts\python.exe -m pip install pandas scikit-learn joblib xgboost
```

3. Run the notebook cells in order (Environment-check -> Clean & Save -> Feature engineering -> Preprocessing pipeline -> Diagnostics -> Model training).

4. After running the model training cell, check `model_comparison_results.csv` for the evaluation table and `model_<Name>.joblib` files for saved models.

### Example: loading a saved model and making a prediction
```python
import joblib, pandas as pd
# load pipeline and model
pre = joblib.load('preprocessor_pipeline.joblib')
model = joblib.load('model_RandomForest.joblib')
# create a one-row DataFrame with the same raw spec columns (including categorical columns as original names)
raw = pd.DataFrame([{
    'battery_capacity_kwh': 75,
    'efficiency_wh_per_km': 180,
    # include other required columns here...
}])
# transform and predict
X = pre.transform(raw)
pred = model.predict(X)
print('Predicted range_km:', pred[0])
```

### Important notes and caveats
- Target leakage: confirm there are no columns that directly encode `range_km` or are post-measurement fields. Remove or transform those before training final models.
- Dominant features: `battery_capacity_kwh` drives most of the predictive power. If you want a model that generalizes to novel battery/efficiency regimes, consider domain features or additional meta-data (e.g., test cycle, tyre spec).
- Encoding strategy: for high-cardinality text fields like `brand`/`model`, consider out-of-fold target encoding (to avoid too many OHE columns and reduce overfitting) if you plan to push performance further.

### Next recommended steps (short)
1. Run hyperparameter tuning for RandomForest, XGBoost, and GradientBoosting and persist tuned models.
2. Implement out-of-fold target encoding for `brand` and `model` and re-run baselines.
3. Add unit tests / small validation script that loads saved artifacts and runs a sanity prediction for a few examples.
4. (Optional) Build a small API (FastAPI/Flask) wrapping the preprocessor + model for real-time predictions.

If you want, I can now run the hyperparameter tuning cell I planned, produce `tuned_models_results.csv`, and save the tuned best model artifacts.

---
Generated: November 2, 2025

## GitHub upload (what to push)

Recommended files to publish to your GitHub repository:

- `cleaned_ev_data.csv` (or `electric_vehicles_spec_2025_cleaned.csv`) — the cleaned dataset generated by the notebook/scripts. This is the primary artifact other users will need to reproduce modeling.
- `README.md` — this documentation file (already present).
- `clean_ev_data.py` and `eda_ev_data.py` — small helper scripts to reproduce cleaning and generate a quick EDA summary.
- `requirements.txt` and `LICENSE` — environment and licensing metadata.

If you want me to prepare a branch with these files staged and a suggested commit message, run the PowerShell commands in the next section (they will copy the cleaned CSV to `cleaned_ev_data.csv`, create a branch `add-cleaned-data`, add files, commit, and push the branch to your remote repository). I cannot push directly from here because I don't have your GitHub credentials.

### Ready-to-run PowerShell commands (creates a branch + push)
Run these from the project root (`C:\Users\asus\OneDrive\Desktop\AICTE_EV_PROJECT`). They will create a branch named `add-cleaned-data` and push it to your GitHub repo `https://github.com/Ishwari0306/Week-1`.

```powershell
# Copy the cleaned CSV to a standard filename used in the repo
Copy-Item .\electric_vehicles_spec_2025_cleaned.csv .\cleaned_ev_data.csv

# Initialize git if needed
if (!(Test-Path .git)) { git init }

# Add remote (overwrite origin if present)
git remote remove origin 2>$null; git remote add origin https://github.com/Ishwari0306/Week-1

# Create a branch, stage files, commit, and push
git checkout -b add-cleaned-data
git add README.md cleaned_ev_data.csv clean_ev_data.py eda_ev_data.py requirements.txt LICENSE .gitignore
git commit -m "Add cleaned dataset and helper scripts"
git push -u origin add-cleaned-data
```

After pushing, open GitHub and create a Pull Request from `add-cleaned-data` into `main` (you can merge immediately if you want). If you prefer to commit directly to `main`, replace the last two lines with:

```powershell
git branch -M main
git push -u origin main
```

If the cleaned CSV is large (it isn't in your case) you would instead use Git LFS or host the dataset externally and include a README link.

## Best model (summary)

After preprocessing and model comparison focused on predicting `range_km`, the best-performing model on the held-out test split was:

- Model: SVR (Support Vector Regressor)
- Saved artifact: `model_SVR_range_retrained.joblib`
- Test metrics (holdout test set): R² ≈ 0.9782, RMSE ≈ 0.147 (scaled units), MAE ≈ 0.116
- Explainability artifacts: `plots_range_retrained/SVR_avp.png` (Actual vs Predicted), `plots_range_retrained/SVR_res.png` (residuals), `plots_range_retrained/SVR_permutation_importances.png`

Why SVR?
- It achieved the highest R² on the holdout test split and showed stable performance in nested CV for robustness checks.

How to load and use the saved model

```python
import joblib, pandas as pd
# load the full pipeline (preprocessor + model) if you saved a combined pipeline, or load preprocessor + model separately
pipeline = joblib.load('model_SVR_range_retrained.joblib')
# if pipeline is a sklearn Pipeline, you can call pipeline.predict(raw_df)
# otherwise, apply preprocessor first then model.predict

raw = pd.DataFrame([{
   # fill with the raw input column names used in training
   'battery_capacity_kwh': 75,
   'efficiency_wh_per_km': 180,
   # ... other required columns
}])
pred = pipeline.predict(raw)
print('Predicted range_km:', pred[0])
```

Notes / Caveats
- Confirm that `raw` contains the same columns and types as the training raw DataFrame (including categorical columns). If you saved separate preprocessor and model objects use them in order: `X = preprocessor.transform(raw)` then `model.predict(X)`.

