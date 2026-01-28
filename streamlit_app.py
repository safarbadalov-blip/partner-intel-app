import streamlit as st
import google.generativeai as genai
import requests
import pandas as pd
import time

# 1. PAGE SETUP
st.set_page_config(page_title="Forensic Partner Intel", layout="wide")
st.title("🕵️ Forensic Truth Engine: 2026 Stable")

# 2. SECRETS
API_KEY = st.secrets["GEMINI_API_KEY"]
RENDER_URL = "https://partner-intelligence-engine.onrender.com"

# 3. CONFIG - LOCKING IN THE STABLE 2026 MODEL
genai.configure(api_key=API_KEY)

# Use 'gemini-2.5-flash' - This is the ONLY stable alias that won't 404
model = genai.GenerativeModel('gemini-2.5-flash')

def call_engine(target_company: str, portal_url: str):
    """Forensic Search Tool"""
    # Safety delay: Prevents the 429 quota crash during tool execution
    time.sleep(2) 
    payload = {
        "TARGET_COMPANY_NAME": target_company, 
        "PARTNER_PORTAL_URL": portal_url,
        "EXECUTION_MODE": "FORENSIC_PLUS_INTERPRETATION"
    }
    r = requests.post(f"{RENDER_URL}/run", json=payload, headers={"x-engine-key": API_KEY})
    data = r.json()
    st.session_state.evidence = data
    return data

# 4. CHAT LOGIC
if prompt := st.chat_input("Analyze..."):
    with st.chat_message("assistant"):
        try:
            # Automatic Function Calling is natively stable in 2.5 Flash
            chat = model.start_chat(enable_automatic_function_calling=True)
            response = chat.send_message(prompt, tools=[call_engine])
            st.markdown(response.text)
        except Exception as e:
            if "404" in str(e):
                st.error("🚨 2026 Update Needed: Model name 'gemini-2.5-flash' is the only stable endpoint.")
            elif "429" in str(e):
                st.error("🛑 Rate Limit. You hit the minute quota. Wait 60s.")
            else:
                st.error(f"Error: {e}")

# 5. FAIL-SAFE TABLE
if "evidence" in st.session_state and st.session_state.evidence:
    st.divider()
    st.subheader("📂 Raw Verified Evidence")
    st.dataframe(pd.DataFrame(st.session_state.evidence.get('QUOTES_TABLE', [])))
