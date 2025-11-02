"""
clean_ev_data.py

Small script to reproduce the cleaning steps performed in the notebook.
Run from project root (Windows PowerShell):
    python .\clean_ev_data.py

This reads the original raw CSV (if present), applies column cleaning, trimming,
basic object->numeric conversion heuristic, imputes missing values, and writes
`cleaned_ev_data.csv` in the project root.
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent
RAW_CANDIDATES = [
    ROOT / 'electric_vehicles_spec_2025.csv.csv',
    ROOT / 'electric_vehicles_spec_2025.csv',
    ROOT / 'EV_raw_dataset.csv'
]

def find_raw():
    for p in RAW_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError('No raw CSV found. Expected one of: ' + ', '.join(str(p) for p in RAW_CANDIDATES))

def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace(r'[^\w]', '', regex=True)

    # Drop exact duplicates
    df = df.drop_duplicates()

    # Trim whitespace in string columns
    for c in df.select_dtypes(include=['object']).columns:
        df[c] = df[c].astype(str).str.strip()

    # Convert object columns to numeric where majority parse as numbers
    for c in df.columns:
        if df[c].dtype == 'object':
            sample = df[c].dropna().astype(str).head(200).str.replace(',', '').str.replace('%', '')
            parsed = pd.to_numeric(sample, errors='coerce')
            if len(sample) > 0 and parsed.notna().sum() / len(sample) > 0.5:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce')

    # Fill numeric NaNs with median (or 0 if all NaN)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for c in num_cols:
        med = df[c].median()
        if pd.isna(med):
            med = 0
        df[c] = df[c].fillna(med)

    # Fill categorical NaNs with mode or 'Unknown'
    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
    for c in cat_cols:
        df[c].replace({'': np.nan, 'nan': np.nan, 'None': np.nan}, inplace=True)
        if df[c].dropna().empty:
            df[c] = df[c].fillna('Unknown')
        else:
            mode = df[c].mode(dropna=True)
            fill = mode.iloc[0] if not mode.empty else 'Unknown'
            df[c] = df[c].fillna(fill)

    return df

def main():
    raw = find_raw()
    print('Loading raw CSV from', raw)
    df = pd.read_csv(raw)
    df_clean = clean(df)
    out = ROOT / 'cleaned_ev_data.csv'
    df_clean.to_csv(out, index=False)
    print('Saved cleaned CSV to', out, 'shape', df_clean.shape)

if __name__ == '__main__':
    main()
