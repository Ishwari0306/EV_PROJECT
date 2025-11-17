import sys, importlib, json, pandas as pd, math, os
sys.path.append('.')
import app_clean as m

# Test input (non-default) to exercise models
row = {
    'battery_capacity_kwh': 100.0,
    'efficiency_wh_per_km': 150.0,
    'top_speed_kmh': 180.0,
    'acceleration_0_100_s': 10.0,
    'fast_charging_power_kw_dc': 150.0,
    'battery_type_Lithium-ion': 0,
    'battery_type_Lithium Iron Phosphate (LFP)': 0,
    'battery_type_NMC': 1,
}


def try_model(fname):
    out = {'file': fname, 'ok': False}
    model = m.safe_load_model(fname)
    if model is None:
        out['error'] = 'load_failed'
        return out
    try:
        df = pd.DataFrame([row])
        means = m.compute_feature_means()
        aligned, missing = m.align_row_to_model(model, df, default_values=means)
        raw = m.predict_with_model(model, aligned)
        raw_val = None
        if raw:
            try:
                raw_val = float(raw[0])
            except Exception:
                raw_val = None
        scalers = m.find_candidate_scalers()
        target_stats = m.compute_target_stats()
        rescaled = None
        method = None
        # try scalers first
        for s in scalers:
            try:
                inv = m.inverse_scale_predictions(s, raw if raw is not None else [])
                if inv:
                    v = float(inv[0])
                    if not math.isnan(v) and v>0 and v<2000:
                        rescaled = v
                        method = f'scaler:{type(s).__name__}'
                        break
            except Exception:
                continue
        if rescaled is None and raw_val is not None:
            rescaled = m.rescale_prediction(raw_val, scalers, target_stats)
            method = 'rescale_prediction'
        out.update({
            'ok': True,
            'raw': raw,
            'raw_val': raw_val,
            'missing_count': len(missing),
            'rescaled': rescaled,
            'method': method,
            'target_stats': target_stats,
        })
    except Exception as e:
        out['error'] = repr(e)
    return out

models = m.list_model_files()
results = []
for f in models:
    r = try_model(f)
    results.append(r)

out_path = 'model_check_results.json'
with open(out_path, 'w', encoding='utf-8') as fh:
    json.dump({'models': results}, fh, indent=2)

# Print brief summary
print('WROTE', out_path)
for r in results:
    if not r.get('ok'):
        print('FAILED:', r['file'], r.get('error'))
    else:
        print('MODEL:', r['file'], 'raw_val=', r.get('raw_val'), 'rescaled=', r.get('rescaled'), 'method=', r.get('method'))

print('\nSummary:')
reasonable = [r for r in results if r.get('ok') and r.get('rescaled') and isinstance(r.get('rescaled'), (int, float)) and r.get('rescaled')>0]
if reasonable:
    for r in reasonable:
        print(f" {r['file']} -> {r['rescaled']:.1f} km via {r['method']}")
else:
    print(' No reasonable rescaled outputs found')

print('Done')
