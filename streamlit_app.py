import streamlit as st
import google.generativeai as genai
import requests
import pandas as pd

# 1. PAGE SETUP
st.set_page_config(page_title="Forensic Partner Intel", layout="wide", page_icon="🕵️")
st.title("🕵️ Forensic Truth Engine")

# 2. SECRETS & CONFIG
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Missing GEMINI_API_KEY in secrets.")
    st.stop()

API_KEY = st.secrets["GEMINI_API_KEY"]
RENDER_URL = "https://partner-intelligence-engine.onrender.com"

# 3. INITIALIZE SESSION STATE (Prevents losing data on refresh)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "evidence" not in st.session_state:
    st.session_state.evidence = None

# 4. THE "CLERK" PROMPT - Zero Hallucination Protocol
system_instruction = """
STRICT PROTOCOL: You are a DATA CLERK. 

1. You will receive a list of quotes and verified URLs.
2. YOU ARE FORBIDDEN from rewriting the URLs or shortening them.
3. YOUR MISSION: Prove that partner pain exists by listing the REMAINDER of the data.
4. If a fact is not directly supported by a 'source_url' in the tool output, DO NOT INCLUDE IT.
5. Every link MUST be clickable and exactly as provided.

PHASE 1: VERIFIED EVIDENCE TABLE
Create a Markdown table with these columns: [Observation | Supporting Quote | Source Link].
In the Source Link column, use the format: [View Source](URL)

PHASE 2: PROSPECTING EMAIL
Write a short, provocative email using ONLY the facts from the table above.
"""

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction=system_instruction)

# 5. ENGINE TOOL DEFINITION
def call_engine(target_company: str, portal_url: str):
    """
    REQUIRED: Performs a forensic search of the internet to find partner pain and 
    tech stack information for a specific company.
    """
    payload = {
        "TARGET_COMPANY_NAME": target_company, 
        "PARTNER_PORTAL_URL": portal_url,
        "EXECUTION_MODE": "FORENSIC_PLUS_INTERPRETATION"
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
            # Store evidence for the fail-safe table
            st.session_state.evidence = data
            return data
        return {"error": f"Backend failed with status {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# 6. DISPLAY CHAT HISTORY
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. MAIN LOGIC
if prompt := st.chat_input("Analyze Lenovo at https://partnerexp.lenovo.com/"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🔍 Searching web for verified evidence...", expanded=True):
            chat = model.start_chat(enable_automatic_function_calling=True)
            response = chat.send_message(prompt, tools=[call_engine])
            full_response = response.text
        
        st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# 8. THE FAIL-SAFE TABLE (The Truth Locker)
if st.session_state.evidence:
    st.divider()
    st.subheader("📂 Verification Locker (Direct Scraper Output)")
    st.info("The links below come directly from the scraper, bypassing the AI's creative summary.")
    
    quotes_data = st.session_state.evidence.get('QUOTES_TABLE', [])
    if quotes_data:
        df = pd.DataFrame(quotes_data)
        st.dataframe(
            df, 
            column_config={
                "source_url": st.column_config.LinkColumn("Verified Source Link"),
                "quote": st.column_config.TextColumn("Extracted Quote", width="large")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("No quotes were found for this specific query.")
