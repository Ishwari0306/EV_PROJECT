# Plot visualizations for GradientBoosting model
import os
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style='whitegrid')

root = Path(r"C:\Users\asus\OneDrive\Desktop\AICTE_EV_PROJECT")
model_path = root / 'model_GradientBoosting.joblib'
clean_csv = root / 'electric_vehicles_spec_2025_cleaned.csv'
features_std = root / 'features_standard_scaled.csv'

# Load model
if not model_path.exists():
    raise FileNotFoundError(f"Model not found: {model_path}")
model = joblib.load(model_path)
print('Loaded model:', model)

# Load test features and target
X_test = None
y_test = None

# Preferred: use preprocessed test CSVs if present
x_test_pre = root / 'X_test_preprocessed.csv'
y_test_csv = root / 'y_test.csv'
if x_test_pre.exists() and y_test_csv.exists():
    X_test = pd.read_csv(x_test_pre)
    y_test = pd.read_csv(y_test_csv).squeeze()
    print('Using preprocessed test CSVs')
else:
    # Fallback: use standardized features (features_standard_scaled.csv) and cleaned CSV to split
    if features_std.exists() and clean_csv.exists():
        X_all = pd.read_csv(features_std)
        df = pd.read_csv(clean_csv)
        if len(X_all) != len(df):
            print('Warning: features and cleaned CSV lengths differ. Will align by index where possible.')
            minlen = min(len(X_all), len(df))
            X_all = X_all.iloc[:minlen]
            df = df.iloc[:minlen]
        y_all = df['range_km']
        # reproduce train/test split used in notebook (random_state=42, test_size=0.2)
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X_all, y_all, test_size=0.2, random_state=42)
        print('Reconstructed test split from features_standard_scaled.csv and cleaned CSV')
    else:
        # Last resort: use cleaned CSV numeric columns only
        if clean_csv.exists():
            df = pd.read_csv(clean_csv)
            if 'range_km' not in df.columns:
                raise ValueError('Target `range_km` not found in cleaned CSV')
            y_all = df['range_km']
            X_all = df.select_dtypes(include=[np.number]).drop(columns=['range_km'], errors='ignore')
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(X_all, y_all, test_size=0.2, random_state=42)
            print('Used numeric columns from cleaned CSV as fallback features')
        else:
            raise FileNotFoundError('No suitable features or cleaned CSV found to build test set')

# Ensure X_test and y_test are set
if X_test is None or y_test is None:
    raise RuntimeError('Failed to prepare test set')

# Convert to numpy arrays
X_test_arr = X_test.values
y_test_arr = np.array(y_test)

# Predict
y_pred = model.predict(X_test_arr)
residuals = y_test_arr - y_pred

# 1) Predicted vs Actual scatter
plt.figure(figsize=(7,7))
plt.scatter(y_test_arr, y_pred, alpha=0.7)
lims = [min(y_test_arr.min(), y_pred.min()), max(y_test_arr.max(), y_pred.max())]
plt.plot(lims, lims, 'r--', linewidth=1)
plt.xlabel('Actual range_km')
plt.ylabel('Predicted range_km')
plt.title('GradientBoosting: Actual vs Predicted')
plt.tight_layout()
out1 = root / 'gb_actual_vs_predicted.png'
plt.savefig(out1, dpi=150)
plt.close()
print('Saved', out1)

# 2) Residuals histogram + KDE
plt.figure(figsize=(8,4))
sns.histplot(residuals, kde=True, bins=30)
plt.axvline(0, color='k', linestyle='--')
plt.xlabel('Residual (actual - predicted)')
plt.title('GradientBoosting Residuals')
plt.tight_layout()
out2 = root / 'gb_residuals_hist.png'
plt.savefig(out2, dpi=150)
plt.close()
print('Saved', out2)

# 3) Feature importances (if available)
if hasattr(model, 'feature_importances_'):
    fi = model.feature_importances_
    # Try to get column names from X_test
    if hasattr(X_test, 'columns'):
        cols = X_test.columns.tolist()
    else:
        cols = [f'feat_{i}' for i in range(len(fi))]
    imp_series = pd.Series(fi, index=cols).sort_values(ascending=False)
    topk = imp_series.head(20)
    plt.figure(figsize=(8,6))
    sns.barplot(x=topk.values, y=topk.index, palette='viridis')
    plt.xlabel('Importance')
    plt.title('GradientBoosting Feature Importances (top 20)')
    plt.tight_layout()
    out3 = root / 'gb_feature_importances.png'
    plt.savefig(out3, dpi=150)
    plt.close()
    print('Saved', out3)
else:
    print('Model has no feature_importances_ attribute; skipping importance plot')

print('All plots created in', root)
