import streamlit as st
import google.generativeai as genai
import requests

# --- APP CONFIG ---
st.set_page_config(page_title="Partner Intel Engine", page_icon="🤖")
st.title("🤖 Partner Intelligence Engine")

# 1. BRAIN CONNECTION
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Please add your GEMINI_API_KEY to Streamlit Secrets.")
    st.stop()

# 2. ENGINE CONNECTION (Your Render URL)
RENDER_URL = "https://partner-intelligence-engine.onrender.com"

# Setup Gemini (Using FLASH for better compatibility)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- THE ENGINE TOOL ---
def call_engine():
    """Fetches real-time data from your Render backend."""
    try:
        # Long timeout because Render Free Tier is slow to wake up
        r = requests.get(RENDER_URL, timeout=90) 
        if r.status_code == 200:
            return f"The Engine is LIVE. Backend says: {r.text}"
        else:
            return f"Backend responded with code {r.status_code}. It might still be booting up."
    except Exception as e:
        return f"Connection attempt failed. Render might be sleeping. Error: {str(e)}"

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about partner intelligence..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # We use st.status so you can see it working while Render wakes up
        with st.status("Gemini is reaching out to your engine...", expanded=True) as status:
            try:
                # Start chat with automatic tool calling
                chat = model.start_chat(enable_automatic_function_calling=True)
                response = chat.send_message(prompt, tools=[call_engine])
                status.update(label="Engine Check Complete!", state="complete", expanded=False)
                
                output_text = response.text
                st.markdown(output_text)
                st.session_state.messages.append({"role": "assistant", "content": output_text})
            except Exception as e:
                status.update(label="Error!", state="error", expanded=True)
                st.error(f"Something went wrong: {str(e)}")
