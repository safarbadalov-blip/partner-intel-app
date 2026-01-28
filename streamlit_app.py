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
# Ensure this matches your actual Render Dashboard URL exactly
RENDER_URL = "https://partner-intelligence-engine.onrender.com"

# Setup Gemini (Using the 'latest' alias to avoid 404 version errors)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- THE ENGINE TOOL ---
def call_engine(target_company: str, portal_url: str, mode: str = "FORENSIC_PLUS_INTERPRETATION"):
    """
    REQUIRED TOOL: Use this to perform a forensic partner intelligence check. 
    This tool scans the portal_url for tech stacks and searches the web for partner 
    pain points related to the target_company. 
    Inputs: target_company (name), portal_url (link), mode (default: FORENSIC_PLUS_INTERPRETATION).
    """
    try:
        payload = {
            "TARGET_COMPANY_NAME": target_company,
            "PARTNER_PORTAL_URL": portal_url,
            "EXECUTION_MODE": mode,
            "MAX_QUOTES": 5
        }
        # Send payload to Render backend /run endpoint
        # The 'x-engine-key' must match your ENGINE_API_KEY in Render env vars
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
        return f"Connection attempt failed. Render might be sleeping or timed out. Error: {str(e)}"

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Analyze Cohesity at https://partners.cohesity.com/s/login/"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Status spinner for long-running Render/Serper searches
        with st.status("Engine is scouring the web for partner pain...", expanded=True) as status:
            try:
                # Enable automatic function calling so Gemini 'clicks' the tool for you
                chat = model.start_chat(enable_automatic_function_calling=True)
                response = chat.send_message(prompt, tools=[call_engine])
                
                status.update(label="Forensic Analysis Complete!", state="complete", expanded=False)
                
                output_text = response.text
                st.markdown(output_text)
                st.session_state.messages.append({"role": "assistant", "content": output_text})
                
            except Exception as e:
                status.update(label="Error!", state="error", expanded=True)
                st.error(f"Something went wrong: {str(e)}")
