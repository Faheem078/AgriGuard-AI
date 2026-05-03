import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from modules.vision     import classify_disease
from modules.weather    import get_weather_context
from modules.agent      import get_treatment_plan, estimate_yield_loss, SUPPORTED_LANGUAGES
from modules.pdf_report import generate_report
from modules.chatbot    import get_chatbot_response, get_mock_chatbot_response, QUICK_QUESTIONS
from config             import USE_REAL_VISION_MODEL, USE_REAL_FLOWISE_AGENT, USE_REAL_WEATHER_API, USE_REAL_GROQ_CHATBOT

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="AgriGuard AI", page_icon="🌿", layout="wide")

# ── Chatbot session state ──────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_disease" not in st.session_state:
    st.session_state.last_disease = None
if "last_weather" not in st.session_state:
    st.session_state.last_weather = None
if "quick_q_used" not in st.session_state:
    st.session_state.quick_q_used = None

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
:root {
    --green-deep: #1a3a2a; --green-mid: #2d6a4f; --green-leaf: #52b788;
    --green-light: #95d5b2; --green-pale: #d8f3dc; --cream: #f8f9f0;
    --text-primary: #1a2e1d; --text-soft: #4a6741; --shadow: rgba(45,106,79,0.15);
    --gold: #b45309; --gold-pale: #fff8e1; --gold-border: #fde68a;
    --red-pale: #fff1f0; --red-mid: #c0392b; --red-border: #fca5a5;
}
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--cream);
    font-family: 'DM Sans', sans-serif; color: var(--text-primary);
}
[data-testid="stSidebar"] { background: linear-gradient(160deg, var(--green-deep), #143326); }
[data-testid="stSidebar"] * { color: var(--green-pale) !important; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div,
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(149,213,178,0.4) !important;
    border-radius: 10px !important;
    color: var(--green-pale) !important;
}
[data-testid="stSidebar"] [data-testid="stNumberInput"] input {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(149,213,178,0.4) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] [data-testid="stNumberInput"] button {
    background: rgba(149,213,178,0.2) !important;
    border: 1px solid rgba(149,213,178,0.3) !important;
    color: var(--green-pale) !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] [data-testid="stNumberInput"] button:hover {
    background: rgba(149,213,178,0.35) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] * { color: var(--green-pale) !important; }
[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="icon"] { color: var(--green-pale) !important; }
#MainMenu, footer, header { visibility: hidden; }
.agri-hero {
    background: linear-gradient(135deg, var(--green-deep) 0%, var(--green-mid) 60%, var(--green-leaf) 100%);
    border-radius: 20px; padding: 2.5rem 3rem; margin-bottom: 2rem; position: relative; overflow: hidden;
}
.agri-hero::before { content:"🌿"; font-size:140px; position:absolute; right:2rem; top:-1rem; opacity:0.1; pointer-events:none; }
.agri-hero h1 { font-family:'DM Serif Display',serif; font-size:2.6rem; color:#fff; margin:0 0 .4rem; }
.agri-hero p  { color:var(--green-pale); font-size:1.05rem; font-weight:300; margin:0; }
.card { background:#fff; border-radius:16px; padding:1.6rem 1.8rem; box-shadow:0 4px 20px var(--shadow);
        border:1px solid rgba(149,213,178,.3); margin-bottom:1rem; }
.card-title { font-family:'DM Serif Display',serif; font-size:1.15rem; color:var(--green-mid); margin-bottom:.6rem; }
.badge { display:inline-block; padding:.25rem .85rem; border-radius:999px; font-size:.78rem; font-weight:600; }
.badge-success { background:var(--green-pale); color:var(--green-mid); border:1px solid var(--green-light); }
.badge-warn    { background:#fff8e1; color:#b45309; border:1px solid #fde68a; }
.badge-danger  { background:var(--red-pale); color:var(--red-mid); border:1px solid var(--red-border); }
.badge-mock    { background:#f0f0ff; color:#5555aa; border:1px solid #ccccee; }
.result-row { display:flex; align-items:flex-start; gap:.8rem; padding:.9rem 0; border-bottom:1px solid var(--green-pale); }
.result-row:last-child { border-bottom:none; }
.result-icon  { font-size:1.3rem; min-width:2rem; text-align:center; }
.result-label { font-size:.72rem; font-weight:600; text-transform:uppercase; letter-spacing:.8px; color:var(--text-soft); margin-bottom:.2rem; }
.result-value { font-size:.97rem; color:var(--text-primary); line-height:1.45; }
.yield-card {
    border-radius: 16px; padding: 1.4rem 1.8rem; margin-top: 1rem; margin-bottom: 1rem;
    box-shadow: 0 4px 20px var(--shadow);
}
.yield-card.severity-high   { background: linear-gradient(135deg, #fff1f0, #ffe4e1); border: 1px solid var(--red-border); }
.yield-card.severity-medium { background: linear-gradient(135deg, #fff8e1, #fef3c7); border: 1px solid var(--gold-border); }
.yield-card.severity-low    { background: linear-gradient(135deg, var(--green-pale), #c8f0d8); border: 1px solid var(--green-light); }
.yield-title { font-family:'DM Serif Display',serif; font-size:1.1rem; margin-bottom:.9rem; display:flex; align-items:center; gap:.5rem; }
.yield-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:.8rem; }
.yield-metric { text-align:center; background:rgba(255,255,255,0.65); border-radius:10px; padding:.7rem .5rem; }
.yield-metric-value { font-size:1.35rem; font-weight:700; line-height:1.1; }
.yield-metric-label { font-size:.68rem; text-transform:uppercase; letter-spacing:.7px; color:#6b6b6b; margin-top:.2rem; }
.yield-metric.loss .yield-metric-value  { color: var(--red-mid); }
.yield-metric.saved .yield-metric-value { color: var(--green-mid); }
.yield-metric.full .yield-metric-value  { color: #1a2e1d; }
.stButton>button { background:linear-gradient(135deg,var(--green-mid),var(--green-leaf));
    color:white!important; border:none!important; border-radius:10px!important;
    font-family:'DM Sans',sans-serif!important; font-weight:500!important; }
.stDownloadButton>button { background:var(--green-deep)!important; color:white!important;
    border-radius:10px!important; border:none!important; font-family:'DM Sans',sans-serif!important; }
[data-testid="stCameraInput"], [data-testid="stFileUploader"] {
    background:#fff!important; border:2px dashed var(--green-light)!important; border-radius:14px!important; }
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] input[type="number"],
[data-testid="stSidebar"] [data-baseweb="input"] input,
[data-testid="stSidebar"] [data-baseweb="base-input"] input {
    background: #1e4533 !important;
    background-color: #1e4533 !important;
    color: #d8f3dc !important;
    -webkit-text-fill-color: #d8f3dc !important;
    border: 1.5px solid #52b788 !important;
    border-radius: 8px !important;
    caret-color: #d8f3dc !important;
}
[data-testid="stSidebar"] [data-baseweb="base-input"],
[data-testid="stSidebar"] [data-baseweb="input"] {
    background: #1e4533 !important;
    background-color: #1e4533 !important;
    border: 1.5px solid #52b788 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] [data-testid="stNumberInput"] button,
[data-testid="stSidebar"] [data-baseweb="button"] {
    background: #2d6a4f !important;
    border: 1px solid #52b788 !important;
    color: #d8f3dc !important;
    border-radius: 6px !important;
}
/* ── invalid image banner ── */
.invalid-image-banner {
    background: linear-gradient(135deg, #fff1f0, #ffe8e6);
    border: 1.5px solid #fca5a5;
    border-radius: 16px;
    padding: 1.8rem 2rem;
    text-align: center;
    margin-bottom: 1rem;
}
.invalid-image-banner .inv-icon { font-size: 3rem; margin-bottom: .6rem; }
.invalid-image-banner h3 { color: #c0392b; font-family:'DM Serif Display',serif; margin: 0 0 .4rem; }
.invalid-image-banner p  { color: #7f1d1d; font-size: .92rem; margin: 0; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 AgriGuard AI")
    st.markdown("---")
    st.markdown("**Mission**  \nInstant AI crop diagnostics for smallholder farmers.")
    st.markdown("**🎯 SDGs**  \nSDG 1 · SDG 2 · SDG 12 · SDG 13")
    st.markdown("**📍 Region**  \nKarachi, Sindh, Pakistan")
    st.markdown("---")

    st.markdown("**🌐 Output Language**")
    selected_language = st.selectbox(
        "Choose language",
        options=list(SUPPORTED_LANGUAGES.keys()),
        index=0,
        label_visibility="collapsed",
    )
    language_code = SUPPORTED_LANGUAGES[selected_language]

    st.markdown("---")

    st.markdown("**🌾 Farm Details**")
    st.caption("Used to estimate economic impact")
    farm_acres = st.number_input(
        "Farm size (acres)",
        min_value=0.1,
        max_value=10000.0,
        value=1.0,
        step=0.5,
        help="Enter your total farm or plot size in acres",
    )

    st.markdown("---")

    st.markdown("**Integration Status**")
    def status(label, live): return f"{'🟢' if live else '🟡'} {label} ({'Live' if live else 'Mock'})"
    st.caption(status("Vision Model (M1)", USE_REAL_VISION_MODEL))
    st.caption(status("Flowise Agent (M4)", USE_REAL_FLOWISE_AGENT))
    st.caption(status("Weather API",        USE_REAL_WEATHER_API))
    st.caption(status("Groq Chatbot",       USE_REAL_GROQ_CHATBOT))

    st.markdown("---")

    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False

    chat_icon = "✕  Close Chat" if st.session_state.chat_open else "💬  Ask AgriGuard"
    if st.button(chat_icon, key="chat_toggle", use_container_width=True):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()

    st.markdown("""
    <style>
    [data-testid="stSidebar"] button[kind="secondary"],
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, rgba(82,183,136,0.25), rgba(45,106,79,0.35)) !important;
        border: 1.5px solid rgba(82,183,136,0.5) !important;
        border-radius: 12px !important;
        color: #d8f3dc !important;
        font-size: .9rem !important;
        font-weight: 500 !important;
        padding: .55rem 1rem !important;
        transition: background .2s, transform .15s !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, rgba(82,183,136,0.4), rgba(45,106,79,0.55)) !important;
        transform: scale(1.02) !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="agri-hero">
    <h1>Crop Disease Diagnostic</h1>
    <p>Capture or upload a crop photo — get an instant AI-powered, weather-aware treatment plan.</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# INPUT COLUMNS
# ─────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("<div class='card'><div class='card-title'>📷 Capture or Upload</div>", unsafe_allow_html=True)
    img_file      = st.camera_input("Take a photo")
    uploaded_file = st.file_uploader("Or upload from gallery", type=['jpg','png','jpeg'],
                                     label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

active_image = img_file or uploaded_file


# ─────────────────────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────────────────────
if active_image:
    with col2:
        st.markdown("<div class='card'><div class='card-title'>🔬 Analysis Results</div>", unsafe_allow_html=True)

        # ── Step 1: Vision (M1) ───────────────────────────────
        with st.spinner("Identifying disease…"):
            vision = classify_disease(active_image)

        # ── ✅ NEW: Check if image is not a plant ─────────────
        if vision.get("error") and vision.get("disease_name") in ("Not a Plant", "Uncertain"):
            st.markdown("</div>", unsafe_allow_html=True)  # close card
            st.markdown(f"""
            <div class="invalid-image-banner">
                <div class="inv-icon">🚫</div>
                <h3>{vision['disease_name']}</h3>
                <p>{vision.get('message', 'Please upload a clear photo of a plant or crop leaf.')}</p>
            </div>
            """, unsafe_allow_html=True)
            st.info("💡 **Tip:** Take a close-up photo of the affected leaf, stem, or fruit of your crop for best results.")
            st.stop()

        # ── Rest of pipeline only runs for valid plant images ──
        disease_name = vision["disease_name"]
        confidence   = int(vision.get("confidence", 0) * 100)
        severity     = vision.get("severity", "Medium")
        crop_type    = vision.get("crop_type", "Unknown Crop")
        mock_badge   = "" if USE_REAL_VISION_MODEL else "<span class='badge badge-mock'>Mock</span>"

        sev_badge_cls = {"High": "badge-danger", "Medium": "badge-warn", "Low": "badge-success"}.get(severity, "badge-warn")

        st.markdown(f"""
        <div class='result-row'>
            <div class='result-icon'>🦠</div>
            <div>
                <div class='result-label'>Detected Disease</div>
                <div class='result-value'><b>{disease_name}</b>
                    &nbsp;<span class='badge {sev_badge_cls}'>{severity} severity</span>
                    &nbsp;{mock_badge}
                    &nbsp;<span style='font-size:.85rem;color:#888'>{confidence}% confidence</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Step 2: Weather ───────────────────────────────────
        with st.spinner("Checking Karachi weather…"):
            weather = get_weather_context()

        rain_badge = "<span class='badge badge-warn'>Rain Expected</span>" if weather.get("rain_expected") \
                     else "<span class='badge badge-success'>No Rain</span>"

        st.markdown(f"""
        <div class='result-row'>
            <div class='result-icon'>🌦️</div>
            <div>
                <div class='result-label'>Weather · Karachi</div>
                <div class='result-value'>
                    {weather.get('condition')} · {weather.get('humidity_pct')}% humidity · {weather.get('temperature_c')}°C
                    &nbsp;{rain_badge}
                </div>
                <div class='result-value' style='margin-top:.3rem; color:#6b5c2e'>{weather.get("advice")}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Step 3: Groq Agent ────────────────────────────────
        with st.spinner("Consulting RAG treatment manuals…"):
            agent = get_treatment_plan(disease_name, weather, language_code)

        mock_badge4 = "" if USE_REAL_FLOWISE_AGENT else "<span class='badge badge-mock'>Mock</span>"
        lang_badge  = f"<span class='badge badge-success'>🌐 {selected_language}</span>" \
                      if language_code != "en" else ""

        st.markdown(f"""
        <div class='result-row'>
            <div class='result-icon'>💊</div>
            <div>
                <div class='result-label'>Treatment Plan &nbsp;{mock_badge4} &nbsp;{lang_badge}</div>
                <div class='result-value'>{agent.get('treatment')}</div>
            </div>
        </div>
        <div class='result-row'>
            <div class='result-icon'>⚠️</div>
            <div>
                <div class='result-label'>Precautions</div>
                <div class='result-value'>{agent.get('precautions')}</div>
            </div>
        </div>
        <div class='result-row'>
            <div class='result-icon'>📚</div>
            <div>
                <div class='result-label'>Source (RAG)</div>
                <div class='result-value' style='color:#888; font-size:.88rem'>{agent.get('rag_source', 'N/A')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)  # close analysis card

        # ── Step 4: Yield Loss Estimator ──────────────────────
        yield_data   = estimate_yield_loss(disease_name, severity, crop_type, farm_acres)
        loss_pct     = yield_data["loss_pct"]
        sev_css      = severity.lower()

        loss_icon = "🔴" if severity == "High" else ("🟡" if severity == "Medium" else "🟢")
        title_txt = (
            "Critical Economic Risk" if severity == "High"
            else ("Moderate Economic Risk" if severity == "Medium"
                  else "Low Economic Risk")
        )

        st.markdown(f"""
        <div class="yield-card severity-{sev_css}">
            <div class="yield-title">
                {loss_icon} Yield Loss Estimate — {title_txt}
            </div>
            <div class="yield-grid">
                <div class="yield-metric loss">
                    <div class="yield-metric-value">{loss_pct}%</div>
                    <div class="yield-metric-label">Est. Yield Loss</div>
                </div>
                <div class="yield-metric loss">
                    <div class="yield-metric-value">PKR {yield_data['lost_pkr']:,}</div>
                    <div class="yield-metric-label">Revenue at Risk</div>
                </div>
                <div class="yield-metric saved">
                    <div class="yield-metric-value">PKR {yield_data['saved_pkr']:,}</div>
                    <div class="yield-metric-label">If Treated Now</div>
                </div>
            </div>
            <div style="margin-top:.8rem; font-size:.8rem; color:#555; text-align:center;">
                Based on <b>{farm_acres} acre(s)</b> of <b>{crop_type}</b>
                · Full crop value: <b>PKR {yield_data['full_crop_pkr']:,}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Step 5: PDF Download ──────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        pdf_bytes = generate_report(vision, agent, weather, lang_code=language_code)
        st.download_button(
            label              = "📄 Download Full Treatment Report (PDF)",
            data               = pdf_bytes,
            file_name          = f"AgriGuard_{disease_name.replace(' ','_')}_Report.pdf",
            mime               = "application/pdf",
            use_container_width=True,
        )

        # Save diagnosis context for chatbot
        st.session_state.last_disease = disease_name
        st.session_state.last_weather = weather

else:
    with col2:
        st.markdown("""
        <div class='card' style='text-align:center; padding:3rem 2rem; opacity:.7;'>
            <div style='font-size:3rem; margin-bottom:1rem;'>🌱</div>
            <div class='card-title'>Awaiting Image</div>
            <p style='color:#4a6741; font-size:.9rem;'>
                Capture or upload a photo of your crop to begin analysis.
            </p>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# CHAT PANEL
# ─────────────────────────────────────────────────────────────
if st.session_state.get("chat_open", False):
    st.markdown("---")
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0f2318,#2d6a4f);border-radius:18px 18px 0 0;
         padding:1rem 1.4rem;display:flex;align-items:center;gap:.7rem;
         border:1px solid rgba(82,183,136,.3);border-bottom:none;">
        <span style="font-size:1.5rem;">🌿</span>
        <div>
            <div style="font-family:'DM Serif Display',serif;font-size:1.1rem;color:#d8f3dc;">
                AgriGuard Chat Assistant
            </div>
            <div style="font-size:.72rem;color:rgba(149,213,178,.75);">
                Ask about diseases, treatments, sprays &amp; prevention
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    chat_panel = st.container()
    with chat_panel:
        if st.session_state.chat_history:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    with st.chat_message("user", avatar="👨‍🌾"):
                        st.markdown(msg["content"])
                else:
                    with st.chat_message("assistant", avatar="🌿"):
                        st.markdown(msg["content"])
        else:
            st.markdown("""
            <div style="background:#f0faf4;border-radius:12px;padding:1.2rem 1.4rem;
                 border:1px solid #d8f3dc;color:#4a6741;font-size:.9rem;text-align:center;">
                👋 Hi! I'm AgriGuard. Ask me anything about crop diseases, treatments, or prevention.
            </div>
            """, unsafe_allow_html=True)

    st.markdown("**💡 Quick Questions:**")
    qcols = st.columns(3)
    for i, q in enumerate(QUICK_QUESTIONS):
        if qcols[i % 3].button(q[:38] + ("…" if len(q) > 38 else ""), key=f"quick_{i}", use_container_width=True):
            st.session_state.quick_q_used = q

    user_input = st.chat_input("Type your question here…")

    active_input = st.session_state.quick_q_used or user_input
    if st.session_state.quick_q_used:
        st.session_state.quick_q_used = None

    if active_input:
        st.session_state.chat_history.append({"role": "user", "content": active_input})
        with st.spinner("AgriGuard is thinking…"):
            if USE_REAL_GROQ_CHATBOT:
                reply = get_chatbot_response(
                    user_message    = active_input,
                    chat_history    = st.session_state.chat_history[:-1],
                    disease_context = st.session_state.last_disease,
                    weather_context = st.session_state.last_weather,
                    language_code   = language_code,
                )
            else:
                reply = get_mock_chatbot_response(active_input)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

