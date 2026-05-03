# ══════════════════════════════════════════════════════════════════
#  HOW TO ADD THE CHATBOT TO YOUR app.py
#  Copy-paste these blocks into your existing app.py file
# ══════════════════════════════════════════════════════════════════

# ── STEP 1: Add this import at the TOP of app.py (with other imports) ──────
from modules.chatbot import get_chatbot_response, get_mock_chatbot_response, QUICK_QUESTIONS
from config import USE_REAL_GROQ_CHATBOT   # add this flag to config.py (see Step 5)


# ── STEP 2: Add this session state init block near the top of app.py ───────
#    (after st.set_page_config, before the sidebar section)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_disease" not in st.session_state:
    st.session_state.last_disease = None

if "last_weather" not in st.session_state:
    st.session_state.last_weather = None

if "quick_q_used" not in st.session_state:
    st.session_state.quick_q_used = None


# ── STEP 3: After your diagnosis pipeline block (after the PDF button), ─────
#    paste this entire chatbot section:

st.markdown("---")
st.markdown("## 💬 Ask AgriGuard — Farmer Chat Assistant")
st.caption("Ask any question about crop diseases, treatments, or prevention.")

# Save diagnosis context for chatbot
if active_image and "vision" in dir():        # if diagnosis was run
    st.session_state.last_disease = disease_name
    st.session_state.last_weather = weather

# ── Quick question buttons ────────────────────────────────────
st.markdown("**Quick Questions:**")
cols = st.columns(3)
for i, q in enumerate(QUICK_QUESTIONS):
    if cols[i % 3].button(q[:45] + ("…" if len(q) > 45 else ""), key=f"quick_{i}"):
        st.session_state.quick_q_used = q

# ── Chat history display ──────────────────────────────────────
chat_container = st.container()
with chat_container:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👨‍🌾"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🌿"):
                st.markdown(msg["content"])

# ── Input box ─────────────────────────────────────────────────
user_input = st.chat_input("Type your question here… (e.g. 'What spray for late blight?')")

# Handle quick question OR typed input
active_input = st.session_state.quick_q_used or user_input
if st.session_state.quick_q_used:
    st.session_state.quick_q_used = None   # reset after use

if active_input:
    # Append user message to history
    st.session_state.chat_history.append({"role": "user", "content": active_input})

    with st.spinner("AgriGuard is thinking…"):
        if USE_REAL_GROQ_CHATBOT:
            reply = get_chatbot_response(
                user_message    = active_input,
                chat_history    = st.session_state.chat_history[:-1],  # exclude current msg
                disease_context = st.session_state.last_disease,
                weather_context = st.session_state.last_weather,
                language_code   = language_code,
            )
        else:
            reply = get_mock_chatbot_response(active_input)

    # Append assistant reply to history
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    st.rerun()

# ── Clear chat button ─────────────────────────────────────────
if st.session_state.chat_history:
    if st.button("🗑️ Clear Chat", key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()


# ── STEP 4: Add to requirements.txt ─────────────────────────────────────────
#    groq   (add this line if not already present)


# ── STEP 5: Add to config.py ────────────────────────────────────────────────
#    Add this one line to your config.py file:
#
#    USE_REAL_GROQ_CHATBOT = True   # False = mock replies, True = live Groq Llama 3
#
#    Your existing GROQ_API_KEY in .env is reused — no new key needed!


# ── STEP 6: Install Groq SDK (run once in terminal) ──────────────────────────
#    pip install groq
