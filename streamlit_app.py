import streamlit as st
import google.generativeai as genai
import requests
import pandas as pd
import time

# 1. PAGE CONFIG
st.set_page_config(page_title="Forensic Partner Intel", layout="wide", page_icon="🕵️")
st.title("🕵️ Forensic Truth Engine")

# 2. SECRETS & CONFIG
# Ensure these are set in your Streamlit Cloud Secrets or local .streamlit/secrets.toml
API_KEY = st.secrets["GEMINI_API_KEY"]
RENDER_URL = "https://partner-intelligence-engine.onrender.com"

# 3. PERSISTENCE LAYER
# This 'vault' survives the reruns that happen during AI function calling
if "evidence_list" not in st.session_state:
    st.session_state.evidence_list = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 4. THE ENGINE BRIDGE (The Tool)
def call_engine(target_company: str, portal_url: str):
    """
    Forensic tool to scrape partner portals and find tech-stack pain points.
    """
    # Forced delay to respect 2026 rate limits
    time.sleep(2) 
    
    payload = {
        "TARGET_COMPANY_NAME": target_company, 
        "PARTNER_PORTAL_URL": portal_url
    }
    
    try:
        r = requests.post(
            f"{RENDER_URL}/run", 
            json=payload, 
            headers={"x-engine-key": API_KEY},
            timeout=180
        )
        
        if r.status_code == 200:
            data = r.json()
            # LOCK DATA INTO STORAGE IMMEDIATELY
            results = data.get('QUOTES_TABLE', [])
            if results:
                st.session_state.evidence_list = results
            return data
        else:
            return {"error": f"Backend returned {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# 5. INITIALIZE AI (Gemini 2.5 Flash GA)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction="You are a Forensic Data Clerk. Extract partner pain points. ALWAYS list the Source URLs provided by the tool."
)

# 6. DISPLAY CHAT
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. MAIN INTERACTION
if prompt := st.chat_input("Analyze Lenovo at https://partnerexp.lenovo.com/"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # We start a chat session with automatic function calling enabled
        chat = model.start_chat(enable_automatic_function_calling=True)
        
        with st.status("🔍 Scraping live portal data...", expanded=True) as status:
            try:
                response = chat.send_message(prompt, tools=[call_engine])
                full_text = response.text
                st.markdown(full_text)
                st.session_state.chat_history.append({"role": "assistant", "content": full_text})
                status.update(label="Analysis Complete!", state="complete")
            except Exception as e:
                st.error(f"Quota/API Error: {e}")

# 8. THE LINK LOCKER (Guaranteed Visibility)
if st.session_state.evidence_list:
    st.divider()
    st.subheader("🔗 Verified Source Links")
    st.info("These URLs are pulled directly from the scraper, bypassing AI summarization.")
    
    df = pd.DataFrame(st.session_state.evidence_list)
    
    # Render clickable blue links
    st.dataframe(
        df,
        column_config={
            "source_url": st.column_config.LinkColumn("Clickable Source URL"),
            "quote": st.column_config.TextColumn("Evidence/Quote", width="large"),
            "observation": st.column_config.TextColumn("Observation")
        },
        hide_index=True,
        use_container_width=True
    )
