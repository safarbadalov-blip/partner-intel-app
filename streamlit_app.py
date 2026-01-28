import streamlit as st
import google.generativeai as genai
import requests

# --- APP CONFIG ---
st.set_page_config(page_title="Partner Intel Engine", page_icon="🤖")
st.title("🤖 Partner Intelligence Engine")

# 1. Brain Connection (We'll set the key in Streamlit Cloud next)
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Please add your GEMINI_API_KEY to Streamlit Secrets.")
    st.stop()

# 2. Engine Connection (Your Render URL)
RENDER_URL = "https://partner-intelligence-engine.onrender.com"

# Setup Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# --- THE ENGINE TOOL ---
def call_engine():
    """Checks your Render backend for partner data."""
    try:
        # Long timeout for the Render Free Tier wake-up
        r = requests.get(RENDER_URL, timeout=85) 
        return f"Engine Response: {r.text}"
    except Exception as e:
        return "The engine is taking a while to wake up. Please wait 20 seconds and try again."

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User types here
if prompt := st.chat_input("Ask about partner intelligence..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Querying Engine...", expanded=True) as status:
            # Create a fresh chat session with the tool enabled
            chat = model.start_chat(enable_automatic_function_calling=True)
            response = chat.send_message(prompt, tools=[call_engine])
            status.update(label="Engine Check Complete!", state="complete", expanded=False)
        
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
