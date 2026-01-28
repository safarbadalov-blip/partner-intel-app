import streamlit as st
import google.generativeai as genai
import requests
import pandas as pd

# --- APP CONFIG ---
st.set_page_config(page_title="Partner Intel Engine", page_icon="🕵️", layout="wide")
st.title("🕵️ Partner Intel & Email Generator")

# 1. AUTH & CONNECTIONS
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("🚨 Missing GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

RENDER_URL = "https://partner-intelligence-engine.onrender.com"

# 2. THE DUAL-PHASE BRAIN (System Instruction)
system_instruction = """
You are a 'Commercial Forensic Analyst'. Your job is to find leverage and then use it.

When you receive the partner intelligence data, your output must follow this STRICT 2-PART FORMAT:

---
### 🔎 PART 1: THE SMOKING GUNS (Verifiable Facts)
List the top 3-5 most critical 'pain points' or 'quotes' found in the data.
* **Format:** Bullet points.
* **CRITICAL RULE:** You MUST include the (Source URL) next to every single fact. Do not hallucinate URLs. If it's in the data, cite it.

---
### ✉️ PART 2: THE OUTBOUND EMAIL (Creative Execution)
Write a prospecting email to the 'VP of Channels' at this company. 
* **Tone:** Professional but slightly provocative. "Challenger Sale" style.
* **Strategy:** Use the facts from Part 1 as the 'hook'. 
* **Subject Line:** Give 2 punchy options.
* **Body:** "I was analyzing your partner ecosystem and noticed [Quote/Fact from Part 1]..."
* **Call to Action:** Specific low-friction ask.
"""

genai.configure(api_key=API_KEY)

# --- CORRECTED MODEL VERSION (Gemini 3) ---
model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction=system_instruction)

# --- THE ENGINE TOOL ---
def call_engine(target_company: str, portal_url: str, mode: str = "FORENSIC_PLUS_INTERPRETATION"):
    """
    Scans the partner portal for tech stack and searches the web for partner pain points.
    """
    try:
        with st.spinner(f"🔍 Forensic scan initiated on {target_company}..."):
            payload = {
                "TARGET_COMPANY_NAME": target_company,
                "PARTNER_PORTAL_URL": portal_url,
                "EXECUTION_MODE": mode,
                "MAX_QUOTES": 7
            }
            
            # Hit your backend
            r = requests.post(
                f"{RENDER_URL}/run", 
                json=payload, 
                headers={"x-engine-key": API_KEY}, 
                timeout=180
            )
            
            if r.status_code == 200:
                data = r.json()
                # SAVE THE RAW EVIDENCE so we can display the table later
                st.session_state['latest_evidence'] = data
                return data
            else:
                return f"Backend error: {r.status_code}. Details: {r.text}"
            
    except Exception as e:
        return f"Connection failed. Error: {str(e)}"

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input Area
if prompt := st.chat_input("Ex: 'Analyze Cohesity at https://partners.cohesity.com'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Clear old evidence so the table updates
            if 'latest_evidence' in st.session_state:
                del st.session_state['latest_evidence']

            # Run the AI
            chat = model.start_chat(enable_automatic_function_calling=True)
            response = chat.send_message(prompt, tools=[call_engine])
            
            # Show the text response (The Facts + The Email)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

            # --- THE TRUTH TABLE (Evidence Locker) ---
            # This runs AFTER the AI response to show the raw data
            if 'latest_evidence' in st.session_state:
                evidence = st.session_state['latest_evidence']
                
                st.divider()
                st.subheader("📂 Reference Data (The Evidence Locker)")
                st.info("Below is the raw, unedited data found by the engine.")
                
                # 1. Tech Stack
                if "TECH_STACK" in evidence and evidence["TECH_STACK"]:
                    with st.expander("🛠️ See Detected Tech Stack", expanded=False):
                        st.json(evidence["TECH_STACK"])

                # 2. Quotes Table with CLICKABLE LINKS
                if "QUOTES_TABLE" in evidence and evidence["QUOTES_TABLE"]:
                    df = pd.DataFrame(evidence["QUOTES_TABLE"])
                    
                    # Configure the table to show clickable links
                    st.dataframe(
                        df,
                        column_config={
                            "source_url": st.column_config.LinkColumn(
                                "Source URL",
                                display_text="🔗 Open Source"
                            ),
                            "quote": st.column_config.TextColumn(
                                "Quote",
                                width="large"
                            ),
                            "score": st.column_config.NumberColumn(
                                "Relevance Score",
                                format="%d ⭐"
                            )
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("No direct quotes found in this scan.")
            
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")
