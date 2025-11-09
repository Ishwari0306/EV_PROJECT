"""
predict_range.py

Small utility to load a saved sklearn Pipeline (preprocessor + model)
and make range_km predictions for new input rows.

Usage examples (from repo root):
python predict_range.py --model model_SVR_range_retrained.joblib --input some_rows.csv --output preds.csv

If --input is omitted the script will read from stdin (CSV) and print predictions to stdout.
"""
import argparse
import sys
import os
import joblib
import pandas as pd


def load_model(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}")
    return joblib.load(path)


def predict(model, X):
    # model is expected to be a Pipeline handling preprocessing
    preds = model.predict(X)
    return preds


def main():
    parser = argparse.ArgumentParser(description='Load a saved pipeline and predict EV range_km for input rows (CSV).')
    parser.add_argument('--model', '-m', default=None, help='Path to saved joblib pipeline. If omitted, the script will pick the best model from metrics_summary_range_km.csv')
    parser.add_argument('--input', '-i', help='CSV file with feature columns (if omitted, read CSV from stdin)')
    parser.add_argument('--output', '-o', help='Output CSV file to write predictions (adds column "predicted_range_km"). If omitted, prints to stdout')
    parser.add_argument('--nrows', type=int, default=None, help='If provided, read only the first N rows from input (useful for quick tests)')
    args = parser.parse_args()

    model_path = args.model
    in_path = args.input
    out_path = args.output

    # If no model provided, try to auto-select best model from metrics CSV
    if model_path is None:
        metrics_csv = 'metrics_summary_range_km.csv'
        try:
            if os.path.exists(metrics_csv):
                import pandas as _pd
                mdf = _pd.read_csv(metrics_csv)
                # prefer highest test_r2; fall back to first row
                if 'test_r2' in mdf.columns and 'model_file' in mdf.columns:
                    best_row = mdf.loc[mdf['test_r2'].idxmax()]
                    model_path = best_row['model_file']
                    print(f"Auto-selected best model from {metrics_csv}: {model_path}")
                else:
                    print(f"Metrics CSV {metrics_csv} missing required columns ('test_r2','model_file')", file=sys.stderr)
            else:
                print(f"Metrics CSV {metrics_csv} not found and no --model provided", file=sys.stderr)
        except Exception as e:
            print('Failed to read metrics CSV for auto-selection:', e, file=sys.stderr)

    try:
        model = load_model(model_path)
    except Exception as e:
        print('Failed to load model:', e, file=sys.stderr)
        sys.exit(2)

    # Read input
    try:
        if in_path:
            df = pd.read_csv(in_path, nrows=args.nrows)
        else:
            # read CSV from stdin
            df = pd.read_csv(sys.stdin, nrows=args.nrows)
    except Exception as e:
        print('Failed to read input CSV:', e, file=sys.stderr)
        sys.exit(3)

    # If target present, drop it
    if 'range_km' in df.columns:
        df = df.drop(columns=['range_km'])

    # Run prediction
    try:
        preds = predict(model, df)
    except Exception as e:
        print('Prediction failed:', e, file=sys.stderr)
        sys.exit(4)

    result = df.copy()
    result['predicted_range_km'] = preds

    if out_path:
        result.to_csv(out_path, index=False)
        print(f'Wrote predictions to {out_path}')
    else:
        # print CSV to stdout
        print(result.to_csv(index=False))


if __name__ == '__main__':
    main()
