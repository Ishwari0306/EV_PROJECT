import os
import re
import joblib
import pandas as pd
import streamlit as st

st.set_page_config(page_title='EV Range Explorer', layout='wide')

ROOT = os.path.dirname(__file__)

@st.cache_resource
def list_models():
    files = [f for f in os.listdir(ROOT) if f.startswith('model_') and f.endswith('.joblib')]
    return sorted(files)

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

st.title('EV Range Explorer — Streamlit UI')

models = list_models()
if not models:
    st.error('No saved models found in repo (look for model_*.joblib). Place a pipeline file and reload.')
    st.stop()

col1, col2 = st.columns([2,1])

with col2:
    st.subheader('Chatbot (EV assistant)')
    if 'chat' not in st.session_state:
        st.session_state.chat = [
            ('system', 'Ask about models, evaluation, or type "predict" to run a range prediction.')
        ]

    for role, msg in st.session_state.chat:
        if role == 'user':
            st.markdown(f"**You:** {msg}")
        else:
            st.markdown(f"**Bot:** {msg}")

    user_input = st.text_input('Message', '')
    if st.button('Send') and user_input:
        st.session_state.chat.append(('user', user_input))
        # simple intent handling
        if 'predict' in user_input.lower():
            st.session_state.chat.append(('bot', 'To predict, switch to the left panel and fill the form or upload a CSV.'))
        elif 'best' in user_input.lower() or 'best model' in user_input.lower():
            snippet = simple_doc_search('Best model (summary)', ['README.md', 'models_report.md'])
            if snippet:
                st.session_state.chat.append(('bot', snippet))
            else:
                st.session_state.chat.append(('bot', 'Best model: SVR (saved as model_SVR_range_retrained.joblib) — see README for metrics.'))
        else:
            # try to search docs
            snippet = simple_doc_search(user_input, ['README.md', 'models_report.md'])
            if snippet:
                st.session_state.chat.append(('bot', snippet))
            else:
                st.session_state.chat.append(('bot', "I don't know that yet — ask about predictions or models."))

with col1:
    st.subheader('Predict Range')
    sel = st.selectbox('Choose model', models, index=0)
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
        try:
            pred = model.predict(raw)
            st.success(f'Predicted range_km: {float(pred[0]):.2f} (units as saved in model)')
        except Exception as e:
            st.error('Model prediction failed: ' + str(e))

    st.markdown('---')
    st.markdown('Or upload a CSV with the same raw columns used for training')
    uploaded = st.file_uploader('Upload CSV', type=['csv'])
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.write('Preview:', df.head())
        try:
            preds = model.predict(df)
            df['predicted_range_km'] = preds
            st.write(df.head())
            st.download_button('Download predictions CSV', df.to_csv(index=False), file_name='predictions.csv')
        except Exception as e:
            st.error('Batch prediction failed: ' + str(e))

    st.markdown('---')
    st.write('Model info:')
    st.write(sel)
    if hasattr(model, 'named_steps'):
        st.write('Pipeline steps:', list(model.named_steps.keys()))
