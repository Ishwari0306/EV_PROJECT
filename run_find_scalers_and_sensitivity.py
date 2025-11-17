import sys
import os
import json
import math
import joblib
import numpy as np
import pandas as pd
sys.path.append('.')
import app_clean as m

OUT = 'models_validation.json'

# test input base
base = {
    'battery_capacity_kwh': 60.0,
    'efficiency_wh_per_km': 150.0,
    'top_speed_kmh': 180.0,
    'acceleration_0_100_s': 8.5,
    'fast_charging_power_kw_dc': 150.0,
    'battery_type_Lithium-ion': 1,
    'battery_type_Lithium Iron Phosphate (LFP)': 0,
    'battery_type_NMC': 0,
}

# grid for sensitivity tests
battery_grid = [40.0, 60.0, 80.0, 100.0]
eff_grid = [120.0, 150.0, 200.0]

# load candidate scalers but keep filename mapping
scaler_candidates = []  # list of (filename, scaler_obj)
for fn in os.listdir(os.getcwd()):
    if not fn.endswith('.joblib'):
        continue
    if fn.startswith('model_'):
        continue
    p = os.path.join(os.getcwd(), fn)
    try:
        obj = joblib.load(p)
    except Exception:
        continue
    # if object itself is scaler-like
    if hasattr(obj, 'inverse_transform'):
        scaler_candidates.append((fn, obj))
    # if dict containing scalers
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if hasattr(v, 'inverse_transform'):
                scaler_candidates.append((f"{fn}::{k}", v))

# helper to extract scalers from inside model pipeline/attributes
def scalers_in_model(model):
    found = []
    try:
        if hasattr(model, 'named_steps'):
            for name, step in model.named_steps.items():
                if hasattr(step, 'inverse_transform'):
                    found.append((f'pipeline:{name}', step))
                # if step is a transformer with sub-objects
                for attr in ['scaler_', 'transformer_', 'preprocessor', 'steps']:
                    if hasattr(step, attr):
                        val = getattr(step, attr)
                        if hasattr(val, 'inverse_transform'):
                            found.append((f'pipeline:{name}.{attr}', val))
    except Exception:
        pass
    # some models may have direct attributes
    for attr in ['scaler_', 'target_scaler', 'y_scaler', 'out_scaler']:
        if hasattr(model, attr):
            v = getattr(model, attr)
            if hasattr(v, 'inverse_transform'):
                found.append((f'model_attr:{attr}', v))
    return found

# load models
models = m.list_model_files()
results = []
# compute dataset target stats
target_stats = m.compute_target_stats()

for mf in models:
    rec = {'file': mf, 'found_scaler': None, 'scaler_source': None, 'raw_pred': None, 'rescaled_via_scaler': None, 'sensitivity': {}}
    model = m.safe_load_model(mf)
    if model is None:
        rec['error'] = 'failed_to_load'
        results.append(rec)
        continue
    # align base input
    means = m.compute_feature_means()
    df = pd.DataFrame([base])
    aligned, missing = m.align_row_to_model(model, df, default_values=means)
    raw = m.predict_with_model(model, aligned)
    raw_val = None
    if raw:
        try:
            raw_val = float(raw[0])
        except Exception:
            raw_val = None
    rec['raw_pred'] = raw_val

    # try scalers inside model first
    tried = []
    model_scalers = scalers_in_model(model)
    success = False
    for name, s in model_scalers:
        try:
            inv = m.inverse_scale_predictions(s, [raw_val])
            if inv:
                v = float(inv[0])
                # plausibility check
                if target_stats:
                    low = target_stats['min'] - 0.1 * abs(target_stats['min'])
                    high = target_stats['max'] + 0.1 * abs(target_stats['max'])
                    if low <= v <= high:
                        rec['found_scaler'] = True
                        rec['scaler_source'] = name
                        rec['rescaled_via_scaler'] = v
                        success = True
                        break
                else:
                    if not math.isnan(v) and 0 < v < 2000:
                        rec['found_scaler'] = True
                        rec['scaler_source'] = name
                        rec['rescaled_via_scaler'] = v
                        success = True
                        break
        except Exception:
            continue
        tried.append(name)

    # try external scaler files
    if not success:
        for fn, s in scaler_candidates:
            try:
                inv = m.inverse_scale_predictions(s, [raw_val])
            except Exception:
                continue
            if inv:
                try:
                    v = float(inv[0])
                except Exception:
                    continue
                if target_stats:
                    low = target_stats['min'] - 0.1 * abs(target_stats['min'])
                    high = target_stats['max'] + 0.1 * abs(target_stats['max'])
                    if low <= v <= high:
                        rec['found_scaler'] = True
                        rec['scaler_source'] = fn
                        rec['rescaled_via_scaler'] = v
                        success = True
                        break
                else:
                    if not math.isnan(v) and 0 < v < 2000:
                        rec['found_scaler'] = True
                        rec['scaler_source'] = fn
                        rec['rescaled_via_scaler'] = v
                        success = True
                        break
    if not success:
        rec['found_scaler'] = False

    # Sensitivity tests: battery capacity monotonicity, efficiency monotonicity
    sens = {'battery': {'inputs': [], 'outputs': []}, 'efficiency': {'inputs': [], 'outputs': []}}
    # vary battery_capacity_kwh
    for b in battery_grid:
        test = base.copy()
        test['battery_capacity_kwh'] = b
        df_test = pd.DataFrame([test])
        aligned_t, _ = m.align_row_to_model(model, df_test, default_values=means)
        raw_t = m.predict_with_model(model, aligned_t)
        vraw = None
        if raw_t:
            try:
                vraw = float(raw_t[0])
            except Exception:
                vraw = None
        # convert to km using discovered scaler or rescale_prediction
        final = None
        if vraw is not None:
            if rec.get('found_scaler') and rec.get('scaler_source'):
                # try to find scaler object
                if rec['scaler_source'].startswith('pipeline:') or rec['scaler_source'].startswith('model_attr:'):
                    # re-extract from model
                    s_obj = None
                    for name, s in model_scalers:
                        if name == rec['scaler_source']:
                            s_obj = s
                            break
                else:
                    # find by filename
                    s_obj = None
                    for fn, s in scaler_candidates:
                        if fn == rec['scaler_source']:
                            s_obj = s
                            break
                if s_obj is not None:
                    try:
                        inv = m.inverse_scale_predictions(s_obj, [vraw])
                        if inv:
                            final = float(inv[0])
                    except Exception:
                        final = m.rescale_prediction(vraw, m.find_candidate_scalers(), target_stats)
                else:
                    final = m.rescale_prediction(vraw, m.find_candidate_scalers(), target_stats)
            else:
                final = m.rescale_prediction(vraw, m.find_candidate_scalers(), target_stats)
        sens['battery']['inputs'].append(b)
        sens['battery']['outputs'].append(final)

    # efficiency
    for e in eff_grid:
        test = base.copy()
        test['efficiency_wh_per_km'] = e
        df_test = pd.DataFrame([test])
        aligned_t, _ = m.align_row_to_model(model, df_test, default_values=means)
        raw_t = m.predict_with_model(model, aligned_t)
        vraw = None
        if raw_t:
            try:
                vraw = float(raw_t[0])
            except Exception:
                vraw = None
        final = None
        if vraw is not None:
            if rec.get('found_scaler') and rec.get('scaler_source'):
                s_obj = None
                if rec['scaler_source'].startswith('pipeline:') or rec['scaler_source'].startswith('model_attr:'):
                    for name, s in model_scalers:
                        if name == rec['scaler_source']:
                            s_obj = s
                            break
                else:
                    for fn, s in scaler_candidates:
                        if fn == rec['scaler_source']:
                            s_obj = s
                            break
                if s_obj is not None:
                    try:
                        inv = m.inverse_scale_predictions(s_obj, [vraw])
                        if inv:
                            final = float(inv[0])
                    except Exception:
                        final = m.rescale_prediction(vraw, m.find_candidate_scalers(), target_stats)
                else:
                    final = m.rescale_prediction(vraw, m.find_candidate_scalers(), target_stats)
            else:
                final = m.rescale_prediction(vraw, m.find_candidate_scalers(), target_stats)
        sens['efficiency']['inputs'].append(e)
        sens['efficiency']['outputs'].append(final)

    # simple monotonicity checks
    def monotonic_increase(xs):
        # treat None as break
        prev = None
        for x in xs:
            if x is None:
                return False
            if prev is None:
                prev = x
            else:
                if x < prev - 1e-6:
                    return False
                prev = x
        return True

    def monotonic_decrease(xs):
        prev = None
        for x in xs:
            if x is None:
                return False
            if prev is None:
                prev = x
            else:
                if x > prev + 1e-6:
                    return False
                prev = x
        return True

    battery_ok = monotonic_increase(sens['battery']['outputs'])
    # efficiency: higher Wh/km should reduce range, so outputs should decrease
    efficiency_ok = monotonic_decrease(sens['efficiency']['outputs'])

    rec['sensitivity'] = {
        'battery': sens['battery'],
        'efficiency': sens['efficiency'],
        'battery_monotonic_increase': battery_ok,
        'efficiency_monotonic_decrease': efficiency_ok,
    }

    results.append(rec)

# optionally update models_metadata.json for exact scaler matches
meta_path = os.path.join(os.getcwd(), 'models_metadata.json')
if os.path.exists(meta_path):
    try:
        with open(meta_path, 'r', encoding='utf-8') as fh:
            meta = json.load(fh)
    except Exception:
        meta = {}
else:
    meta = {}

updated = False
for r in results:
    if r.get('found_scaler') and r.get('scaler_source'):
        name = os.path.basename(r['file'])
        # prefer to save exact scaler filename if available
        src = r['scaler_source']
        if src.startswith('pipeline:') or src.startswith('model_attr:'):
            # mark as use_model_scaler
            new = {'method': 'use_model_scaler', 'scaler_ref': src}
        else:
            new = {'method': 'use_file_scaler', 'scaler_ref': src}
        if meta.get(name) != new:
            meta[name] = new
            updated = True

if updated:
    try:
        with open(meta_path, 'w', encoding='utf-8') as fh:
            json.dump(meta, fh, indent=2)
    except Exception:
        pass

with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump({'models': results, 'updated_metadata_written': updated}, fh, indent=2)

print('WROTE', OUT)
