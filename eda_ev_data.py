"""
eda_ev_data.py

Quick EDA script that loads the cleaned dataset and writes a short text summary
and a basic histogram for `range_km`.

Run:
    python .\eda_ev_data.py

Output:
    eda_summary.txt (project root)
    figures/range_hist.png
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
CLEAN_PATH = ROOT / 'cleaned_ev_data.csv'
OUT_SUM = ROOT / 'eda_summary.txt'
FIG_DIR = ROOT / 'figures'
FIG_DIR.mkdir(exist_ok=True)

def main():
    if not CLEAN_PATH.exists():
        raise FileNotFoundError('cleaned_ev_data.csv not found. Run clean_ev_data.py first or copy the cleaned CSV to project root.')
    df = pd.read_csv(CLEAN_PATH)
    out_lines = []
    out_lines.append(f'Loaded cleaned data: {CLEAN_PATH}  shape={df.shape}')
    if 'range_km' in df.columns:
        y = df['range_km']
        out_lines.append('\nTarget (range_km) stats:')
        out_lines.append(f' count: {y.count()}')
        out_lines.append(f' mean: {y.mean():.2f}')
        out_lines.append(f' median: {y.median():.2f}')
        out_lines.append(f' std: {y.std():.2f}')
        out_lines.append(f' min: {y.min()}  max: {y.max()}')
        # plot
        plt.figure(figsize=(6,4))
        plt.hist(y.dropna(), bins=30)
        plt.title('Distribution of range_km')
        plt.xlabel('range_km')
        plt.ylabel('count')
        plt.tight_layout()
        plt.savefig(FIG_DIR / 'range_hist.png')
        out_lines.append(f'Wrote histogram to {FIG_DIR / "range_hist.png"}')
    else:
        out_lines.append('No column named range_km found in dataset.')

    with OUT_SUM.open('w', encoding='utf8') as f:
        f.write('\n'.join(out_lines))
    print('Wrote EDA summary to', OUT_SUM)

if __name__ == '__main__':
    main()
