import os
import time
import joblib
import pandas as pd
import requests
import streamlit as st

try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False


st.set_page_config(page_title='EV Range Explorer', layout='wide')


def load_openai_key():
    k = os.environ.get('OPENAI_API_KEY')
    if k:
        return k
    try:
        if hasattr(st, 'secrets'):
            v = st.secrets.get('OPENAI_API_KEY')
            if v:
                os.environ['OPENAI_API_KEY'] = v
                return v
    except Exception:
        pass
    try:
        p = os.path.join(os.getcwd(), 'openai_key.txt')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as fh:
                v = fh.read().strip()
                if v:
                    os.environ['OPENAI_API_KEY'] = v
                    return v
    except Exception:
        pass
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
                        if v:
                            os.environ['OPENAI_API_KEY'] = v
                            import os
                            import time
                            import joblib
                            import pandas as pd
                            import requests
                            import streamlit as st

                            try:
                                import openai
                                OPENAI_AVAILABLE = True
                            except Exception:
                                OPENAI_AVAILABLE = False


                            st.set_page_config(page_title='EV Range Explorer', layout='wide')


                            def load_openai_key():
                                k = os.environ.get('OPENAI_API_KEY')
                                if k:
                                    return k
                                try:
                                    if hasattr(st, 'secrets'):
                                        v = st.secrets.get('OPENAI_API_KEY')
                                        if v:
                                            os.environ['OPENAI_API_KEY'] = v
                                            return v
                                except Exception:
                                    pass
                                try:
                                    p = os.path.join(os.getcwd(), 'openai_key.txt')
                                    if os.path.exists(p):
                                        with open(p, 'r', encoding='utf-8') as fh:
                                            v = fh.read().strip()
                                            if v:
                                                os.environ['OPENAI_API_KEY'] = v
                                                return v
                                except Exception:
                                    pass
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
                                                    if v:
                                                        os.environ['OPENAI_API_KEY'] = v
                                                        return v
                                except Exception:
                                    pass
                                return None


                            _ = load_openai_key()


                            def call_openai(query: str):
                                if not OPENAI_AVAILABLE:
                                    return None
                                key = os.environ.get('OPENAI_API_KEY')
                                if not key:
                                    return None
                                try:
                                    openai.api_key = key
                                    resp = openai.ChatCompletion.create(
                                        model='gpt-3.5-turbo',
                                        messages=[
                                            {'role': 'system', 'content': 'You are an assistant for an EV range prediction app. Keep answers concise.'},
                                            {'role': 'user', 'content': query},
                                        ],
                                        max_tokens=300,
                                        temperature=0.2,
                                    )
                                    return resp.choices[0].message.content.strip()
                                except Exception:
                                    return None


                            def call_wikipedia(query: str):
                                try:
                                    s = requests.get('https://en.wikipedia.org/w/api.php', params={
                                        'action': 'query', 'list': 'search', 'srsearch': query, 'format': 'json', 'srlimit': 1
                                    }, timeout=6)
                                    s.raise_for_status()
                                    js = s.json()
                                    hits = js.get('query', {}).get('search', [])
                                    if not hits:
                                        return None
                                    title = hits[0]['title']
                                    r = requests.get(f'https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.requote_uri(title)}', timeout=6)
                                    r.raise_for_status()
                                    jd = r.json()
                                    return jd.get('extract') or jd.get('description')
                                except Exception:
                                    return None


                            def generate_reply(query: str) -> str:
                                q = (query or '').strip()
                                if not q:
                                    return 'Please ask a question about EV range, models, or the dataset.'
                                lower = q.lower()
                                if 'what is an ev' in lower or 'what is ev' in lower or ('electric vehicle' in lower and 'what' in lower):
                                    return 'An electric vehicle (EV) uses electric motors powered by rechargeable batteries instead of an internal combustion engine.'
                                if 'predict' in lower and ('range' in lower or 'battery' in lower):
                                    return 'Use the left panel: choose a model, provide battery_capacity_kwh and efficiency_wh_per_km (or upload a CSV), then click Predict.'
                                out = call_openai(q)
                                if out:
                                    return out
                                out = call_wikipedia(q)
                                if out:
                                    return out
                                return "I don't know that yet — ask about models, prediction inputs, or upload a CSV."


                            def list_model_files():
                                try:
                                    return sorted([f for f in os.listdir(os.getcwd()) if f.startswith('model_') and f.endswith('.joblib')])
                                except Exception:
                                    return []


                            def safe_load_model(path: str):
                                try:
                                    return joblib.load(path)
                                except Exception:
                                    return None


                            def predict_with_model(model, df):
                                try:
                                    preds = model.predict(df)
                                    return list(preds)
                                except Exception:
                                    try:
                                        if hasattr(model, 'predict'):
                                            return list(model.predict(df))
                                    except Exception:
                                        return []


                            def main():
                                st.title('EV Range Explorer — Rebuilt')
                                st.markdown('Minimal clean rebuild: left = prediction, right = assistant (OpenAI if available, Wikipedia fallback).')

                                models = list_model_files()

                                left, right = st.columns([1.3, 1])

                                with left:
                                    st.subheader('Range Prediction')
                                    if not models:
                                        st.info('No model_*.joblib files found in the project folder. Prediction panel is disabled.')
                                    model_choice = st.selectbox('Choose a model file', options=models, index=0 if models else None)

                                    with st.expander('Manual single-row prediction'):
                                        cols = st.text_input('Feature names (comma separated)', value='battery_capacity_kwh, efficiency_wh_per_km')
                                        vals = st.text_input('Values (comma separated, same order)', value='60,150')
                                        if st.button('Predict single row'):
                                            if not model_choice:
                                                st.error('No model selected')
                                            else:
                                                features = [c.strip() for c in cols.split(',') if c.strip()]
                                                values = [v.strip() for v in vals.split(',') if v.strip()]
                                                if len(features) != len(values):
                                                    st.error('Feature and value counts do not match')
                                                else:
                                                    try:
                                                        df = pd.DataFrame([dict(zip(features, [float(x) for x in values]))])
                                                    except Exception as e:
                                                        st.error(f'Could not parse values: {e}')
                                                        df = None
                                                    if df is not None:
                                                        model = safe_load_model(os.path.join(os.getcwd(), model_choice))
                                                        if model is None:
                                                            st.error('Failed to load model file')
                                                        else:
                                                            with st.spinner('Predicting...'):
                                                                preds = predict_with_model(model, df)
                                                                if preds:
                                                                    st.success(f'Predicted range(s): {preds}')
                                                                else:
                                                                    st.error('Prediction failed. Model may expect different features')

                                    st.markdown('---')
                                    st.subheader('Batch predict (CSV upload)')
                                    uploaded = st.file_uploader('Upload CSV with feature columns matching the model', type=['csv'])
                                    if uploaded is not None and model_choice:
                                        try:
                                            df = pd.read_csv(uploaded)
                                            st.write(df.head())
                                            model = safe_load_model(os.path.join(os.getcwd(), model_choice))
                                            if model is None:
                                                st.error('Failed to load model file')
                                            else:
                                                with st.spinner('Predicting...'):
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
                                    st.subheader('Assistant (Chat)')
                                    if OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
                                        st.success('OpenAI available — using ChatCompletion for answers')
                                    else:
                                        st.info('OpenAI not available / key missing — falling back to Wikipedia')

                                    if 'chat' not in st.session_state:
                                        st.session_state['chat'] = [('system', 'Assistant ready. Ask about models, predictions, or EV topics.')]

                                    # render chat
                                    for role, text in st.session_state['chat']:
                                        if role == 'user':
                                            st.markdown(f'**You:** {text}')
                                        elif role == 'bot':
                                            st.markdown(f'**Assistant:** {text}')
                                        else:
                                            st.write(text)

                                    # Chat input
                                    user_input = st.text_input('Message', key='user_input')
                                    if st.button('Send') and st.session_state.get('user_input'):
                                        ui = st.session_state.get('user_input')
                                        st.session_state['chat'].append(('user', ui))
                                        # placeholder
                                        st.session_state['chat'].append(('bot', 'Thinking...'))
                                        # synchronous reply
                                        with st.spinner('Assistant is thinking...'):
                                            reply = generate_reply(ui)
                                            time.sleep(0.1)
                                        # replace placeholder
                                        if st.session_state['chat'] and st.session_state['chat'][-1][1] == 'Thinking...':
                                            st.session_state['chat'][-1] = ('bot', reply)
                                        else:
                                            st.session_state['chat'].append(('bot', reply))


                            if __name__ == '__main__':
                                main()
    # .env simple parse
    try:
        p = os.path.join(ROOT, '.env')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as fh:
                for line in fh:
                    if '=' not in line:
                        continue
                    kname, val = line.split('=', 1)
                    if kname.strip() == 'OPENAI_API_KEY':
                        v = val.strip().strip('"\'')
                        if v:
                            os.environ['OPENAI_API_KEY'] = v
                            return v
    except Exception:
        pass
    return None


_ = load_openai_key()


def call_openai(query: str) -> Optional[str]:
    if not OPENAI_AVAILABLE:
        return None
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        return None
    try:
        openai.api_key = key
        resp = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {"role": "system", "content": "You are an assistant for an EV range prediction app. Be concise and domain-focused."},
                {"role": "user", "content": query},
            ],
            max_tokens=300,
            temperature=0.2,
        )
        try:
            return resp.choices[0].message.content.strip()
        except Exception:
            return None
    except Exception:
        return None


def call_wikipedia(query: str) -> Optional[str]:
    try:
        s = requests.get('https://en.wikipedia.org/w/api.php', params={
            'action': 'query', 'list': 'search', 'srsearch': query, 'format': 'json', 'srlimit': 1
        }, timeout=6)
        s.raise_for_status()
        js = s.json()
        hits = js.get('query', {}).get('search', [])
        if not hits:
            return None
        title = hits[0]['title']
        r = requests.get(f'https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.requote_uri(title)}', timeout=6)
        r.raise_for_status()
        jd = r.json()
        return jd.get('extract') or jd.get('description')
    except Exception:
        return None


def generate_reply(query: str) -> str:
    q = (query or '').strip()
    if not q:
        return 'Please ask a question about EVs, models, or predictions.'
    lower = q.lower()
    # Small rule answers
    if 'what is an ev' in lower or 'what is ev' in lower or ('electric vehicle' in lower and 'what' in lower):
        return 'An electric vehicle (EV) uses electric motors powered by rechargeable batteries instead of an internal combustion engine.'
    if 'predict' in lower and ('range' in lower or 'battery' in lower):
        return 'Use the left panel: choose a model, provide features (battery_capacity_kwh, efficiency_wh_per_km, etc.) or upload a CSV, then click Predict.'

    # Domain gating: refuse unrelated personal/medical/legal topics
    allowed_keywords = ('ev vehicle model predict range battery charging efficiency features dataset csv train retrain')
    if not any(k in lower for k in allowed_keywords.split()):
        return 'This assistant is focused on EVs, models, datasets, and predictions. Please ask a related question.'

    # Try OpenAI then fallback to Wikipedia
    out = call_openai(q)
    if out:
        return out
    out = call_wikipedia(q)
    if out:
        return out
    return "I don't know that yet — ask about model usage, inputs, or upload a CSV for batch prediction."


def list_model_files() -> List[str]:
    try:
        return sorted([f for f in os.listdir(ROOT) if f.startswith('model_') and f.endswith('.joblib')])
    except Exception:
        return []


def safe_load_model(path: str):
    try:
        return joblib.load(path)
    except Exception:
        return None


def predict_with_model(model, df: pd.DataFrame) -> List[float]:
    try:
        pred = model.predict(df)
        return list(map(float, pred))
    except Exception:
        try:
            return list(map(float, model.predict(df)))
        except Exception:
            return []


def main():
    st.set_page_config(page_title='EV Range Explorer', layout='wide')
    st.title('EV Range Explorer — Clean Rebuild')
    st.write('Left: model-based predictions. Right: EV assistant (OpenAI + Wikipedia fallback).')

    models = list_model_files()
    left, right = st.columns([1.5, 1])

    with left:
        st.header('Predict Range')
        if not models:
            st.warning('No model_*.joblib files found. Place a model file in the project root to enable predictions.')
        model_choice = st.selectbox('Model file', options=models, index=0 if models else None)

        with st.form('single'):
            st.subheader('Single-row prediction')
            cols = st.text_input('Feature names (comma separated)', value='battery_capacity_kwh, efficiency_wh_per_km')
            vals = st.text_input('Values (comma separated)', value='75,180')
            run = st.form_submit_button('Predict')
        if run and model_choice:
            feats = [c.strip() for c in cols.split(',') if c.strip()]
            vs = [v.strip() for v in vals.split(',') if v.strip()]
            if len(feats) != len(vs):
                st.error('Feature names and values must match in length.')
            else:
                try:
                    row = {k: float(v) for k, v in zip(feats, vs)}
                    df = pd.DataFrame([row])
                except Exception:
                    st.error('Could not parse numeric values.')
                    df = None
                if df is not None:
                    model = safe_load_model(os.path.join(ROOT, model_choice))
                    if model is None:
                        st.error('Failed to load selected model.')
                    else:
                        with st.spinner('Predicting...'):
                            preds = predict_with_model(model, df)
                            if preds:
                                st.success(f'Predicted range(s): {preds}')
                            else:
                                st.error('Prediction failed. Model may expect different feature names.')

        st.markdown('---')
        st.subheader('Batch predict (CSV)')
        uploaded = st.file_uploader('Upload CSV', type=['csv'])
        if uploaded is not None and model_choice:
            try:
                df = pd.read_csv(uploaded)
                st.write(df.head())
                model = safe_load_model(os.path.join(ROOT, model_choice))
                if model is None:
                    st.error('Failed to load selected model.')
                else:
                    with st.spinner('Predicting on CSV...'):
                        preds = predict_with_model(model, df)
                        if preds:
                            df['predicted_range'] = preds
                            st.write(df.head())
                            st.download_button('Download predictions', df.to_csv(index=False).encode('utf-8'), file_name='predictions.csv')
                        else:
                            st.error('Prediction failed. Model may expect different feature columns.')
            except Exception as e:
                st.error(f'Failed to read uploaded CSV: {e}')

    with right:
        st.header('Assistant')
        if OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
            st.info('Using OpenAI for answers (key loaded from environment/secrets/file).')
        else:
            st.info('OpenAI not available or key not found — falling back to Wikipedia for general questions.')

        if 'chat' not in st.session_state:
            st.session_state['chat'] = [('system', 'Assistant ready. Ask about the project, models, or EV topics.')]

        def render_chat():
            for role, txt in st.session_state['chat'][-20:]:
                if role == 'user':
                    st.markdown(f'**You:** {txt}')
                elif role == 'bot':
                    st.markdown(f'**Assistant:** {txt}')
                else:
                    st.markdown(f'_{txt}_')

        render_chat()

        with st.form('chat_form'):
            user_input = st.text_input('Message', key='chat_input')
            sent = st.form_submit_button('Send')

        if sent and user_input:
            # append user message and a visible placeholder
            st.session_state['chat'].append(('user', user_input))
            st.session_state['chat'].append(('bot', 'Thinking...'))
            render_chat()
            # synchronous processing with spinner ensures one-click behavior
            with st.spinner('Assistant is thinking...'):
                reply = generate_reply(user_input)
                # tiny sleep to make spinner visible in fast responses
                time.sleep(0.15)

            # replace last placeholder
            try:
                if st.session_state['chat'] and st.session_state['chat'][-1][1] == 'Thinking...':
                    st.session_state['chat'][-1] = ('bot', reply)
                else:
                    st.session_state['chat'].append(('bot', reply))
            except Exception:
                st.session_state['chat'].append(('bot', reply))

            render_chat()


if __name__ == '__main__':
    main()
import os
import time
from typing import List

import joblib
import pandas as pd
import requests
import streamlit as st

try:
        else:
            st.info('OpenAI not available or key not found — the assistant will fall back to Wikipedia for general questions.')

        if 'chat' not in st.session_state:
            st.session_state['chat'] = [('system', 'Assistant ready. Ask about the project, models, or EV topics.')]

        chat_box = st.container()

        def render_chat():
            with chat_box:
                for role, text in st.session_state['chat']:
                    if role == 'user':
                        st.markdown(f"**You:** {text}")
                    elif role == 'bot':
                        st.markdown(f"**Assistant:** {text}")
                    else:
                        st.markdown(f"_{text}_")

        render_chat()

        with st.form('chat_form'):
            user_input = st.text_input('Message', '')
            send = st.form_submit_button('Send')

        if send and user_input:
            st.session_state['chat'].append(('user', user_input))
            st.session_state['chat'].append(('bot', 'Thinking...'))
            render_chat()

            with st.spinner('Assistant is thinking...'):
                reply = generate_reply(user_input)
                time.sleep(0.2)

            if st.session_state['chat'] and st.session_state['chat'][-1][1] == 'Thinking...':
                import os
                import time
                from typing import List

                import joblib
                import pandas as pd
                import requests
                import streamlit as st

                try:
                    import openai
                    OPENAI_AVAILABLE = True
                except Exception:
                    OPENAI_AVAILABLE = False


                st.set_page_config(page_title='EV Range Explorer', layout='wide')


                def load_openai_key():
                    key = os.environ.get('OPENAI_API_KEY')
                    if key:
                        return key
                    try:
                        if hasattr(st, 'secrets'):
                            k = st.secrets.get('OPENAI_API_KEY')
                            if k:
                                os.environ['OPENAI_API_KEY'] = k
                                return k
                    except Exception:
                        pass
                    try:
                        p = os.path.join(os.getcwd(), 'openai_key.txt')
                        if os.path.exists(p):
                            with open(p, 'r', encoding='utf-8') as fh:
                                v = fh.read().strip()
                                if v:
                                    os.environ['OPENAI_API_KEY'] = v
                                    return v
                    except Exception:
                        pass
                    try:
                        p = os.path.join(os.getcwd(), '.env')
                        if os.path.exists(p):
                            with open(p, 'r', encoding='utf-8') as fh:
                                for line in fh:
                                    if '=' in line and line.strip() and not line.strip().startswith('#'):
                                        kname, val = line.split('=', 1)
                                        if kname.strip() == 'OPENAI_API_KEY':
                                            v = val.strip().strip('"\'')
                                            if v:
                                                os.environ['OPENAI_API_KEY'] = v
                                                return v
                    except Exception:
                        pass
                    return None


                _ = load_openai_key()


                def call_openai(query):
                    if not OPENAI_AVAILABLE:
                        return None
                    key = os.environ.get('OPENAI_API_KEY')
                    if not key:
                        return None
                    try:
                        openai.api_key = key
                        resp = openai.ChatCompletion.create(
                            model='gpt-3.5-turbo',
                            messages=[
                                {"role": "system", "content": "You are an assistant for an EV range prediction app. Be concise."},
                                {"role": "user", "content": query},
                            ],
                            max_tokens=300,
                            temperature=0.2,
                        )
                        return resp.choices[0].message.content.strip()
                    except Exception:
                        return None


                def call_wikipedia(query):
                    try:
                        s = requests.get('https://en.wikipedia.org/w/api.php', params={
                            'action': 'query', 'list': 'search', 'srsearch': query, 'format': 'json', 'srlimit': 1
                        }, timeout=6)
                        s.raise_for_status()
                        js = s.json()
                        hits = js.get('query', {}).get('search', [])
                        if not hits:
                            return None
                        title = hits[0]['title']
                        r = requests.get(f'https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.requote_uri(title)}', timeout=6)
                        r.raise_for_status()
                        jd = r.json()
                        return jd.get('extract') or jd.get('description')
                    except Exception:
                        return None


                def generate_reply(query):
                    q = (query or '').strip()
                    if not q:
                        return "Please ask a question about EV range, models, or the dataset."
                    lower = q.lower()
                    if 'what is an ev' in lower or 'what is ev' in lower or ('electric vehicle' in lower and 'what' in lower):
                        return 'An electric vehicle (EV) uses electric motors powered by rechargeable batteries instead of a gasoline engine.'
                    if 'predict' in lower and ('range' in lower or 'battery' in lower):
                        return 'Use the left panel: choose a model, provide battery_capacity_kwh and efficiency_wh_per_km (or upload a CSV), then click Predict.'
                    out = call_openai(q)
                    if out:
                        return out
                    out = call_wikipedia(q)
                    if out:
                        return out
                    return "I don't know that yet — ask about models, prediction inputs, or upload a CSV."


                def list_model_files():
                    try:
                        return sorted([f for f in os.listdir(os.getcwd()) if f.startswith('model_') and f.endswith('.joblib')])
                    except Exception:
                        return []


                def safe_load_model(path):
                    try:
                        return joblib.load(path)
                    except Exception:
                        return None


                def predict_with_model(model, df):
                    try:
                        preds = model.predict(df)
                        return list(preds)
                    except Exception:
                        try:
                            if hasattr(model, 'predict'):
                                return list(model.predict(df))
                        except Exception:
                            return []


                def main():
                    st.title('EV Range Explorer — Rebuilt')
                    st.markdown('A minimal, robust rebuild that uses OpenAI (if available) for chat and existing joblib models for range prediction.')

                    models = list_model_files()

                    left, right = st.columns([1.2, 1])

                    with left:
                        st.subheader('Range Prediction')
                        if not models:
                            st.info('No model_*.joblib files found in the project folder. Prediction panel is disabled.')
                        model_choice = st.selectbox('Choose a model file', options=models, index=0 if models else None)

                        with st.form('manual_input'):
                            st.markdown('Provide manual input features (enter columns expected by your model).')
                            cols_text = st.text_area('Feature names (comma separated)', value='battery_capacity_kwh, efficiency_wh_per_km')
                            values_text = st.text_area('Values (comma separated, same order)', value='60,150')
                            submit_manual = st.form_submit_button('Predict (single row)')

                        if submit_manual and model_choice:
                            features = [c.strip() for c in cols_text.split(',') if c.strip()]
                            vals = [v.strip() for v in values_text.split(',') if v.strip()]
                            if len(features) != len(vals):
                                st.error('Number of features and values must match.')
                            else:
                                try:
                                    df = pd.DataFrame([dict(zip(features, [float(x) for x in vals]))])
                                except Exception:
                                    st.error('Could not parse numeric values; ensure values are numeric and comma-separated.')
                                    df = None
                                if df is not None:
                                    model = safe_load_model(os.path.join(os.getcwd(), model_choice))
                                    if model is None:
                                        st.error('Failed to load model file.')
                                    else:
                                        with st.spinner('Predicting...'):
                                            preds = predict_with_model(model, df)
                                            if preds:
                                                st.success(f'Predicted range(s): {preds}')
                                            else:
                                                st.error('Prediction failed. The model may expect different features.')

                        st.markdown('---')
                        st.subheader('Batch predict (CSV upload)')
                        uploaded = st.file_uploader('Upload CSV with feature columns matching the model', type=['csv'])
                        if uploaded is not None and model_choice:
                            try:
                                df = pd.read_csv(uploaded)
                                st.write('Uploaded data preview:', df.head())
                                model = safe_load_model(os.path.join(os.getcwd(), model_choice))
                                if model is None:
                                    st.error('Failed to load model file.')
                                else:
                                    with st.spinner('Predicting on CSV...'):
                                        preds = predict_with_model(model, df)
                                        if preds:
                                            df['predicted_range'] = preds
                                            st.write(df.head())
                                            st.download_button('Download with predictions (CSV)', df.to_csv(index=False).encode('utf-8'), file_name='predictions.csv')
                                        else:
                                            st.error('Prediction failed for uploaded CSV. Model may expect different features.')
                            except Exception as e:
                                st.error(f'Failed to read uploaded CSV: {e}')

                    with right:
                        st.subheader('Assistant (Chat)')
                        if OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
                            st.info('OpenAI is available and will be used for general questions. (Key loaded from environment/secrets/file).')
                        else:
                            st.info('OpenAI not available or key not found — the assistant will fall back to Wikipedia for general questions.')

                        if 'chat' not in st.session_state:
                            st.session_state['chat'] = [('system', 'Assistant ready. Ask about the project, models, or EV topics.')]

                        chat_box = st.container()

                        def render_chat():
                            with chat_box:
                                for role, text in st.session_state['chat']:
                                    if role == 'user':
                                        st.markdown(f"**You:** {text}")
                                    elif role == 'bot':
                                        st.markdown(f"**Assistant:** {text}")
                                    else:
                                        st.markdown(f"_{text}_")

                        render_chat()

                        with st.form('chat_form'):
                            user_input = st.text_input('Message', '')
                            send = st.form_submit_button('Send')

                        if send and user_input:
                            st.session_state['chat'].append(('user', user_input))
                            st.session_state['chat'].append(('bot', 'Thinking...'))
                            render_chat()

                            with st.spinner('Assistant is thinking...'):
                                reply = generate_reply(user_input)
                                time.sleep(0.2)

                            if st.session_state['chat'] and st.session_state['chat'][-1][1] == 'Thinking...':
                                st.session_state['chat'][-1] = ('bot', reply)
                            else:
                                st.session_state['chat'].append(('bot', reply))

                            render_chat()

                        st.markdown('---')
                        st.markdown('Helpful prompts:')
                        if st.button('What is an EV?'):
                            st.session_state['chat'].append(('user', 'What is an EV?'))
                        if st.button('How to predict range?'):
                            st.session_state['chat'].append(('user', 'How do I predict range using this app?'))


                if __name__ == '__main__':
                    main()
            render_chat()

            # generate reply synchronously (ensures one-click behavior)
            with st.spinner('Assistant is thinking...'):
                reply = generate_reply(user_input)
                # small delay to make spinner visible (optional)
                time.sleep(0.3)
            # replace last placeholder
            if st.session_state['chat'] and st.session_state['chat'][-1][1] == 'Thinking...':
                st.session_state['chat'][-1] = ('bot', reply)
            else:
                st.session_state['chat'].append(('bot', reply))

            # re-render chat after reply is ready
            render_chat()

        st.markdown('---')
        st.markdown('Helpful prompts:')
        st.button('What is an EV?', on_click=lambda: st.session_state['chat'].append(('user', 'What is an EV?')))
        st.button('How to predict range?', on_click=lambda: st.session_state['chat'].append(('user', 'How do I predict range using this app?')))


if __name__ == '__main__':
    main()
import os
import re
import os
import json
import joblib
import pandas as pd
import streamlit as st
import requests
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False


st.set_page_config(page_title='EV Range Explorer (New)', layout='wide')
# --- Styling for chat bubbles and cards (light & dark) ---
_CHAT_CSS_LIGHT = """
<style>
/* Theme variables (light) */
:root {
    --bg: #ffffff;
    --card: linear-gradient(135deg, #f8fafc, #ffffff);
    --primary: #0ea5a4;
    --muted: #6c757d;
    --text: #0b1420;
}
.ev-header { display:flex; align-items:center; gap:14px; margin-bottom:6px }
/* Give the page container a little horizontal padding so content (logo) isn't flush against edges */
div.block-container { padding-top: 0.5rem; padding-left:12px; padding-right:12px; max-width:1100px; margin-left:auto; margin-right:auto; font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; }
/* Make the logo responsive and preserve aspect ratio to avoid clipping */
.ev-header img { width:auto; height:44px; max-width:100%; object-fit:contain; display:block; border-radius:8px }
.ev-title { font-size:20px; font-weight:700; }
.ev-sub { color: var(--muted); margin-top: -2px; font-size:13px }
.card { background: var(--card); padding:16px; border-radius:12px; box-shadow:0 6px 20px rgba(15,23,42,0.06); margin-bottom:8px }
.chat { max-width:100%; }
.chat .user { background:#daf5ff; color:#022d45; padding:8px 12px; border-radius:12px; margin:4px 0; display:inline-block }
.chat .bot { background:#f1f5f9; color:var(--text); padding:8px 12px; border-radius:12px; margin:4px 0; display:inline-block }
.suggested { margin-top:8px; display:flex; gap:8px; flex-wrap:wrap }
.suggested .btn { background:var(--primary); color:white; border:none; padding:6px 10px; border-radius:8px; cursor:pointer; white-space:nowrap }
.stButton>button { white-space:nowrap; min-width:64px }

/* Tighten spacing under Chat to remove large empty gaps */
.stTextInput, .stTextArea { margin-top:4px !important; margin-bottom:6px !important }
.stTextInput>div, .stTextArea>div { padding:6px !important; border-radius:8px }
.stButton>button { padding:6px 10px !important }
.left-panel { padding-right: 10px }
.right-panel { padding-left: 10px }
.model-select-note { color:#475569; font-size:13px; margin-top:6px }
.chat-title { margin-bottom:4px }
</style>
"""

_CHAT_CSS_DARK = """
<style>
/* Theme variables (dark) */
:root {
    --bg: #071028;
    --card: linear-gradient(135deg, #071526, #09172a);
    --primary: #0ea5a4;
    --muted: #9fb4c8;
    --text: #dbeeff;
}
.ev-header { display:flex; align-items:center; gap:14px; margin-bottom:6px }
/* Prevent header/logo from being clipped at very small viewports */
div.block-container { padding-top: 0.5rem; padding-left:12px; padding-right:12px; max-width:1100px; margin-left:auto; margin-right:auto; font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; color: var(--text); background: var(--bg) }
.ev-title { font-size:24px; font-weight:700; color:var(--text) }
.ev-sub { color: var(--muted); margin-top: -4px }
.card { background: var(--card); padding:16px; border-radius:12px; box-shadow:0 6px 20px rgba(0,0,0,0.6); margin-bottom:8px }
.chat { max-width:100%; }
.chat .user { background:#063b4a; color:#c9f6ff; padding:8px 12px; border-radius:12px; margin:4px 0; display:inline-block }
.chat .bot { background:#0b2330; color:var(--text); padding:8px 12px; border-radius:12px; margin:4px 0; display:inline-block }
.suggested { margin-top:8px; display:flex; gap:8px; flex-wrap:wrap }
.suggested .btn { background:var(--primary); color:white; border:none; padding:6px 10px; border-radius:8px; cursor:pointer }
.left-panel { padding-right: 10px }
.right-panel { padding-left: 10px }
.model-select-note { color:var(--muted); font-size:13px; margin-top:6px }
.chat-title { margin-bottom:4px }
</style>
"""

def render_header(): 
    st.markdown("# EV Range Explorer — Clean Rebuild")
    st.markdown("A simplified, reliable rebuild using OpenAI (if available) + Wikipedia fallback.")


render_header()
    # Render only the textual header (title + subtitle) and remove the logo image
    st.markdown(
        '<div style="margin:6px 0">'
        '<div class="ev-title">EV Range Explorer</div>'
        '<div class="ev-sub">Interactive range prediction & EV assistant</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# Determine repository root robustly. In some Streamlit runtimes __file__ can be empty,
# so fall back to the current working directory when needed.
try:
    ROOT = os.path.abspath(os.path.dirname(__file__))
    if not ROOT:
        raise NameError()
except Exception:
    ROOT = os.getcwd()


def load_openai_key():
    """Try multiple locations to find an OpenAI API key.

    Search order:
      1. Environment variable OPENAI_API_KEY
      2. Streamlit secrets (st.secrets['OPENAI_API_KEY']) if available
      3. A file named 'openai_key.txt' in the project root (first line)
      4. A '.env' file in the project root with OPENAI_API_KEY=...

    If found, this function also sets os.environ['OPENAI_API_KEY'] so other
    code using os.environ will work. Returns the key string or None.
    """
    # 1. env
    key = os.environ.get('OPENAI_API_KEY')
    if key:
        return key

    # 2. Streamlit secrets (when running under Streamlit)
    try:
        s = st.secrets.get('OPENAI_API_KEY') if hasattr(st, 'secrets') else None
        if s:
            os.environ['OPENAI_API_KEY'] = s
            return s
    except Exception:
        pass

    # 3. project file openai_key.txt
    try:
        p = os.path.join(ROOT, 'openai_key.txt')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as fh:
                v = fh.read().strip()
                if v:
                    os.environ['OPENAI_API_KEY'] = v
                    return v
    except Exception:
        pass

    # 4. simple .env parsing (no dependency)
    try:
        p = os.path.join(ROOT, '.env')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    kname, val = line.split('=', 1)
                    if kname.strip() == 'OPENAI_API_KEY':
                        v = val.strip().strip('"\'"')
                        if v:
                            os.environ['OPENAI_API_KEY'] = v
                            return v
    except Exception:
        pass

    return None


_ = load_openai_key()


def find_model_files(root):
    try:
        return sorted([f for f in os.listdir(root) if f.startswith('model_') and f.endswith('.joblib')])
    except Exception:
        return []


def safe_load_model(path):
    try:
        return joblib.load(path)
    except Exception:
        return None


def call_openai_system(query: str) -> str:
    """Call OpenAI ChatCompletion (gpt-3.5-turbo) if available and key is set."""
    if not OPENAI_AVAILABLE:
        return None
    key = load_openai_key()
    if not key:
        return None
    try:
        openai.api_key = key
        resp = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': 'You are an assistant for an EV range prediction app. Keep answers short and actionable.'},
                {'role': 'user', 'content': query},
            ],
            max_tokens=200,
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None


def call_wikipedia(query: str) -> str:
    try:
        s = requests.get('https://en.wikipedia.org/w/api.php', params={
            'action': 'query', 'list': 'search', 'srsearch': query, 'format': 'json', 'srlimit': 1
        }, timeout=6)
        s.raise_for_status()
        js = s.json()
        hits = js.get('query', {}).get('search', [])
        if not hits:
            return None
        title = hits[0]['title']
        r = requests.get(f'https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.requote_uri(title)}', timeout=6)
        r.raise_for_status()
        jd = r.json()
        return jd.get('extract') or jd.get('description')
    except Exception:
        return None


def generate_reply(query: str) -> str:
    q = (query or '').strip()
    if not q:
        return "Please ask a question about EV range, models, or the dataset."
    # direct rule
    lower = q.lower()
    if 'what is an ev' in lower or 'what is ev' in lower or ('what' in lower and 'electric vehicle' in lower):
        return 'An electric vehicle (EV) uses one or more electric motors powered by rechargeable batteries instead of an internal combustion engine.'
    if 'predict' in lower and ('range' in lower or 'battery' in lower):
        return 'Use the left panel: choose a model, provide battery_capacity_kwh and efficiency_wh_per_km (or upload a CSV), then click Predict.'
    # try OpenAI
    out = call_openai_system(q)
    if out:
        return out
    # fallback to Wikipedia
    out = call_wikipedia(q)
    if out:
        return out
    return "I don't know that yet — ask about models, prediction inputs, or upload a CSV."

@st.cache_resource
def list_models():
    try:
        files = [f for f in os.listdir(ROOT) if f.startswith('model_') and f.endswith('.joblib')]
        return sorted(files)
    except FileNotFoundError:
        # If ROOT is invalid for any reason, return empty list (UI will show an error)
        return []
    except Exception as e:
        # log exception to the app (so user can see it in the UI) and return empty list
        st.error(f'Error listing models: {e}')
        return []

@st.cache_resource
def load_model(path):
    return joblib.load(os.path.join(ROOT, path))

def simple_doc_search(query, docs):
    query = query.lower()
    for doc in docs:
        text = open(os.path.join(ROOT, doc), encoding='utf-8').read()
        if query in text.lower():
            # return a short snippet
            i = text.lower().find(query)
            start = max(0, i-200)
            return text[start:start+600].strip()
    return None


@st.cache_resource
def build_doc_index(candidate_files=None):
    """Build a small TF-IDF index over a list of repository text files.

    Returns a dict with keys: vectorizer, matrix, files, docs
    """
    if candidate_files is None:
        candidate_files = ['README.md', 'models_report.md', 'README_predict.md', 'models_report.md', 'models_report.md']
    # If no candidate list provided, discover common doc files in the repo.
    if candidate_files is None:
        candidate_files = []
        for root, _, files in os.walk(ROOT):
            for fn in files:
                if fn.lower().endswith(('.md', '.txt', '.rst')) or fn.lower().startswith('readme'):
                    candidate_files.append(os.path.join(root, fn))

    chunks = []
    meta = []
    for path in candidate_files:
        p = path if os.path.isabs(path) else os.path.join(ROOT, path)
        if not os.path.exists(p):
            continue
        try:
            with open(p, 'r', encoding='utf-8') as fh:
                text = fh.read()
        except Exception:
            text = ''
        if not text:
            continue
        # split into overlapping chunks (~300-400 chars) for finer retrieval
        max_len = 400
        step = 250
        i = 0
        while i < len(text):
            chunk = text[i:i+max_len].strip()
            if chunk:
                chunks.append(chunk.replace('\n', ' '))
                meta.append({'file': os.path.relpath(p, ROOT)})
            i += step

    if not chunks:
        return None

    try:
        vect = TfidfVectorizer(stop_words='english', max_features=20000)
        mat = vect.fit_transform(chunks)
        return {'vectorizer': vect, 'matrix': mat, 'meta': meta, 'chunks': chunks}
    except Exception:
        return None


def semantic_doc_search(query, index, top_n=1, min_score=0.12):
    """Return the most relevant chunk(s) from the index or None.

    Returns a plain string suitable for bot_reply when score >= min_score.
    """
    if not index:
        return None
    try:
        qv = index['vectorizer'].transform([query])
        sims = linear_kernel(qv, index['matrix']).flatten()
        if sims.size == 0:
            return None
        idxs = sims.argsort()[::-1][:top_n]
        best_idx = idxs[0]
        best_score = float(sims[best_idx])
        if best_score < min_score:
            return None
        chunk = index['chunks'][best_idx]
        file = index['meta'][best_idx]['file'] if 'meta' in index and index['meta'] and 'file' in index['meta'][best_idx] else 'doc'
        # return snippet with source and score context
        return f'From {file} (score={best_score:.2f}): ' + (chunk[:1000] + ('...' if len(chunk) > 1000 else ''))
    except Exception:
        return None


def process_user_message(user_input):
    """Schedule a user message for processing: append the user message and a
    'Thinking...' placeholder, then mark the message as pending. The actual
    reply will be generated by the main loop so the placeholder is visible
    immediately and replaced when ready.
    """
    # append user message
    st.session_state.chat.append(('user', user_input))
    # append placeholder if not present
    try:
        if not (st.session_state.chat and st.session_state.chat[-1][0] == 'bot' and st.session_state.chat[-1][1] == 'Thinking...'):
            st.session_state.chat.append(('bot', 'Thinking...'))
    except Exception:
        st.session_state.chat.append(('bot', 'Thinking...'))

    # store pending message. If the running Streamlit exposes experimental_rerun
    # we call it to force an immediate rerun so the 'Thinking...' placeholder
    # is shown before heavy work; otherwise skip (older/newer Streamlit may not
    # provide this function) and rely on the normal rerun behavior.
    st.session_state['_pending'] = user_input
    try:
        rerun_fn = getattr(st, 'experimental_rerun', None)
        if callable(rerun_fn):
            rerun_fn()
    except Exception:
        # if experimental_rerun isn't available or fails, continue without it
        pass


def _bot_reply_replace(msg):
    """Replace the last bot placeholder with the real reply or append if missing."""
    try:
        if st.session_state.chat and st.session_state.chat[-1][0] == 'bot' and st.session_state.chat[-1][1] == 'Thinking...':
            st.session_state.chat[-1] = ('bot', msg)
            return
    except Exception:
        pass
    st.session_state.chat.append(('bot', msg))


def generate_reply(user_input):
    """Generate a bot reply string for a given user_input (pure logic, no UI).
    This is extracted from the original process_user_message code.
    """
    txt = user_input.lower()
    # small regex rule: "predict battery 75" -> guide user to set battery field
    m_batt = re.search(r"battery\s*(\d+\.?\d*)", txt)
    if m_batt and 'predict' in txt:
        val = m_batt.group(1)
        return f'I saw battery capacity {val} kWh — set `battery_capacity_kwh` to {val} in the left panel and click Predict.'

    if 'predict' in txt or 'range' in txt:
        return 'To predict, switch to the left panel and fill the form or upload a CSV.'
    elif ('list' in txt and 'model' in txt) or 'models' in txt:
        m = list_models()
        if m:
            return 'Available models: ' + ', '.join(m)
        else:
            return 'No saved models found in the repository.'

    # Ask what inputs the model expects
    if any(x in txt for x in ('what does the model', 'what inputs', 'features expected', 'feature names', 'input features', 'what does model expect', 'expected features', 'feature_names')):
        all_models = list_models()
        if all_models:
            try:
                m0 = load_model(all_models[0])
                expected = getattr(m0, 'feature_names_in_', None)
                if expected is not None:
                    return 'A typical model expects these features: ' + ', '.join(expected)
                else:
                    return 'Could not determine feature names from the saved model pipeline.'
            except Exception:
                return 'Could not load model to inspect expected features.'
        else:
            return 'No models found in repository to inspect.'

    elif 'best' in txt or 'best model' in txt or 'which model' in txt:
        snippet = simple_doc_search('best model', ['README.md', 'models_report.md'])
        if snippet:
            return snippet
        else:
            return 'Best model: SVR (see README.md and models_report.md for full metrics).'
    elif 'feature' in txt or 'features' in txt or 'columns' in txt:
        fpath = os.path.join(ROOT, 'features_standard_scaled.csv')
        if os.path.exists(fpath):
            try:
                df = pd.read_csv(fpath, nrows=0)
                return 'Features in dataset: ' + ', '.join(df.columns.tolist())
            except Exception:
                return 'Could not read features file.'
        else:
            return 'Preprocessed features file not found. Check repo files.'
    elif 'metric' in txt or 'evaluate' in txt or 'evaluation' in txt:
        snippet = simple_doc_search('metrics', ['metrics_summary_range_km.csv', 'models_report.md', 'README.md'])
        if snippet:
            return 'Found this in docs:\n' + snippet
        else:
            return 'See metrics_summary_range_km.csv or models_report.md for evaluation info.'

    # Additional rule-based intents
    # Charging-related questions
    if any(x in txt for x in ('charge', 'charging', 'charger', 'fast charge', 'dc fast', 'ac charger', 'type 2', 'ccs', 'tesla')):
        m = re.search(r"(\d+\.?\d*)\s?%.*?(\d+\.?\d*)\s?min|(\d+\.?\d*)\s?min.*?(\d+\.?\d*)\s?%", txt)
        if m:
            return 'Charging time depends strongly on charger power and battery state-of-charge. If you give battery kWh and charger kW I can estimate a rough charge time.'
        else:
            return 'Charging: AC (home) chargers are ~3-22 kW; public fast DC chargers are ~50-350+ kW. Example: 75 kWh battery on a 150 kW DC charger may reach ~0-80% in ~30-40 minutes.'

    # Battery degradation / life
    if any(x in txt for x in ('degrad', 'degrade', 'battery life', 'battery health', 'warranty', 'cycle')):
        return 'Battery degradation depends on chemistry, depth-of-discharge, temperature, and charging habits. Typical usable capacity loss is a few percent per year; manufacturers often warranty ~8 years / 100k miles.'

    # Sample CSV / upload guidance
    if any(x in txt for x in ('csv', 'upload', 'sample csv', 'batch predict', 'batch')):
        return 'To run batch predictions upload a CSV with the same feature columns used in training (see `test_input_manual.csv` for an example). Use the left panel upload control and choose the model before Predict.'

    # Explain prediction / feature importance
    if any(x in txt for x in ('explain', 'why', 'feature importance', 'shap', 'why predicted', 'interpret')):
        return 'Model predictions use features like battery capacity, efficiency (Wh/km), and vehicle mass/geometry. For per-prediction explanations use tools like SHAP. I can list the features the model expects if you ask "Show dataset features".'

    # Unit conversions (miles/km)
    if 'mile' in txt or 'km' in txt or 'kilometer' in txt:
        if 'miles to km' in txt or 'miles to kilometers' in txt:
            return '1 mile = 1.60934 km. To convert miles->km multiply by 1.60934.'
        elif 'km to miles' in txt or 'kilometer to miles' in txt:
            return '1 km = 0.621371 miles. To convert km->miles multiply by 0.621371.'
        else:
            return 'Range is reported in kilometers in this app by default (see README). Ask "convert X miles to km" for a conversion example.'

    # Short FAQ-style canned answers (expanded)
    faq_map = {
        ('charging time', 'how long to charge', 'charge time', 'fast charging'): 'Charging time depends on charger power and battery size. Example: a 75 kWh battery on a 150 kW DC fast charger may charge ~0-80% in ~30-40 minutes.',
        ('battery life', 'battery health', 'warranty', 'degrad', 'degrade'): 'Battery life depends on chemistry, usage, and temperature. Typical warranties are 8 years or 100,000 miles for many EVs; degradation is usually a few percent per year.',
        ('how to retrain', 'retrain', 'training', 'retraining'): 'To retrain: prepare a CSV with the original features, apply the same preprocessing pipeline, fit an estimator, and save the pipeline as model_*.joblib. See `models_report.md` and `README.md` for details on features and metrics.',
        ('where is readme', 'readme', 'docs', 'documentation'): 'See README.md in the repo root for project overview, and `models_report.md` for model evaluation details.',
        ('efficiency', 'wh/km', 'wh per km', 'efficiency_wh_per_km'): 'Efficiency (Wh/km) has a large influence on range: lower Wh/km (more efficient) increases range linearly for a given battery size.',
        ('sample csv', 'test_input', 'example csv', 'example input'): 'A sample input CSV is provided as `test_input_manual.csv`. Upload a CSV with the same column names as the model expects (see "Show dataset features").'
    }
    for triggers, resp in faq_map.items():
        for trig in (triggers if isinstance(triggers, (list, tuple)) else (triggers,)):
            if trig in txt:
                return resp

    # Semantic document search (TF-IDF) — prefer local docs for project-specific
    try:
        doc_index = st.session_state.get('_doc_index')
    except Exception:
        doc_index = None
    if doc_index is None:
        candidates = [f for f in ['README.md', 'models_report.md', 'README_predict.md'] if os.path.exists(os.path.join(ROOT, f))]
        doc_index = build_doc_index(candidates)
        try:
            st.session_state['_doc_index'] = doc_index
        except Exception:
            pass
    try:
        sem = semantic_doc_search(user_input, doc_index)
        if sem:
            return sem
    except Exception:
        pass

    # Domain gating: don't answer out-of-scope personal/medical questions.
    allowed_keywords = (
        'ev vehicle model predict range battery charging charge efficiency '
        'features dataset csv train retrain shap metric rmse r2 mae wh/km kwh km miles'
    )
    if not any(k in txt for k in allowed_keywords.split()):
        return 'This assistant answers questions about the project, electric vehicles, models, datasets, and predictions only. Please ask a question related to EVs, models, or the repository.'

    # Try external provider(s) as a last resort (OpenAI preferred, Wikipedia fallback)
    try:
        use_external = st.session_state.get('use_external_api', False)
    except Exception:
        use_external = True
    provider = st.session_state.get('external_provider', 'OpenAI') if 'external_provider' in st.session_state else 'OpenAI'
    if use_external:
        try:
            resp = call_external_api(user_input, provider)
        except Exception:
            resp = None
        if not resp and provider == 'OpenAI':
            try:
                resp = call_external_api(user_input, 'Wikipedia')
            except Exception:
                resp = None
        if resp:
            return resp

    # Fallback simple doc search then Wikipedia
    try:
        snippet = simple_doc_search(user_input, ['README.md', 'models_report.md'])
        if snippet:
            return snippet
    except Exception:
        pass

    try:
        wiki_resp = call_external_api(user_input, 'Wikipedia')
    except Exception:
        wiki_resp = None
    if wiki_resp:
        return wiki_resp

    return "I don't know that yet — ask about predictions, models, or dataset features."


def call_external_api(query, provider='OpenAI'):
    """Call an external API provider and return a short string reply.

    provider: 'OpenAI' or 'Wikipedia'
    """
    q = query.strip()
    if provider == 'OpenAI':
        # If the openai package is missing or we can't find a key, silently
        # return None so callers fallback to local responses.
        if not OPENAI_AVAILABLE:
            return None
        key = load_openai_key()
        if not key:
            return None
        # set for downstream libraries that expect os.environ
        os.environ['OPENAI_API_KEY'] = key
        try:
            openai.api_key = key
        except Exception:
            # openai module may not expose attribute in static analysis; ignore
            pass

        # simple chat completion
        try:
            resp = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    { 'role': 'system', 'content': 'You are an assistant for an EV range prediction app. Keep answers short and actionable.' },
                    { 'role': 'user', 'content': q }
                ],
                max_tokens=300,
                temperature=0.2,
            )
            # defensive: resp may be None or malformed
            try:
                return resp.choices[0].message.content.strip()
            except Exception:
                return None
        except Exception:
            return None
    elif provider == 'Wikipedia':
        # Use MediaWiki search then fetch summary via REST summary endpoint
        try:
            s = requests.get('https://en.wikipedia.org/w/api.php', params={
                'action': 'query', 'list': 'search', 'srsearch': q, 'format': 'json', 'srlimit': 1
            }, timeout=8)
            s.raise_for_status()
            js = s.json()
            hits = js.get('query', {}).get('search', [])
            if not hits:
                return None
            title = hits[0]['title']
            # fetch summary
            r = requests.get(f'https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.requote_uri(title)}', timeout=8)
            r.raise_for_status()
            jd = r.json()
            return jd.get('extract') or jd.get('description')
        except Exception:
            return None
    else:
        raise RuntimeError(f'Unknown provider: {provider}')

# render header instead of a large duplicated title so heading isn't cut off
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
dark = st.sidebar.checkbox('Dark mode', value=st.session_state.dark_mode)
st.session_state.dark_mode = dark
css = _CHAT_CSS_DARK if dark else _CHAT_CSS_LIGHT
st.markdown(css, unsafe_allow_html=True)
render_header()

# Ensure the chat session state exists immediately so the UI can render a
# stable initial message even before any user action. This prevents the
# app showing a blank chat area on first load.
if 'chat' not in st.session_state:
    st.session_state.chat = [
        ('system', 'Hello — ask about models, evaluation, predictions, or dataset. Try the suggested questions below.')
    ]

# Debug banner: show a build timestamp so you can confirm this code is running in the browser.
from datetime import datetime as _dt
_debug_ts = _dt.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
st.markdown(f"**DEBUG BUILD:** {_debug_ts}")

# Large visible helper: show a cache-busting link the user can click to force
# the browser to load a fresh page (useful when Ctrl+F5 isn't working).
cb = f'?v={_debug_ts.replace(" ", "_")}'
st.markdown(
    "<div style='background:#fffae6;border-left:6px solid #f59e0b;padding:10px;border-radius:6px'>"
    "<strong>If the page looks stale:</strong> click the link below to open a fresh view (cache-busted)." 
    f"<br><a href='{cb}' target='_blank' style='font-weight:700'>Open fresh view</a>"
    "</div>",
    unsafe_allow_html=True,
)

# Raw session dump (debug): show the chat state so you can confirm messages exist
try:
    raw_chat = st.session_state.get('chat', [])
    st.markdown('**RAW chat session state (debug)**')
    st.code(json.dumps(raw_chat[-30:], indent=2, default=str))
except Exception:
    st.write('Could not render raw chat state')

models = list_models()
if not models:
    st.error('No saved models found in repo (look for model_*.joblib). Place a pipeline file and reload.')
    st.stop()

# If there's a pending chatbot message (set by process_user_message), handle it
# here. This separation ensures the 'Thinking...' placeholder is rendered on
# the prior run, then the heavy reply generation runs and replaces the
# placeholder so the UI shows the indicator reliably.
# Helper to process a single action (append user, compute reply, replace)
def _process_action(q: str):
    if not q:
        return
    try:
        st.session_state.chat.append(('user', q))
    except Exception:
        st.session_state.chat = st.session_state.get('chat', []) + [('user', q)]
    try:
        st.session_state.chat.append(('bot', 'Thinking...'))
    except Exception:
        st.session_state.chat = st.session_state.get('chat', []) + [('bot', 'Thinking...')]
    with st.spinner('Thinking...'):
        try:
            reply = generate_reply(q)
        except Exception:
            reply = 'I encountered an error while preparing the reply.'
    try:
        st.session_state.chat[-1] = ('bot', reply)
    except Exception:
        st.session_state.chat.append(('bot', reply))

# Central queued-action handler: when a widget sets `_queued_action` we
# process it here before rendering so the chat + 'Thinking...' placeholder
# appear and are replaced in the same run. This avoids off-by-one click bugs.
if '_queued_action' in st.session_state:
    act = st.session_state.pop('_queued_action')
    try:
        q = act.get('q') if isinstance(act, dict) else act
    except Exception:
        q = act
    _process_action(q)

col1, col2 = st.columns([2,1])

with col2:
    st.subheader('Chatbot (EV assistant)')
    # External API controls
    st.caption('The chatbot will query external services (OpenAI preferred, Wikipedia fallback) for richer answers.')
    # Small runtime status to help debug UI issues (visible in app)
    try:
        pending_flag = '_queued_action' in st.session_state
        st.markdown(f"**Status:** chat_messages={len(st.session_state.get('chat', []))}, pending={pending_flag}")
    except Exception:
        st.markdown("**Status:** unable to read session state")
    # External lookups are enabled by default for this app. Set session keys only
    # if they don't already exist to avoid forcing a Streamlit rerun on every render.
    if 'use_external_api' not in st.session_state:
        st.session_state['use_external_api'] = True
    if 'external_provider' not in st.session_state:
        st.session_state['external_provider'] = 'OpenAI'
    if 'chat' not in st.session_state:
        st.session_state.chat = [
            ('system', 'Hello — ask about models, evaluation, predictions, or dataset. Try the suggested questions below.')
        ]

    # chat rendering using a placeholder container so we can update it
    # in the same run after appending messages (avoids needing a rerun).
    def render_chat(container):
        # Render a simple, robust textual fallback first so the chat is visible
        # even if custom CSS/HTML rendering fails in some Streamlit environments.
        try:
            container.markdown('---')
            for role, msg in st.session_state.chat[-12:]:
                if role == 'user':
                    container.write(f'**You:** {msg}')
                elif role == 'bot':
                    container.write(f'**Bot:** {msg}')
                else:
                    container.write(f'**System:** {msg}')
            container.markdown('---')
        except Exception:
            # As a last resort, show raw chat data for debugging
            try:
                container.write(st.session_state.get('chat', [])[-12:])
            except Exception:
                container.write('No chat data available')

    chat_container = st.empty()
    render_chat(chat_container)

    # Suggested quick questions (short labels, horizontal)
    suggested_questions = [
        ('Predict', 'How do I predict range?'),
        ('List', 'List available models'),
        ('Best', 'Which is the best model?'),
        ('Features', 'Show dataset features'),
        ('Eval', 'How were models evaluated?')
    ]
    q_cols = st.columns(len(suggested_questions))
    for c, (label, q) in zip(q_cols, suggested_questions):
        if c.button(label):
            # queue the action; attempt to rerun the script so the central
            # handler picks it up. If experimental_rerun isn't available,
            # process the action immediately to avoid lag.
            st.session_state['_queued_action'] = {'q': q}
            try:
                rerun_fn = getattr(st, 'experimental_rerun', None)
                if callable(rerun_fn):
                    rerun_fn()
                else:
                    # immediate fallback
                    _process_action(q)
            except Exception:
                try:
                    _process_action(q)
                except Exception:
                    pass

    # Chat input form: process synchronously so the placeholder and spinner
    # are rendered in the same run and the reply appears without extra clicks.
    with st.form('chat_form', clear_on_submit=False):
        user_input = st.text_input('Message', '', key='chat_input')
        submitted = st.form_submit_button('Send')
    if submitted:
        val = st.session_state.get('chat_input', '')
        if val:
            st.session_state['_queued_action'] = {'q': val}
            # clear input immediately so UI shows it's been sent
            try:
                st.session_state['chat_input'] = ''
            except Exception:
                pass
            try:
                rerun_fn = getattr(st, 'experimental_rerun', None)
                if callable(rerun_fn):
                    rerun_fn()
                else:
                    _process_action(val)
            except Exception:
                try:
                    _process_action(val)
                except Exception:
                    pass

with col1:
    st.subheader('Predict Range')
    # Model selection: show friendly model names (from metrics) but restrict to those with model files present
    metrics_path = os.path.join(ROOT, 'metrics_summary_range_km.csv')
    dfm = None
    if os.path.exists(metrics_path):
        try:
            dfm = pd.read_csv(metrics_path)
        except Exception:
            dfm = None

    model_map = {}  # display_name -> model_file
    if dfm is not None and 'model' in dfm.columns and 'model_file' in dfm.columns:
        for _, r in dfm.iterrows():
            mf = r.get('model_file')
            name = r.get('model')
            if pd.notna(mf) and mf in models:
                model_map[str(name)] = mf

    # Fallback: if model_map empty, try to populate from models filenames
    if not model_map:
        for m in models:
            short = os.path.splitext(os.path.basename(m))[0]
            model_map[short] = m

    display_names = list(model_map.keys())
    sel_display = st.selectbox('Choose model', display_names, index=0)
    sel = model_map.get(sel_display)

    # optional: allow expanding to raw filenames
    if st.checkbox('Show raw model filenames', value=False):
        sel = st.selectbox('Raw model file', models, index=models.index(sel) if sel in models else 0, key='raw_models')

    model = load_model(sel)

    st.markdown('---')
    st.markdown('Manual input (fill fields used commonly in training). Leave blank to skip.')
    with st.form('manual'):
        battery = st.number_input('battery_capacity_kwh', value=75.0)
        efficiency = st.number_input('efficiency_wh_per_km', value=180.0)
        top_speed = st.number_input('top_speed_kmh', value=160.0)
        acc = st.number_input('acceleration_0_100_s', value=8.5)
        length = st.number_input('length_mm', value=4600.0)
        width = st.number_input('width_mm', value=1800.0)
        height = st.number_input('height_mm', value=1500.0)
        submitted = st.form_submit_button('Predict')
    if submitted:
        raw = pd.DataFrame([{ 
            'battery_capacity_kwh': battery,
            'efficiency_wh_per_km': efficiency,
            'top_speed_kmh': top_speed,
            'acceleration_0_100_s': acc,
            'length_mm': length,
            'width_mm': width,
            'height_mm': height
        }])
        # Build a full input row matching the model's expected feature names.
        # Prefer medians from preprocessed features file when available.
        expected = getattr(model, 'feature_names_in_', None)
        defaults = {}
        preproc_file = os.path.join(ROOT, 'features_standard_scaled.csv')
        if os.path.exists(preproc_file):
            try:
                df_defaults = pd.read_csv(preproc_file)
            except Exception:
                df_defaults = None
        else:
            df_defaults = None

        # manual inputs mapping (raw names used in training)
        manual_map = {
            'battery_capacity_kwh': battery,
            'efficiency_wh_per_km': efficiency,
            'top_speed_kmh': top_speed,
            'acceleration_0_100_s': acc,
            'length_mm': length,
            'width_mm': width,
            'height_mm': height,
        }

        row = {}
        if expected is None:
            # fallback: use manual_map only
            row = manual_map
        else:
            for col in expected:
                if col in manual_map:
                    row[col] = manual_map[col]
                else:
                    # prefer median from preprocessed features if available
                    if df_defaults is not None and col in df_defaults.columns:
                        try:
                            val = df_defaults[col].median()
                            # ensure it's a python scalar
                            row[col] = float(val) if pd.notna(val) else 0.0
                        except Exception:
                            # fallback to mode
                            try:
                                row[col] = df_defaults[col].mode().iat[0]
                            except Exception:
                                row[col] = 0
                    else:
                        # conservative fallback: 0 or False
                        row[col] = 0

        input_df = pd.DataFrame([row])
        try:
            # If the loaded model is a plain estimator (not a Pipeline), it may
            # expect preprocessed / scaled inputs. Try to apply a saved scaler
            # (prefer `scaler_standard.joblib`, then `scaler_minmax.joblib`).
            if not isinstance(model, Pipeline):
                scaler = None
                for sname in ('scaler_standard.joblib', 'scaler_minmax.joblib'):
                    sp = os.path.join(ROOT, sname)
                    if os.path.exists(sp):
                        try:
                            scaler = joblib.load(sp)
                            break
                        except Exception:
                            scaler = None

                if scaler is not None:
                    try:
                        expected = getattr(model, 'feature_names_in_', None)
                        if expected is not None:
                            to_transform = input_df[expected]
                        else:
                            to_transform = input_df

                        # If the scaler was fit on a DataFrame it may expect specific
                        # feature names (including the target). Respect scaler.feature_names_in_ if present.
                        scaler_cols = getattr(scaler, 'feature_names_in_', None)
                        if scaler_cols is not None:
                            # Build a frame matching the scaler's expected columns.
                            tf = pd.DataFrame()
                            for col in scaler_cols:
                                if col in to_transform.columns:
                                    tf[col] = to_transform[col]
                                else:
                                    # try to fill from preprocessed defaults if available
                                    if df_defaults is not None and col in df_defaults.columns:
                                        try:
                                            tf[col] = [float(df_defaults[col].median())]
                                        except Exception:
                                            try:
                                                tf[col] = [df_defaults[col].mode().iat[0]]
                                            except Exception:
                                                tf[col] = [0]
                                    else:
                                        tf[col] = [0]
                            to_scale = tf
                        else:
                            to_scale = to_transform

                        # scaler.transform will produce values for all scaler columns; if the
                        # scaler was fitted including the target or extra cols, slice the
                        # resulting array to the model's expected feature order.
                        scaled_all = scaler.transform(to_scale)
                        model_feats = getattr(model, 'feature_names_in_', None)
                        if scaler_cols is not None and model_feats is not None:
                            s_list = list(scaler_cols)
                            try:
                                idxs = [s_list.index(f) for f in model_feats]
                                X = scaled_all[:, idxs]
                            except Exception:
                                # couldn't map precisely; fall back to scaled_all
                                X = scaled_all
                        else:
                            X = scaled_all

                        pred = model.predict(X)
                    except Exception as e:
                        st.warning('Scaling failed; attempting raw prediction. Details: ' + str(e))
                        pred = model.predict(input_df)
                else:
                    st.warning('No scaler found; predicting with raw inputs. If the model was trained on scaled features this may be invalid.')
                    pred = model.predict(input_df)
            else:
                pred = model.predict(input_df)

            # Some models were trained on a scaled target. Compute and show both raw
            # model output and an inverse-scaled value (when applicable) so users see
            # what's happening and can confirm correctness.
            raw_val = float(pred[0])
            displayed_pred = raw_val

            try:
                s = None
                for sname in ('scaler_standard.joblib', 'scaler_minmax.joblib'):
                    sp = os.path.join(ROOT, sname)
                    if os.path.exists(sp):
                        try:
                            s = joblib.load(sp)
                            break
                        except Exception:
                            s = None
                if s is not None:
                    sfn = list(getattr(s, 'feature_names_in_', []))
                    if 'range_km' in sfn:
                        idx = sfn.index('range_km')
                        mean = s.mean_[idx]
                        scale = s.scale_[idx]
                        inv = raw_val * scale + mean
                        # Heuristic: if raw is small (likely scaled) and inverse is plausible,
                        # show inverse-scaled value instead and inform the user.
                        if abs(raw_val) < 5 and 0 < inv < 100000:
                            displayed_pred = inv
                            st.info(f'Inverse-scaled prediction: raw={raw_val:.3f} -> {displayed_pred:.2f} km (using {os.path.basename(sp)})')
            except Exception:
                # don't block on inverse-scaling failures; show raw
                pass

            # always show raw and final value to be explicit
            st.write(f'Raw model output: {raw_val:.6f}')

            # If the displayed prediction is implausible (negative or extremely large),
            # try a fallback model (SVR, RandomForest, GradientBoosting) to provide a
            # more reliable estimate and warn the user.
            implausible = False
            if displayed_pred is None:
                implausible = True
            else:
                try:
                    implausible = (displayed_pred < 0) or (displayed_pred > 2000)
                except Exception:
                    implausible = True

            if implausible:
                st.warning('Model output looks implausible — trying fallback models for a sanity check.')
                fallback_list = ['model_SVR.joblib', 'model_RandomForest.joblib', 'model_GradientBoosting.joblib']
                fallback_pred = None
                for fb in fallback_list:
                    if fb in os.listdir(ROOT):
                        try:
                            fb_model = load_model(fb)
                            # reuse same scaling logic as above for this model
                            if not isinstance(fb_model, Pipeline):
                                # try to apply scaler if present
                                sp = None
                                for sname in ('scaler_standard.joblib', 'scaler_minmax.joblib'):
                                    spath = os.path.join(ROOT, sname)
                                    if os.path.exists(spath):
                                        sp = spath
                                        break
                                if sp is not None:
                                    s = joblib.load(sp)
                                    sfn = list(getattr(s, 'feature_names_in_', []))
                                    # attempt to build transformable frame
                                    exp = getattr(fb_model, 'feature_names_in_', None)
                                    if exp is not None:
                                        to_tr = input_df[exp]
                                    else:
                                        to_tr = input_df
                                    try:
                                        Xfb = s.transform(to_tr)
                                        pfb = fb_model.predict(Xfb)
                                    except Exception:
                                        pfb = fb_model.predict(input_df)
                                else:
                                    pfb = fb_model.predict(input_df)
                            else:
                                pfb = fb_model.predict(input_df)
                            fallback_pred = float(pfb[0])
                            # if fallback looks reasonable, stop
                            if 0 <= fallback_pred < 2000:
                                break
                        except Exception:
                            fallback_pred = None
                if fallback_pred is not None:
                    st.success(f'Fallback estimate (from {fb}): {fallback_pred:.2f} km')
                else:
                    st.error('Fallback models failed to produce a sensible prediction.')

            st.success(f'Predicted range_km: {displayed_pred:.2f} (units as saved in model)')
        except Exception as e:
            st.error('Model prediction failed: ' + str(e))

    # show a compact model card with metrics
    st.markdown('---')
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader('Model details')
    st.write(sel)
    # display metrics if available
    try:
        if dfm is not None:
            # try to match by model_file first
            row = None
            if 'model_file' in dfm.columns:
                matches = dfm[dfm['model_file'].str.contains(os.path.basename(sel))]
                if len(matches) == 1:
                    row = matches.iloc[0]
                else:
                    # try matching by the model short name in 'model' column
                    short = os.path.splitext(os.path.basename(sel))[0]
                    if 'model' in dfm.columns:
                        matches2 = dfm[dfm['model'].str.lower().str.contains(short.lower())]
                        if len(matches2) >= 1:
                            row = matches2.iloc[0]
            if row is None and 'model' in dfm.columns:
                # fallback: pick row with matching name to sel label if possible
                possible = dfm[dfm['model'].str.lower().isin([sel.lower(), os.path.splitext(sel)[0].lower()])]
                if len(possible) >= 1:
                    row = possible.iloc[0]

            if row is not None:
                cols = st.columns(3)
                try:
                    cols[0].metric('Test R²', f"{row.get('test_r2', 'N/A'):.3f}")
                except Exception:
                    cols[0].write('Test R²: N/A')
                try:
                    cols[1].metric('RMSE', f"{row.get('rmse', 'N/A'):.3f}")
                except Exception:
                    cols[1].write('RMSE: N/A')
                try:
                    cols[2].metric('MAE', f"{row.get('mae', 'N/A'):.3f}")
                except Exception:
                    cols[2].write('MAE: N/A')
            else:
                st.write('No metrics found for selected model.')
        else:
            st.write('Metrics file not available.')
    except Exception:
        st.write('Could not load metrics for model.')
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('---')
    st.markdown('Or upload a CSV with the same raw columns used for training')
    uploaded = st.file_uploader('Upload CSV', type=['csv'])
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.write('Preview:', df.head())
        try:
            # For batch CSVs, if the model is not a Pipeline, attempt to scale inputs
            if not isinstance(model, Pipeline):
                scaler = None
                for sname in ('scaler_standard.joblib', 'scaler_minmax.joblib'):
                    sp = os.path.join(ROOT, sname)
                    if os.path.exists(sp):
                        try:
                            scaler = joblib.load(sp)
                            break
                        except Exception:
                            scaler = None

                if scaler is not None:
                    try:
                        expected = getattr(model, 'feature_names_in_', None)

                        # If scaler expects specific column names (scaler.feature_names_in_),
                        # ensure the DataFrame includes them; otherwise try to use expected.
                        scaler_cols = getattr(scaler, 'feature_names_in_', None)
                        preproc_file = os.path.join(ROOT, 'features_standard_scaled.csv')
                        df_defaults = None
                        if os.path.exists(preproc_file):
                            try:
                                df_defaults = pd.read_csv(preproc_file)
                            except Exception:
                                df_defaults = None

                        if scaler_cols is not None:
                            # add missing columns with medians or zeros
                            for c in scaler_cols:
                                if c not in df.columns:
                                    if df_defaults is not None and c in df_defaults.columns:
                                        try:
                                            df[c] = df_defaults[c].median()
                                        except Exception:
                                            try:
                                                df[c] = df_defaults[c].mode().iat[0]
                                            except Exception:
                                                df[c] = 0
                                    else:
                                        df[c] = 0
                            scaled_all = scaler.transform(df[scaler_cols])
                            # slice scaled columns to model expected order (model may not expect the target column)
                            model_feats = getattr(model, 'feature_names_in_', None)
                            if model_feats is not None:
                                s_list = list(scaler_cols)
                                try:
                                    idxs = [s_list.index(f) for f in model_feats]
                                    X = scaled_all[:, idxs]
                                except Exception:
                                    X = scaled_all
                            else:
                                X = scaled_all
                        else:
                            if expected is not None:
                                X = scaler.transform(df[expected])
                            else:
                                X = scaler.transform(df)

                        preds = model.predict(X)
                    except Exception as e:
                        st.warning('Scaling failed for batch; attempting raw prediction. Details: ' + str(e))
                        preds = model.predict(df)
                else:
                    st.warning('No scaler found; predicting with raw inputs. If the model was trained on scaled features this may be invalid.')
                    preds = model.predict(df)
            else:
                preds = model.predict(df)

            # Post-process batch preds: try inverse-scaling if necessary (same heuristic)
            adjusted = []
            s = None
            spath = os.path.join(ROOT, 'scaler_standard.joblib')
            if os.path.exists(spath):
                try:
                    s = joblib.load(spath)
                except Exception:
                    s = None

            for p in preds:
                disp = float(p)
                try:
                    if s is not None:
                        sfn = list(getattr(s, 'feature_names_in_', []))
                        if 'range_km' in sfn:
                            idx = sfn.index('range_km')
                            mean = s.mean_[idx]
                            scale = s.scale_[idx]
                            raw = float(p)
                            inv = raw * scale + mean
                            if abs(raw) < 5 and 0 < inv < 100000:
                                # replace with inverse-scaled value but keep raw visible in table
                                disp = inv
                except Exception:
                    pass
                adjusted.append(disp)

            df['predicted_range_km'] = adjusted
            st.write(df.head())
            st.download_button('Download predictions CSV', df.to_csv(index=False), file_name='predictions.csv')
        except Exception as e:
            st.error('Batch prediction failed: ' + str(e))

    st.markdown('---')
    st.write('Tips:')
    st.info('Leave manual fields blank to use dataset medians. Use the CSV upload for batch predictions.')
