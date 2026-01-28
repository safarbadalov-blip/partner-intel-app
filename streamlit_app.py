import streamlit as st
import google.generativeai as genai
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

# 1. PAGE SETUP
st.set_page_config(page_title="Forensic Partner Intel", layout="wide")
st.title("🕵️ Forensic Truth Engine: Conservative Mode")

# 2. SECRETS
API_KEY = st.secrets["GEMINI_API_KEY"]
RENDER_URL = "https://partner-intelligence-engine.onrender.com"

# 3. CONSERVATIVE RATE LIMITER (The Secret Sauce)
if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = datetime.now() - timedelta(seconds=20)

def wait_for_safety():
    """Forces a strict 15-second gap between any AI activity."""
    time_since_last = (datetime.now() - st.session_state.last_request_time).total_seconds()
    wait_needed = 15 - time_since_last
    if wait_needed > 0:
        with st.spinner(f"🛡️ Safety Throttle: Waiting {int(wait_needed)}s to prevent 429 crash..."):
            time.sleep(wait_needed)
    st.session_state.last_request_time = datetime.now()

# 4. CONFIG
genai.configure(api_key=API_KEY)
# We use 1.5 Flash because it has the most 'forgiving' free tier in 2026
model = genai.GenerativeModel('gemini-1.5-flash')

def call_engine(target_company: str, portal_url: str):
    """Forensic Search Tool"""
    # Tool calls also count as requests, so we throttle here too
    time.sleep(2) 
    payload = {"TARGET_COMPANY_NAME": target_company, "PARTNER_PORTAL_URL": portal_url}
    r = requests.post(f"{RENDER_URL}/run", json=payload, headers={"x-engine-key": API_KEY})
    data = r.json()
    st.session_state.evidence = data
    return data

# 5. CHAT LOGIC
if prompt := st.chat_input("Analyze..."):
    # STEP 1: Wait for the safety window
    wait_for_safety()
    
    with st.chat_message("assistant"):
        try:
            chat = model.start_chat(enable_automatic_function_calling=True)
            # STEP 2: Execute
            response = chat.send_message(prompt, tools=[call_engine])
            st.markdown(response.text)
        except Exception as e:
            if "429" in str(e):
                st.error("🛑 Daily Quota Exhausted. Google has cut off free access until Midnight PT.")
            else:
                st.error(f"Error: {e}")

# 6. FAIL-SAFE DATA TABLE (Always shows if data was fetched)
if "evidence" in st.session_state and st.session_state.evidence:
    st.divider()
    st.subheader("📂 Raw Verified Evidence")
    st.dataframe(pd.DataFrame(st.session_state.evidence.get('QUOTES_TABLE', [])))
