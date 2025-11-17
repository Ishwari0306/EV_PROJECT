import sys, json, os
sys.path.append('.')
import importlib
import pandas as pd
m = importlib.import_module('app_clean')
models = m.list_model_files()
manual_cols = ['battery_capacity_kwh','efficiency_wh_per_km','top_speed_kmh','acceleration_0_100_s','fast_charging_power_kw_dc','battery_type_Lithium-ion','battery_type_Lithium Iron Phosphate (LFP)','battery_type_NMC']
report = []
for mf in models:
    rec = {'file': mf}
    model = m.safe_load_model(mf)
    if model is None:
        rec['error'] = 'failed_to_load'
        report.append(rec)
        continue
    try:
        exp = m.get_model_expected_features(model)
    except Exception as e:
        exp = None
    rec['expected_features_count'] = len(exp) if exp else None
    rec['expected_features_sample'] = exp[:40] if exp else None
    # pipeline steps
    try:
        if hasattr(model, 'named_steps'):
            rec['pipeline_steps'] = list(model.named_steps.keys())
        else:
            rec['pipeline_steps'] = None
    except Exception:
        rec['pipeline_steps'] = None
    # model attrs of interest
    attrs = {}
    for a in ['feature_names_in_', 'feature_names', 'get_booster', 'scaler_', 'target_scaler', 'y_scaler']:
        try:
            if hasattr(model, a):
                val = getattr(model, a)
                if a == 'get_booster' and callable(val):
                    try:
                        b = model.get_booster()
                        attrs['booster_feature_names'] = getattr(b, 'feature_names', None)
                    except Exception:
                        attrs['booster_feature_names'] = None
                else:
                    try:
                        attrs[a] = str(val) if not hasattr(val, '__len__') else (list(val)[:20] if hasattr(val, '__iter__') else str(val))
                    except Exception:
                        attrs[a] = 'unserializable'
        except Exception:
            attrs[a] = 'error'
    rec['interesting_attrs'] = attrs
    # mapping of manual cols
    mapped = []
    if exp:
        for ef in exp:
            en = ef.lower().replace('-', '_').replace(' ', '_')
            for mc in manual_cols:
                mc_n = mc.lower().replace('-', '_').replace(' ', '_')
                if mc_n in en or en in mc_n or set(en.split('_')) & set(mc_n.split('_')):
                    mapped.append({'manual': mc, 'expected': ef})
                    break
    rec['manual_mapped'] = mapped
    report.append(rec)

out='models_features_report.json'
with open(out, 'w', encoding='utf-8') as fh:
    json.dump(report, fh, indent=2)
print('WROTE', out)
