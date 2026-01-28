import streamlit as st
import google.generativeai as genai
import requests

# --- APP CONFIG ---
st.set_page_config(page_title="Partner Intel Engine", page_icon="🤖")
st.title("🤖 Partner Intelligence Engine")

# 1. BRAIN CONNECTION (Secrets)
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Please add your GEMINI_API_KEY to Streamlit Secrets.")
    st.stop()

# 2. ENGINE CONNECTION (Your Render URL)
RENDER_URL = "https://partner-intelligence-engine.onrender.com"

# Setup Gemini (Updated to Gemini 3 Flash for 2026 API keys)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- THE ENGINE TOOL ---
def call_engine(target_company: str, portal_url: str, mode: str = "FORENSIC_PLUS_INTERPRETATION"):
    """
    REQUIRED TOOL: Use this to perform a forensic partner intelligence check. 
    It scans the portal_url for tech stacks and searches the web for partner 
    pain points related to the target_company. 
    """
    try:
        payload = {
            "TARGET_COMPANY_NAME": target_company,
            "PARTNER_PORTAL_URL": portal_url,
            "EXECUTION_MODE": mode,
            "MAX_QUOTES": 5
        }
        # Send payload to Render backend
        r = requests.post(
            f"{RENDER_URL}/run", 
            json=payload, 
            headers={"x-engine-key": API_KEY}, 
            timeout=180
        )
        
        if r.status_code == 200:
            return r.json()
        else:
            return f"Backend error: {r.status_code}. Details: {r.text}"
            
    except Exception as e:
        return f"Connection failed. Error: {str(e)}"

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Analyze Cohesity at https://partners.cohesity.com/s/login/"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Engine is scouring the web for partner pain...", expanded=True) as status:
            try:
                # Automatic function calling allows Gemini to use 'call_engine'
                chat = model.start_chat(enable_automatic_function_calling=True)
                response = chat.send_message(prompt, tools=[call_engine])
                
                status.update(label="Forensic Analysis Complete!", state="complete", expanded=False)
                
                output_text = response.text
                st.markdown(output_text)
                st.session_state.messages.append({"role": "assistant", "content": output_text})
                
            except Exception as e:
                status.update(label="Error!", state="error", expanded=True)
                st.error(f"Something went wrong: {str(e)}")
