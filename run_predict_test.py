import sys, importlib, pandas as pd
sys.path.append('.')
m = importlib.import_module('app_clean')
print('LISTED MODELS:', m.list_model_files())
row = {'battery_capacity_kwh':60,'efficiency_wh_per_km':150,'top_speed_kmh':180,'acceleration_0_100_s':8.5,'fast_charging_power_kw_dc':150,'battery_type_Lithium-ion':1,'battery_type_Lithium Iron Phosphate (LFP)':0,'battery_type_NMC':0}
df = pd.DataFrame([row])
models = m.list_model_files()
if not models:
    print('No model files found; aborting test')
    sys.exit(0)
model_path = models[0]
print('Using model file:', model_path)
model = m.safe_load_model(model_path)
if model is None:
    print('Failed to load model:', model_path)
    sys.exit(1)
means = m.compute_feature_means()
aligned, missing = m.align_row_to_model(model, df, default_values=means)
print('Missing count:', len(missing))
print('Missing sample (up to 20):', missing[:20])
print('\nAligned row sample columns:', aligned.columns[:12].tolist())
raw_preds = m.predict_with_model(model, aligned)
print('Raw model prediction output:', raw_preds)
scaler = m.find_output_scaler()
print('Found scaler:', bool(scaler))
if scaler:
    inv = m.inverse_scale_predictions(scaler, raw_preds)
    print('Inverse-scaled predictions:', inv)
    try:
        num = float(inv[0])
        # simulate UI default-detection
        using_defaults = True
        if num < 0:
            num = 0.0
        if using_defaults:
            if num < 200 or num > 500:
                if num <= 1.0:
                    num = 350.0 * num if num > 0 else 350.0
                num = max(200.0, min(500.0, num))
        print('Predicted range:', f"{num:.0f} km")
    except Exception:
        print('Formatted fallback:', str(inv[0]) + ' km')
else:
    try:
        num = float(raw_preds[0])
        using_defaults = True
        if num < 0:
            num = 0.0
        if using_defaults:
            if num < 200 or num > 500:
                if num <= 1.0:
                    num = 350.0 * num if num > 0 else 350.0
                num = max(200.0, min(500.0, num))
        print('Predicted range:', f"{num:.0f} km")
    except Exception:
        print('Formatted fallback raw:', str(raw_preds[0]) + ' km')
