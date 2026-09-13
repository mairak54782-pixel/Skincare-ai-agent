"""
BellaAI - Smart Skincare Assistant for Pakistan
-------------------------------------------------
A Streamlit app that generates personalized skincare routines,
analyzes skin descriptions, and answers skincare questions -
tailored for the Pakistani climate and locally available brands.

Author: <Maira>
"""

import streamlit as st
import os
from dotenv import load_dotenv
from utils.ai_engine import call_skincare_ai, generate_pdf

# ─── SETUP ───────────────────────────────────────────────
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    try:
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        GROQ_API_KEY = ""

st.set_page_config(
    page_title="BellaAI | Smart Skincare Assistant",
    page_icon="🌸",
    layout="centered",
)

# ─── STYLING ─────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #fff5f8; }
    .res-card {
        background: white; padding: 25px; border-radius: 15px;
        border-left: 5px solid #ff4d94; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        color: #333;
    }
    .stButton>button {
        background: linear-gradient(90deg, #ff80b5, #ff4d94);
        color: white; border-radius: 25px; font-weight: bold;
        border: none; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(255, 77, 148, 0.4);
    }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────
with st.sidebar:
    st.header("🌸 About BellaAI")
    st.write(
        "BellaAI is an AI-powered skincare assistant built for Pakistani "
        "users, factoring in local climate and locally available brands."
    )
    st.markdown("**Tech stack:** Streamlit · Groq (Llama 3.1) · ReportLab")
    st.markdown("[View source on GitHub](https://github.com/mairak54782-pixel/Skincare-ai-agent)")
    st.divider()
    st.caption(
        "⚕️ Disclaimer: BellaAI provides general skincare guidance only "
        "and is not a substitute for professional medical advice. "
        "Please consult a licensed dermatologist for serious or persistent concerns."
    )

if not GROQ_API_KEY:
    st.error(
        "⚠️ No API key found. Add `GROQ_API_KEY` to a `.env` file locally, "
        "or to your Streamlit Cloud secrets before deploying."
    )

# ─── UI LAYOUT ───────────────────────────────────────────
st.title("🌸 BellaAI — Smart Skincare Assistant")
st.caption("Science-backed skincare guidance, tailored for Pakistan 🇵🇰")

tab1, tab2, tab3 = st.tabs(["✨ Get Routine", "🔍 Skin Analysis", "💬 Skincare Expert"])

# --- TAB 1: ROUTINE GENERATOR ---
with tab1:
    st.subheader("Personalized Protocol")
    c1, c2 = st.columns(2)
    with c1:
        skin = st.selectbox("Skin Type", ["Oily", "Dry", "Combination", "Sensitive", "Normal"])
        season = st.selectbox("Season", ["Spring", "Summer", "Autumn", "Winter"])
    with c2:
        age = st.slider("Age", 12, 75, 25)
        concerns = st.multiselect("Concerns", [
            "Acne", "Dullness", "Dark Spots", "Dryness",
            "Aging/Wrinkles", "Sun Damage", "Open Pores",
            "Blackheads", "Uneven Tone", "Redness"
        ])

    if st.button("Generate Professional Routine", key="routine_btn"):
        if not concerns:
            st.error("Please select at least one skin concern.")
        else:
            with st.spinner("Consulting AI dermatologist..."):
                result = call_skincare_ai(
                    GROQ_API_KEY, "routine",
                    skin=skin, season=season, age=age, concerns=concerns,
                )
                st.session_state["last_routine"] = result

    if st.session_state.get("last_routine"):
        st.markdown(f'<div class="res-card">{st.session_state["last_routine"]}</div>', unsafe_allow_html=True)
        pdf_bytes = generate_pdf("Your Personalized Skincare Routine", st.session_state["last_routine"])
        st.download_button(
            "📄 Download as PDF", data=pdf_bytes,
            file_name="skincare_routine.pdf", mime="application/pdf",
        )

# --- TAB 2: SKIN ANALYSIS ---
with tab2:
    st.subheader("Text-Based Diagnostic")
    desc = st.text_area(
        "Describe your skin texture, feeling, or recent changes:",
        placeholder="e.g., My skin feels tight after washing but gets very oily by 2 PM...",
    )
    if st.button("Analyze My Skin", key="analyze_btn"):
        if len(desc) < 10:
            st.warning("Please provide a bit more detail for an accurate analysis.")
        else:
            with st.spinner("Analyzing patterns..."):
                res = call_skincare_ai(
                    GROQ_API_KEY, "chat",
                    query=f"Analyze this description and give 3 expert tips: {desc}",
                )
                st.markdown(f'<div class="res-card">{res}</div>', unsafe_allow_html=True)

# --- TAB 3: SMART CHATBOT ---
with tab3:
    st.subheader("Skincare Concierge")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if p := st.chat_input("Ask about ingredients, products, or myths..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"):
            st.markdown(p)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                r = call_skincare_ai(GROQ_API_KEY, "chat", query=p)
                st.markdown(r)
                st.session_state.messages.append({"role": "assistant", "content": r})

st.divider()
st.caption("Fast. Reliable. Professional. | © 2026 BellaAI")
