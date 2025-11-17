import os
import json
import time
from typing import List, Optional

import joblib
import pandas as pd
import requests
import streamlit as st

# Optional OpenAI import; app works without it (falls back to Wikipedia)
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# Force using Wikipedia only by default. Set to False to allow OpenAI when
# configured and enabled in the UI. This protects users who don't want external
# API calls or don't have keys.
FORCE_WIKIPEDIA = True

st.set_page_config(page_title='EV Range Explorer (Clean)', layout='wide')

# Defaults used in manual input — used to detect "defaults" and optionally clamp output
DEFAULT_BATTERY_KWH = 60.0
DEFAULT_EFFICIENCY_WH_PER_KM = 150.0
DEFAULT_TOP_SPEED_KMH = 180.0
DEFAULT_ACCEL_0_100_S = 8.5
DEFAULT_FAST_CHARGE_KW = 150.0
DEFAULT_BATTERY_TYPE = 'Lithium-ion'


def load_openai_key() -> Optional[str]:
    # 1) environment
    key = os.environ.get('OPENAI_API_KEY')
    if key:
        return key
    # 2) Streamlit secrets
    try:
        if hasattr(st, 'secrets'):
            k = st.secrets.get('OPENAI_API_KEY')
            if k:
                os.environ['OPENAI_API_KEY'] = k
                return k
    except Exception:
        pass
    # 3) openai_key.txt
    try:
        p = os.path.join(os.getcwd(), 'openai_key.txt')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as fh:
                v = fh.read()
                # strip BOM if present (PowerShell Out-File may add a UTF-8 BOM)
                if v and v[0] == '\ufeff':
                    v = v.lstrip('\ufeff')
                v = v.strip()
                if v:
                    os.environ['OPENAI_API_KEY'] = v
                    return v
    except Exception:
        pass
    # 4) simple .env
    try:
        p = os.path.join(os.getcwd(), '.env')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as fh:
                for line in fh:
                    if '=' not in line or line.strip().startswith('#'):
                        continue
                    name, val = line.split('=', 1)
                    if name.strip() == 'OPENAI_API_KEY':
                        v = val.strip().strip('"\'')
                        if v and v[0] == '\ufeff':
                            v = v.lstrip('\ufeff')
                        if v:
                            os.environ['OPENAI_API_KEY'] = v
                            return v
    except Exception:
        pass
    return None


# Load once (no UI to paste key per user's request)
_ = load_openai_key()


def call_openai(query: str) -> Optional[str]:
    if not OPENAI_AVAILABLE:
        return None
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        return None
    # sanitize key (remove BOM if present)
    try:
        if key and key[0] == '\ufeff':
            key = key.lstrip('\ufeff').strip()
            os.environ['OPENAI_API_KEY'] = key
    except Exception:
        pass
    try:
        # detect installed openai version to avoid triggering migration errors
        ver = None
        try:
            ver = openai.__dict__.get('__version__') if hasattr(openai, '__dict__') else None
        except Exception:
            ver = None
        major = None
        try:
            if ver:
                major = int(str(ver).split('.')[0])
        except Exception:
            major = None

        # If openai version is 1.x or greater, prefer the new OpenAI client and skip legacy attributes
        openai_openai = None
        if major is None or major < 1:
            openai_openai = None
        else:
            try:
                openai_openai = openai.__dict__.get('OpenAI') if hasattr(openai, '__dict__') else None
            except Exception:
                openai_openai = None

        if openai_openai:
            try:
                client = openai_openai()
                resp = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[
                        {"role": "system", "content": "You are a concise assistant for an EV range prediction app."},
                        {"role": "user", "content": query},
                    ],
                    max_tokens=300,
                    temperature=0.2,
                )
                # safe-extract for new client
                try:
                    return resp.choices[0].message.get('content') if hasattr(resp.choices[0].message, 'get') else getattr(resp.choices[0].message, 'content', None)
                except Exception:
                    try:
                        return resp.choices[0].text.strip()
                    except Exception:
                        return None
            except Exception as e:
                print(f"OpenAI call failed: {e}")
                # If we're on openai>=1.x, don't attempt legacy interfaces (they raise migration errors)
                if major is not None and major >= 1:
                    return None

        # Try legacy ChatCompletion (older client versions)
        try:
            chat_api = openai.__dict__.get('ChatCompletion') if hasattr(openai, '__dict__') else None
        except Exception:
            chat_api = None

        if chat_api is not None:
            try:
                resp = chat_api.create(
                    model='gpt-3.5-turbo',
                    messages=[
                        {"role": "system", "content": "You are a concise assistant for an EV range prediction app."},
                        {"role": "user", "content": query},
                    ],
                    max_tokens=300,
                    temperature=0.2,
                )
                try:
                    return resp.choices[0].message.content.strip()
                except Exception:
                    try:
                        return resp.choices[0].text.strip()
                    except Exception:
                        return None
            except Exception as e:
                print(f"OpenAI call failed: {e}")

        # Finally, try older Completion API
        try:
            completion_api = openai.__dict__.get('Completion') if hasattr(openai, '__dict__') else None
        except Exception:
            completion_api = None

        if completion_api is not None:
            try:
                resp = completion_api.create(
                    model='text-davinci-003',
                    prompt=query,
                    max_tokens=300,
                    temperature=0.2,
                )
                try:
                    return resp.choices[0].text.strip()
                except Exception:
                    return None
            except Exception as e:
                print(f"OpenAI call failed: {e}")
                return None

        return None
    except Exception:
        return None


def call_wikipedia(query: str) -> Optional[str]:
    try:
        # use a friendly User-Agent; Wikipedia blocks generic/no-UA requests with 403
        headers = {'User-Agent': 'EV-Range-Explorer/1.0 (https://github.com/; contact: dev@example.com)'}
        # try a few search results (srlimit) to improve chance of hitting a good page
        s = requests.get('https://en.wikipedia.org/w/api.php', params={
            'action': 'query', 'list': 'search', 'srsearch': query, 'format': 'json', 'srlimit': 3
        }, timeout=6, headers=headers)
        s.raise_for_status()
        js = s.json()
        hits = js.get('query', {}).get('search', [])
        if not hits:
            # If no hits and query uses common battery acronyms, try expanding them
            qlow = (query or '').lower()
            if 'nmc' in qlow or 'lfp' in qlow:
                alt = qlow.replace('nmc', 'nickel manganese cobalt').replace('lfp', 'lithium iron phosphate')
                # try again with expanded terms
                s2 = requests.get('https://en.wikipedia.org/w/api.php', params={
                    'action': 'query', 'list': 'search', 'srsearch': alt, 'format': 'json', 'srlimit': 3
                }, timeout=6, headers=headers)
                s2.raise_for_status()
                js2 = s2.json()
                hits = js2.get('query', {}).get('search', [])
                if not hits:
                    return None
            else:
                return None
        # try the first few hits and prefer the one that yields a summary
        for h in hits:
            title = h.get('title')
            try:
                r = requests.get(f'https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.requote_uri(title)}', timeout=6, headers=headers)
                r.raise_for_status()
                jd = r.json()
                text = jd.get('extract') or jd.get('description')
                if text:
                    return text
            except Exception:
                continue
        return None
    except Exception:
        return None


def generate_reply(query: str) -> str:
    q = (query or '').strip()
    if not q:
        return 'Please ask a question about EV range, models, or the dataset.'
    lower = q.lower()
    # small direct answers and common topics
    if any(p in lower for p in ['what is an ev', 'what is ev', 'what is an electric vehicle', 'what is electric vehicle']):
        return 'An electric vehicle (EV) uses electric motors and rechargeable batteries instead of an internal combustion engine.'
    if lower.strip() in ('hi', 'hii', 'hello', 'hey'):
        return 'Hi — ask me about EV range, model prediction, features to include in the CSV, or examples.'
    if 'predict' in lower and ('range' in lower or 'battery' in lower):
        return 'Use the left panel: pick a model, enter feature names & values or upload a CSV, then click Predict.'
    # efficiency questions
    if 'effici' in lower or 'effecien' in lower or 'effeciency' in lower:
        return ("Efficiency for EVs is often expressed in Wh/km (watt-hours per kilometer). "
                "Lower Wh/km means the car is more efficient. You can estimate range from battery size and efficiency: "
                "range_km ≈ battery_capacity_kwh * 1000 / efficiency_wh_per_km. "
                "For example, a 60 kWh battery with 150 Wh/km efficiency gives about 400 km.")
    # range questions
    if 'range' in lower or 'how far' in lower or 'km' in lower or 'miles' in lower:
        return ("EV range depends on battery capacity (kWh), vehicle efficiency (Wh/km), driving style, terrain, and temperature. "
                "Rough formula: range_km ≈ battery_kwh * 1000 / efficiency_wh_per_km. "
                "Typical small EVs: 200–350 km, modern long-range models: 350–600+ km depending on battery and aerodynamics.")
    if any(x in lower for x in ['charging', 'charge', 'fast charger', 'ccs', 'chademo']):
        return ("Charging: AC home chargers are slower (few kW–11 kW). DC fast chargers (50 kW–350+ kW) charge much faster. "
                "Charging speed depends on the car's onboard charger and the charger power. For range planning, consider charging station locations and charge rate.")
    if any(x in lower for x in ['factors', 'what affects', 'why does range vary']):
        return ("Main factors affecting range: battery capacity, vehicle efficiency (Wh/km), speed (highway uses more), payload, temperature (cold reduces usable range), and auxiliary loads like heating/AC.")
    if 'how to improve' in lower or 'improve range' in lower or 'increase range' in lower:
        return ("To improve range: drive smoothly, reduce high speeds, reduce payload, use eco-driving modes, keep tires properly inflated, pre-condition cabin while plugged in, and avoid heavy use of HVAC when possible.")
    # Determine whether OpenAI should be used for this runtime.
    def is_openai_enabled():
        if FORCE_WIKIPEDIA:
            return False
        try:
            # prefer explicit UI toggle when available
            if hasattr(st, 'session_state') and 'allow_openai' in st.session_state:
                return bool(st.session_state.get('allow_openai'))
        except Exception:
            pass
        return OPENAI_AVAILABLE and bool(os.environ.get('OPENAI_API_KEY'))

    # If the user specifically asked about battery chemistries NMC vs LFP,
    # prefer targeted Wikipedia lookups and a concise synthesized comparison.
    if 'nmc' in lower and 'lfp' in lower:
        # expand acronyms
        try:
            lfp = call_wikipedia('Lithium iron phosphate battery') or call_wikipedia('Lithium iron phosphate')
        except Exception:
            lfp = None
        try:
            nmc = call_wikipedia('Nickel manganese cobalt battery') or call_wikipedia('Nickel manganese cobalt oxide battery')
        except Exception:
            nmc = None
        parts = []
        if nmc:
            parts.append(f"NMC (Nickel–Manganese–Cobalt): {nmc}")
        else:
            parts.append("NMC (Nickel–Manganese–Cobalt): generally higher energy density and commonly used where range is important.")
        if lfp:
            parts.append(f"LFP (Lithium Iron Phosphate): {lfp}")
        else:
            parts.append("LFP (Lithium Iron Phosphate): generally safer with longer cycle life but lower energy density compared to NMC.")
        # short comparative summary
        parts.append("Summary: NMC offers higher energy density (better range) but typically higher cost and uses nickel/cobalt; LFP offers better thermal stability, longer cycle life, lower cost, and improved safety at the expense of energy density.")
        return '\n\n'.join(parts)

    # Helper: determine if a question is in-scope for this repo/app
    def is_in_scope(text: str) -> bool:
        s = (text or '').lower()
        inscope_keywords = ['model', 'predict', 'prediction', 'upload', 'csv', 'feature', 'features', 'range', 'which model', 'best model', 'how do i', 'how to', 'left panel']
        return any(k in s for k in inscope_keywords)

    # Directly handle requests that ask to list available models
    if any(kw in lower for kw in ['what models', 'what model', 'which models', 'list models', 'models used', 'models have you used']):
        models = list_model_files()
        if not models:
            return 'No model files (model_*.joblib) were found in the project folder.'
        # present simplified friendly names alongside filenames
        entries = []
        for f in models:
            entries.append(f"{simplify_model_name(f)} ({f})")
        return 'Models available in this project: ' + ', '.join(entries) + '. Use the left panel to run predictions.'

    # Common helpers: CSV format, how to run app, scaling explanation, prediction-changing troubleshooting
    if any(kw in lower for kw in ['how to format', 'format csv', 'csv format', 'example csv', 'sample csv', 'sample input']):
        # Try to provide a CSV header from feature files if present, otherwise suggest a minimal header
        try:
            feature_files = [f for f in os.listdir(os.getcwd()) if f.lower().startswith('features') and f.lower().endswith('.csv')]
            if feature_files:
                df = pd.read_csv(feature_files[0], nrows=1)
                cols = list(df.columns)
                return 'CSV format (example header from %s):\n' % feature_files[0] + ', '.join(cols) + '\n\nProvide a CSV with these column names and one row per vehicle; upload from the right panel.'
        except Exception:
            pass
        sample = 'battery_capacity_kwh,efficiency_wh_per_km,top_speed_kmh,acceleration_0_100_s,fast_charging_power_kw_dc,battery_type_NMC,battery_type_Lithium-ion'
        return 'Example CSV header:\n' + sample + '\nProvide one row per vehicle. Use the left panel to choose a model and upload the CSV to get batch predictions.'

    if any(kw in lower for kw in ['how to run', 'start app', 'run app', 'streamlit run', 'open app']):
        return ('Run the Streamlit app from the project root. Example (PowerShell):\n'
                ".\\.venv\\Scripts\\python.exe -m streamlit run .\\app_clean.py --server.port 8501\n"
                'Then open http://localhost:8501 in your browser.')

    if any(kw in lower for kw in ['why negative', 'negative prediction', 'negative range', 'why is it negative']):
        return ("Some models predict a scaled target (standardized or normalized) so raw outputs can be negative or in 0..1. "
                "The app attempts to inverse-transform outputs using saved scalers or dataset statistics. If you see a negative raw value, the app will try to rescale it to km; check the left panel mapping info or open `models_metadata.json` for per-model scaler info.")

    if any(kw in lower for kw in ['why 0 km', '0 km', 'zero km', 'why 0']):
        return ("A 0 km display usually means the model output was clipped or could not be rescaled to a positive km value. "
                "Try changing input values (battery_capacity_kwh, efficiency_wh_per_km) and confirm the UI shows which manual inputs were mapped to model features. If problems persist, run the 'Inspect model features' script to see the model's expected names.")

    if any(kw in lower for kw in ['prediction not changing', 'predictions not changing', "doesn't change", 'range isnt changing', 'not changing']):
        return ("If predictions don't change when you edit inputs, the model likely expects different feature names. "
                "The app automatically maps common manual fields (battery_capacity_kwh, efficiency_wh_per_km, top_speed_kmh, etc.) into model inputs, but if your model expects a different set, try uploading a CSV with the full header, or run `inspect_model_features.py` to see the model's expected names. The UI will also show the mapping applied.")

    if any(kw in lower for kw in ['which features', 'important features', 'top features', 'feature importance']):
        # try to summarize frequent features from models_features_report.json if present
        try:
            p = os.path.join(os.getcwd(), 'models_features_report.json')
            if os.path.exists(p):
                rep = pd.read_json(p)
                # collect feature lists
                feats = {}
                for item in rep.to_dict(orient='records'):
                    for f in item.get('expected_features_sample') or []:
                        feats[f] = feats.get(f, 0) + 1
                # sort and return top 8
                top = sorted(feats.items(), key=lambda x: -x[1])[:8]
                top_list = ', '.join([t[0] for t in top])
                return 'Common important features across models: ' + top_list + '. Typically battery_capacity_kwh and efficiency_wh_per_km are the most important.'
        except Exception:
            pass
        return 'Typical important features: battery_capacity_kwh, efficiency_wh_per_km, top_speed_kmh, acceleration_0_100_s, fast_charging_power_kw_dc. These usually have the largest effect on predicted range.'

    if any(kw in lower for kw in ['scaled', 'scaler', 'minmax', 'standard', 'inverse_transform', '0.7', '0.8']):
        return ("Many models output scaled targets. The app looks for saved scalers (`scaler_standard.joblib`, `scaler_minmax.joblib`) or per-model metadata in `models_metadata.json` and uses inverse_transform when possible. "
                "If you want exact inverse transforms, ensure the original target scaler file is present in the project and listed in `models_metadata.json`.")
    # Helper: try to determine the best model from local metric files
    def find_best_model_in_repo() -> Optional[str]:
        # look for common metrics files and try to infer a best model
        candidates = ['model_comparison_results.csv', 'metrics_summary_range_km.csv', 'metrics_nested_cv.csv']
        for fn in candidates:
            p = os.path.join(os.getcwd(), fn)
            if os.path.exists(p):
                try:
                    df = pd.read_csv(p)
                    # try columns that indicate score or error
                    metrics_cols = [c for c in df.columns if c.lower() in ('r2', 'score', 'mean_test_score', 'rmse', 'mae', 'mse')]
                    if metrics_cols:
                        # choose the first metric and decide direction
                        col = metrics_cols[0]
                        vals = df[col]
                        # if higher is better (r2, score, mean_test_score)
                        higher_better = col.lower() in ('r2', 'score', 'mean_test_score')
                        try:
                            if higher_better:
                                idx = vals.idxmax()
                            else:
                                idx = vals.idxmin()
                            model_name = None
                            # try common model name columns
                            for candidate in ('model', 'model_name', 'estimator'):
                                if candidate in df.columns:
                                    model_name = str(df.loc[idx, candidate])
                                    break
                            if model_name is None:
                                # fallback: try the first column as name
                                model_name = str(df.iloc[idx, 0])
                            return f"Best model by {col}: {model_name} (value={df.loc[idx, col]})"
                        except Exception:
                            continue
                except Exception:
                    continue
        # no metric files or decision, fall back to listing model files
        models = list_model_files()
        if models:
            return 'Models available in this project: ' + ', '.join(models) + '. Use the left panel to run predictions and compare.'
        return None

    # If the question is in-scope, answer from repo knowledge / rules first.
    if is_in_scope(q):
        # If user asks about features used for prediction, try to discover them
        if 'feature' in lower or 'features' in lower:
            # 1) look for explicit feature files
            feature_files = [f for f in os.listdir(os.getcwd()) if f.lower().startswith('features') and f.lower().endswith('.csv')]
            cols = None
            for ff in feature_files:
                try:
                    df = pd.read_csv(ff, nrows=1)
                    cols = list(df.columns)
                    if cols:
                        return 'Features (from file %s): %s' % (ff, ', '.join(cols))
                except Exception:
                    continue

            # 2) check main dataset cleaned CSV for header
            ds_candidates = ['electric_vehicles_spec_2025_cleaned.csv', 'electric_vehicles_spec_2025.csv.csv', 'electric_vehicles_spec_2025.csv']
            for ds in ds_candidates:
                p = os.path.join(os.getcwd(), ds)
                if os.path.exists(p):
                    try:
                        df = pd.read_csv(p, nrows=1)
                        cols = list(df.columns)
                        if cols:
                            return 'Dataset features (from %s): %s' % (ds, ', '.join(cols))
                    except Exception:
                        continue

            # 3) inspect saved models for feature_names_in_ or similar
            models = list_model_files()
            for m in models:
                try:
                    model = safe_load_model(os.path.join(os.getcwd(), m))
                    if model is None:
                        continue
                    # sklearn estimator feature names
                    fn = getattr(model, 'feature_names_in_', None)
                    if fn is None:
                        # xgboost booster
                        try:
                            booster = getattr(model, 'get_booster', None)
                            if booster:
                                b = model.get_booster()
                                fn = getattr(b, 'feature_names', None)
                        except Exception:
                            fn = None
                    if fn is not None:
                        try:
                            return 'Features used by %s: %s' % (m, ', '.join(list(fn)))
                        except Exception:
                            return 'Features used by %s (count=%s)' % (m, len(fn))
                except Exception:
                    continue

            # 4) fallback message
            return "I couldn't find an explicit feature list in the repo. Try uploading a CSV or point me to a model file to inspect."

        # handle 'best model' directly
        if 'best model' in lower or ('which' in lower and 'model' in lower):
            best = find_best_model_in_repo()
            if best:
                return best
            return "I couldn't find model comparison metrics in the repo. Available model files: " + (', '.join(list_model_files()) or 'none') + ". Use the left panel to test models or upload a CSV to run batch predictions."

        # other in-scope fallbacks: encourage user to use app features
        if 'how' in lower and ('predict' in lower or 'prediction' in lower):
            return 'To predict range: select a model from the left panel, provide feature names and values or upload a CSV, then click Predict. If you need help formatting the CSV, ask for an example.'

        # For other in-scope questions not matched above, give a focused prompt
        return "I can help with models, predictions and dataset inputs — ask about a specific model file, how to format your CSV, or upload a CSV and I will run predictions."

    # Out-of-scope: allow OpenAI (if enabled) then Wikipedia fallback
    if is_openai_enabled():
        out = call_openai(q)
        if out:
            return out
    out = call_wikipedia(q)
    if out:
        return out
    return "I don't know that yet — ask about models, prediction inputs, or upload a CSV."


def list_model_files() -> List[str]:
    try:
        # Find all model_*.joblib files and keep only one (newest) per model family.
        files = [f for f in os.listdir(os.getcwd()) if f.startswith('model_') and f.endswith('.joblib')]
        # Map family -> best_file
        best: dict[str, str] = {}
        best_mtime: dict[str, float] = {}
        for f in files:
            # example filename: model_RandomForest_range_retrained.joblib
            core = f[len('model_'):-len('.joblib')]
            # family heuristics: first token before '_' indicates family (RandomForest, GradientBoosting, KNN, SVR, Ridge, etc.)
            family = core.split('_')[0]
            try:
                mtime = os.path.getmtime(os.path.join(os.getcwd(), f))
            except Exception:
                mtime = 0
            if family not in best or mtime > best_mtime.get(family, 0):
                best[family] = f
                best_mtime[family] = mtime
        # Return sorted list of selected model files (stable ordering)
        return sorted(best.values())
    except Exception:
        return []


def simplify_model_name(filename: str) -> str:
    """Turn a filename like `model_RandomForest_range_retrained.joblib` into
    a simple identifier like `randomforest`.
    """
    try:
        if filename.startswith('model_') and filename.endswith('.joblib'):
            core = filename[len('model_'):-len('.joblib')]
        else:
            core = filename
        # remove common suffixes
        for suf in ('_range_retrained', '_retrained', '_range', '_final', '_v1', '_v2'):
            if core.endswith(suf):
                core = core[: -len(suf)]
        # keep only letters and numbers
        import re

        cleaned = re.sub(r'[^0-9A-Za-z]', '', core)
        return cleaned.lower()
    except Exception:
        return filename


def safe_load_model(path: str):
    try:
        return joblib.load(path)
    except Exception:
        return None


def predict_with_model(model, df: pd.DataFrame):
    try:
        preds = model.predict(df)
        return list(preds)
    except Exception:
        try:
            if hasattr(model, 'predict'):
                return list(model.predict(df))
        except Exception:
            return []


def find_output_scaler() -> Optional[object]:
    """Try to find a saved scaler in the repo to inverse-transform model outputs.

    Looks for common filenames and returns the scaler object or None.
    """
    candidates = ['scaler_minmax.joblib', 'scaler_standard.joblib', 'scaler.joblib']
    for fn in candidates:
        p = os.path.join(os.getcwd(), fn)
        if os.path.exists(p):
            try:
                s = joblib.load(p)
                return s
            except Exception:
                continue
    return None


def inverse_scale_predictions(scaler, preds: List[float]) -> List[float]:
    """Attempt to inverse-transform a list of numeric predictions using the provided scaler.

    Returns a list of floats. If inverse fails, returns the original preds.
    """
    try:
        import numpy as np
        arr = np.array(preds, dtype=float).reshape(-1, 1)
        inv = scaler.inverse_transform(arr)
        # flatten
        return [float(x[0]) for x in inv.tolist()]
    except Exception:
        # Some scalers (custom) may store mean_/scale_ as arrays; try manual inverse for 1-D
        try:
            mean = getattr(scaler, 'mean_', None)
            scale = getattr(scaler, 'scale_', None)
            if mean is not None and scale is not None:
                # if arrays, take first element
                m = float(mean[0]) if hasattr(mean, '__len__') else float(mean)
                s = float(scale[0]) if hasattr(scale, '__len__') else float(scale)
                return [float(p) * s + m for p in preds]
        except Exception:
            pass
    return preds


def compute_target_stats() -> Optional[dict]:
    """Try to find the target column (range) in repo datasets and return stats.

    Returns dict with keys: min, max, mean, std or None if not found.
    """
    # prefer cleaned/original datasets (contain real km values) before any scaled feature files
    candidates = ['electric_vehicles_spec_2025_cleaned.csv', 'electric_vehicles_spec_2025.csv', 'electric_vehicles_spec_2025.csv.csv', 'features_minmax_scaled.csv', 'features_standard_scaled.csv']
    for fn in candidates:
        p = os.path.join(os.getcwd(), fn)
        if os.path.exists(p):
            try:
                df = pd.read_csv(p)
                # try to find a column that looks like the target
                target_cols = [c for c in df.columns if 'range' in c.lower()]
                if not target_cols:
                    # fallback: columns named predicted_range or similar
                    target_cols = [c for c in df.columns if 'predicted' in c.lower() and 'range' in c.lower()]
                if target_cols:
                    col = target_cols[0]
                    ser = pd.to_numeric(df[col], errors='coerce').dropna()
                    if len(ser) == 0:
                        continue
                    # prefer an unscaled target (values larger than 1); if we detect values are in 0..1
                    # treat this candidate as scaled and keep searching for an original dataset first
                    ser_min = float(ser.min())
                    ser_max = float(ser.max())
                    ser_mean = float(ser.mean())
                    ser_std = float(ser.std())
                    if ser_max <= 1.01:
                        # likely a scaled target; skip to next candidate to try find raw km values
                        continue
                    return {'min': ser_min, 'max': ser_max, 'mean': ser_mean, 'std': ser_std}
            except Exception:
                continue
    return None


def load_models_metadata() -> dict:
    """Load per-model metadata (method to rescale outputs)."""
    p = os.path.join(os.getcwd(), 'models_metadata.json')
    if os.path.exists(p):
        try:
            with open(p, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except Exception:
            return {}
    return {}


# simple cache for file-loaded scalers to avoid repeated joblib loads
SCALER_CACHE: dict = {}


def load_file_scaler(ref: str):
    """Load a scaler saved in a joblib file. ref may be 'file.joblib' or 'file.joblib::key'."""
    if not ref:
        return None
    if ref in SCALER_CACHE:
        return SCALER_CACHE[ref]
    parts = ref.split('::', 1)
    fname = parts[0]
    key = parts[1] if len(parts) > 1 else None
    p = os.path.join(os.getcwd(), fname)
    if not os.path.exists(p):
        return None
    try:
        obj = joblib.load(p)
    except Exception:
        return None
    if key and isinstance(obj, dict):
        obj = obj.get(key)
    SCALER_CACHE[ref] = obj
    return obj


def get_model_scaler(model, scaler_ref: str):
    """Attempt to extract a scaler object from a model given a scaler_ref like 'pipeline:step' or 'model_attr:attr'."""
    if not scaler_ref or model is None:
        return None
    try:
        if scaler_ref.startswith('pipeline:'):
            name = scaler_ref.split(':', 1)[1]
            # maybe 'step' or 'step.attr'
            if '.' in name:
                step_name, attr = name.split('.', 1)
            else:
                step_name, attr = name, None
            steps = getattr(model, 'named_steps', {})
            step = steps.get(step_name) if isinstance(steps, dict) else None
            if step is None:
                return None
            if attr:
                return getattr(step, attr, None)
            # prefer common names
            for a in ('scaler_', 'y_scaler', 'target_scaler'):
                if hasattr(step, a):
                    return getattr(step, a)
            if hasattr(step, 'inverse_transform'):
                return step
        if scaler_ref.startswith('model_attr:'):
            attr = scaler_ref.split(':', 1)[1]
            return getattr(model, attr, None)
    except Exception:
        return None
    return None


def find_candidate_scalers() -> List[object]:
    """Search the repo for joblib objects that look like scalers (have inverse_transform).

    Returns list of scaler objects.
    """
    scalers = []
    for fn in os.listdir(os.getcwd()):
        if not fn.endswith('.joblib'):
            continue
        # skip model files
        if fn.startswith('model_'):
            continue
        p = os.path.join(os.getcwd(), fn)
        try:
            obj = joblib.load(p)
        except Exception:
            continue
        if hasattr(obj, 'inverse_transform'):
            scalers.append(obj)
        else:
            # some savers store dicts with scalers
            if isinstance(obj, dict):
                for v in obj.values():
                    if hasattr(v, 'inverse_transform'):
                        scalers.append(v)
    return scalers


def rescale_prediction(pred: float, candidate_scalers: List[object], target_stats: Optional[dict]) -> float:
    """Rescale a single numeric prediction to the target unit (km) using candidates.

    Strategy:
    1) Try each candidate scaler.inverse_transform on [[pred]]; accept result if it falls
       within a reasonable range (if target_stats present: between min-10% and max+10% or >0).
    2) If pred magnitude looks like a normalized [0,1], map linearly to [min,max].
    3) If pred looks standardized (within [-3,3]) and target_stats present, map via mean+pred*std.
    4) Otherwise, return pred (or clipped to >=0).
    """
    import math
    # 1) try scalers
    for s in candidate_scalers:
        try:
            inv = inverse_scale_predictions(s, [pred])
            if inv and isinstance(inv, list):
                v = float(inv[0])
                if target_stats:
                    low = target_stats['min'] - 0.1 * abs(target_stats['min'])
                    high = target_stats['max'] + 0.1 * abs(target_stats['max'])
                    if low <= v <= high and not math.isnan(v):
                        return v
                else:
                    # if scaler produced a positive reasonable number, accept
                    if not math.isnan(v) and v > 0 and abs(v) < 2000:
                        return v
        except Exception:
            continue

    # 2) if normalized [0,1]
    if target_stats and 0.0 <= pred <= 1.0:
        return target_stats['min'] + pred * (target_stats['max'] - target_stats['min'])

    # 3) if standardized approx
    if target_stats and -4.0 <= pred <= 4.0:
        return target_stats['mean'] + pred * target_stats['std']

    # 4) fallback: clip to non-negative
    try:
        p = float(pred)
        return max(0.0, p)
    except Exception:
        return 0.0


def get_model_expected_features(model) -> Optional[List[str]]:
    """Try several strategies to extract the feature names expected by a model.

    Returns a list of feature names or None if unknown.
    """
    try:
        # common sklearn attribute
        if hasattr(model, 'feature_names_in_'):
            return list(getattr(model, 'feature_names_in_'))
    except Exception:
        pass

    # sklearn pipelines: try last estimator
    try:
        if hasattr(model, 'named_steps'):
            steps = list(model.named_steps.values())
            if steps:
                last = steps[-1]
                if hasattr(last, 'feature_names_in_'):
                    return list(getattr(last, 'feature_names_in_'))
    except Exception:
        pass

    # some transformers / estimators expose get_feature_names_out
    try:
        if hasattr(model, 'get_feature_names_out'):
            out = model.get_feature_names_out()
            return list(out)
    except Exception:
        pass

    # xgboost booster
    try:
        if hasattr(model, 'get_booster'):
            b = model.get_booster()
            fn = getattr(b, 'feature_names', None)
            if fn:
                return list(fn)
    except Exception:
        pass

    # try estimator attribute 'feature_names'
    try:
        fn = getattr(model, 'feature_names', None)
        if fn:
            return list(fn)
    except Exception:
        pass

    # fallback: look for a features CSV in the repo
    for cand in ('features_minmax_scaled.csv', 'features_standard_scaled.csv', 'electric_vehicles_spec_2025_cleaned.csv'):
        p = os.path.join(os.getcwd(), cand)
        if os.path.exists(p):
            try:
                return list(pd.read_csv(p, nrows=1).columns)
            except Exception:
                continue
    return None


def compute_feature_means() -> dict:
    """Compute per-column means from available feature CSVs in repo.

    Returns a dict mapping column->mean (floats). If no data available, returns empty dict.
    """
    candidates = ['features_minmax_scaled.csv', 'features_standard_scaled.csv', 'electric_vehicles_spec_2025_cleaned.csv', 'electric_vehicles_spec_2025.csv.csv', 'electric_vehicles_spec_2025.csv']
    for fn in candidates:
        p = os.path.join(os.getcwd(), fn)
        if os.path.exists(p):
            try:
                df = pd.read_csv(p)
                means = {}
                for c in df.columns:
                    try:
                        means[c] = float(df[c].dropna().astype(float).mean())
                    except Exception:
                        # non-numeric -> skip
                        continue
                return means
            except Exception:
                continue
    return {}


def align_row_to_model(model, df_row: pd.DataFrame, default_values: Optional[dict] = None, default_value=0.0):
    """Given a single-row DataFrame df_row, align/pad it to the model's expected features.

    default_values may be a dict mapping feature->fill_value (preferred). If a feature
    is not present in default_values, default_value is used.

    Returns (aligned_df, missing_features_list). If expected features are unknown,
    returns (df_row, []).
    """
    expected = get_model_expected_features(model)
    if not expected:
        return df_row, []
    cols_present = list(df_row.columns)
    missing = [c for c in expected if c not in cols_present]
    # build aligned row dict using default_values when available
    dv = default_values or {}
    aligned = {}

    # helper: attempt to map manual columns to expected feature name by substring/token matching
    def find_manual_for_expected(expected_name):
        # exact match first
        if expected_name in cols_present:
            return expected_name
        # tokenized matching: replace non-alnum with underscore
        en = expected_name.lower().replace('-', '_').replace(' ', '_')
        for col in cols_present:
            c = col.lower().replace('-', '_').replace(' ', '_')
            # direct substring
            if c in en or en in c:
                return col
            # tokens overlap
            en_tokens = set(en.split('_'))
            c_tokens = set(c.split('_'))
            if en_tokens & c_tokens:
                return col
        return None

    for c in expected:
        mapped = find_manual_for_expected(c)
        if mapped and not pd.isna(df_row.iloc[0].get(mapped, None)):
            try:
                aligned[c] = float(df_row.iloc[0][mapped])
                # if mapped, it's not missing
                if c in missing:
                    missing.remove(c)
            except Exception:
                aligned[c] = float(dv.get(c, default_value))
        else:
            # fallback to provided default values
            aligned[c] = float(dv.get(c, default_value))
    aligned_df = pd.DataFrame([aligned])
    return aligned_df, missing


def run_ui():
    st.title('EV Range Explorer — Clean')
    st.markdown('Left: model prediction. Right: assistant (OpenAI if key set, otherwise Wikipedia).')

    models = list_model_files()

    left, right = st.columns([1.4, 1])

    with left:
        st.subheader('Range prediction')
        if not models:
            st.info('No `model_*.joblib` files found in the project folder.')
        # Present simplified model names to the user (map back to filenames internally)
        model_files = models
        display_map = {}
        seen = set()
        options = []
        for f in model_files:
            simple = simplify_model_name(f)
            # ensure uniqueness
            orig = simple
            i = 1
            while simple in seen:
                i += 1
                simple = f"{orig}{i}"
            seen.add(simple)
            display_map[simple] = f
            options.append(simple)

        model_choice_simple = st.selectbox('Model', options=options, index=0 if options else None)
        model_choice = display_map.get(model_choice_simple) if model_choice_simple else None
        if model_choice:
            st.caption(f"Using file: {model_choice}")

        with st.expander('Manual input'):
            st.markdown('Enter important features (defaults provided). Change values and click Predict.')
            # Key features we expose for quick single-row prediction
            battery_capacity_kwh = st.number_input('Battery capacity (kWh)', value=60.0, step=1.0, format="%.2f")
            efficiency_wh_per_km = st.number_input('Efficiency (Wh/km)', value=150.0, step=1.0, format="%.2f")
            top_speed_kmh = st.number_input('Top speed (km/h)', value=180.0, step=1.0, format="%.1f")
            acceleration_0_100_s = st.number_input('0-100 km/h acceleration (s)', value=8.5, step=0.1, format="%.2f")
            fast_charging_power_kw_dc = st.number_input('Fast charging power (kW DC)', value=150.0, step=1.0, format="%.1f")
            battery_type = st.selectbox('Battery type', options=['Lithium-ion', 'Lithium Iron Phosphate (LFP)', 'NMC', 'Other'], index=0)

            if st.button('Predict single row'):
                if not model_choice:
                    st.error('Select a model first')
                else:
                    # build a DataFrame matching exposed features; models may expect additional columns
                    row = {
                        'battery_capacity_kwh': float(battery_capacity_kwh),
                        'efficiency_wh_per_km': float(efficiency_wh_per_km),
                        'top_speed_kmh': float(top_speed_kmh),
                        'acceleration_0_100_s': float(acceleration_0_100_s),
                        'fast_charging_power_kw_dc': float(fast_charging_power_kw_dc),
                        'battery_type_Lithium-ion': 1 if battery_type == 'Lithium-ion' else 0,
                        'battery_type_Lithium Iron Phosphate (LFP)': 1 if battery_type.startswith('Lithium Iron') or 'LFP' in battery_type else 0,
                        'battery_type_NMC': 1 if 'NMC' in battery_type else 0,
                    }
                    df = pd.DataFrame([row])
                    st.write('Input features:')
                    st.write(df)
                    model = safe_load_model(os.path.join(os.getcwd(), model_choice))
                    if model is None:
                        st.error('Failed to load model')
                    else:
                        # auto-align the single-row inputs to the model's expected features
                        try:
                            means = compute_feature_means()
                            aligned_df, missing = align_row_to_model(model, df, default_values=means, default_value=0.0)
                            if missing:
                                # show up to 20 missing columns
                                show = missing if len(missing) <= 20 else missing[:20] + ['...']
                                st.warning(f'Added/padded {len(missing)} missing features filled with dataset mean (where available): {show}')
                            # show which manual inputs were mapped to model features (if any)
                            try:
                                expected = get_model_expected_features(model) or []
                                manual_cols = list(df.columns)
                                mapped = []
                                for expf in expected:
                                    en = expf.lower().replace('-', '_').replace(' ', '_')
                                    for mc in manual_cols:
                                        mc_n = mc.lower().replace('-', '_').replace(' ', '_')
                                        if mc_n in en or en in mc_n or set(en.split('_')) & set(mc_n.split('_')):
                                            mapped.append((mc, expf))
                                            break
                                if mapped:
                                    st.info(f'Mapped manual inputs to model features: {mapped}')
                            except Exception:
                                pass
                        except Exception as e:
                            aligned_df = df
                            st.info(f'Could not auto-align inputs to model: {e}')

                        with st.spinner('Predicting...'):
                            preds = predict_with_model(model, aligned_df)
                        if preds:
                            # attempt principled rescaling using found scalers and dataset stats
                            candidate_scalers = find_candidate_scalers()
                            target_stats = compute_target_stats()
                            try:
                                num_raw = float(preds[0])
                            except Exception:
                                num_raw = None
                            final_val = None
                            # consult per-model metadata if available for deterministic rescaling
                            models_meta = load_models_metadata()
                            model_meta = models_meta.get(os.path.basename(model_choice), {}) if models_meta else {}
                            if num_raw is not None and model_meta:
                                method = model_meta.get('method')
                                if method == 'raw_km':
                                    final_val = float(num_raw)
                                elif method == 'normalized':
                                    if target_stats:
                                        final_val = target_stats['min'] + float(num_raw) * (target_stats['max'] - target_stats['min'])
                                    else:
                                        final_val = float(num_raw)
                                elif method == 'standardized':
                                    if target_stats:
                                        final_val = target_stats['mean'] + float(num_raw) * target_stats['std']
                                    else:
                                        final_val = float(num_raw)
                                elif method == 'use_file_scaler':
                                    ref = model_meta.get('scaler_ref')
                                    scaler = load_file_scaler(str(ref)) if ref is not None else None
                                    if scaler is not None:
                                        try:
                                            inv = inverse_scale_predictions(scaler, [num_raw])
                                            if inv:
                                                final_val = float(inv[0])
                                        except Exception:
                                            final_val = None
                                    if final_val is None:
                                        final_val = rescale_prediction(num_raw, candidate_scalers, target_stats)
                                elif method == 'use_model_scaler':
                                    ref = model_meta.get('scaler_ref')
                                    scaler = get_model_scaler(model, str(ref)) if ref is not None else None
                                    if scaler is not None:
                                        try:
                                            inv = inverse_scale_predictions(scaler, [num_raw])
                                            if inv:
                                                final_val = float(inv[0])
                                        except Exception:
                                            final_val = None
                                    if final_val is None:
                                        final_val = rescale_prediction(num_raw, candidate_scalers, target_stats)
                                else:
                                    # fallback: use existing rescale attempt
                                    final_val = rescale_prediction(num_raw, candidate_scalers, target_stats)
                            else:
                                if num_raw is not None:
                                    final_val = rescale_prediction(num_raw, candidate_scalers, target_stats)
                            if final_val is None:
                                # fallback to clipping
                                try:
                                    final_val = max(0.0, float(preds[0]))
                                except Exception:
                                    final_val = 0.0
                            try:
                                st.success(f"Predicted range: {final_val:.0f} km")
                            except Exception:
                                st.success(str(final_val) + ' km')
                        else:
                            st.error('Prediction failed — model may expect different features. Try uploading a CSV or inspect the model feature names.')

        st.markdown('---')
        st.subheader('Batch (CSV)')
        uploaded = st.file_uploader('Upload CSV', type=['csv'])
        if uploaded is not None and model_choice:
            try:
                df = pd.read_csv(uploaded)
                st.write(df.head())
                model = safe_load_model(os.path.join(os.getcwd(), model_choice))
                if model is None:
                    st.error('Failed to load model')
                else:
                    with st.spinner('Predicting CSV...'):
                        preds = predict_with_model(model, df)
                        if preds:
                            df['predicted_range'] = preds
                            st.write(df.head())
                            st.download_button('Download CSV with predictions', df.to_csv(index=False).encode('utf-8'), file_name='predictions.csv')
                        else:
                            st.error('Prediction failed for uploaded CSV')
            except Exception as e:
                st.error(f'Failed to read CSV: {e}')

    with right:
        st.subheader('Assistant')
        # (info banners removed to reduce visual noise)

        # keep chat history in a different session key than any widget id
        if 'chat_history' not in st.session_state:
            st.session_state['chat_history'] = [('system', 'Assistant ready. Ask about EVs, models, or predictions.')]
        # remove any old/conflicting 'chat' key left from previous runs
        if 'chat' in st.session_state:
            try:
                del st.session_state['chat']
            except Exception:
                pass

        # single placeholder used for all chat renderings so we clear previous output
        chat_placeholder = st.empty()

        def render_chat():
            # clear and re-render into the placeholder to avoid duplicate content
            with chat_placeholder.container():
                for role, txt in st.session_state['chat_history'][-40:]:
                    if role == 'user':
                        st.markdown(f'**You:** {txt}')
                    elif role == 'bot':
                        st.markdown(f'**Assistant:** {txt}')
                    else:
                        st.write(txt)

        # guard to prevent re-entrancy/duplicate processing
        if 'chat_processing' not in st.session_state:
            st.session_state['chat_processing'] = False

        def process_user_message(user_msg: str):
            """Append the user message and generate a reply, avoiding duplicates and re-entrancy."""
            if not user_msg:
                return
            # avoid duplicate consecutive user messages
            if st.session_state['chat_history'] and st.session_state['chat_history'][-1] == ('user', user_msg):
                return
            # avoid concurrent processing
            if st.session_state.get('chat_processing'):
                return
            st.session_state['chat_processing'] = True
            try:
                st.session_state['chat_history'].append(('user', user_msg))
                st.session_state['chat_history'].append(('bot', 'Thinking...'))
                render_chat()
                with st.spinner('Assistant is thinking...'):
                    reply = generate_reply(user_msg)
                    # tiny delay so spinner is visible in very fast cases
                    time.sleep(0.15)
                # replace placeholder
                if st.session_state['chat_history'] and st.session_state['chat_history'][-1][1] == 'Thinking...':
                    st.session_state['chat_history'][-1] = ('bot', reply)
                else:
                    st.session_state['chat_history'].append(('bot', reply))
                render_chat()
            finally:
                st.session_state['chat_processing'] = False

        render_chat()

        # use a different form id so it doesn't conflict with session keys
        with st.form('chat_form'):
            user_msg = st.text_input('Message', '')
            send = st.form_submit_button('Send')

        if send and user_msg:
            process_user_message(user_msg)

        st.markdown('---')
        st.markdown('Helpful prompts:')
        if st.button('What is an EV?'):
            process_user_message('What is an EV?')
        if st.button('How to predict range?'):
            process_user_message('How do I predict range using this app?')


if __name__ == '__main__':
    run_ui()
