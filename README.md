---
title: AgriGuard AI
emoji: 🌿
colorFrom: green
colorTo: blue
sdk: docker
app_port: 8501
pinned: false
---


# 🌿 AgriGuard AI — Complete Setup Guide

A beginner-friendly guide to running AgriGuard AI on your computer from scratch.

---

## What is AgriGuard AI?

AgriGuard AI is a crop disease detection app for smallholder farmers in Karachi, Sindh. You take a photo of a sick crop, and the app tells you what disease it has, the local weather conditions, and exactly how to treat it. It also generates a downloadable PDF report.

**Aligned with:**
- SDG 1 — No Poverty
- SDG 2 — Zero Hunger
- SDG 12 — Responsible Production
- SDG 13 — Climate Action

---

## What You Need Before Starting

- A computer running Windows 10 or 11
- Internet connection
- VS Code installed (download from https://code.visualstudio.com)
- Python installed (download from https://python.org — click "Download Python 3.x")

> ⚠️ When installing Python, tick the box that says **"Add Python to PATH"** before clicking Install.

---

## Step 1 — Get Your API Keys

You need 3 free API keys. Get them before anything else.

---

### 1A. HuggingFace Token (for the Vision Model)

1. Go to https://huggingface.co
2. Click **Sign Up** — create a free account
3. Click your profile picture (top right) → **Settings** → **Access Tokens**
4. Click **New Token**
5. Name it anything (e.g. `agriguard`)
6. Select **Read** as the role
7. Click **Create token**
8. Copy the token — it starts with `hf_`

> ⚠️ You only see the token once. Copy it immediately.

---

### 1B. OpenWeatherMap Key (for Live Weather)

1. Go to https://openweathermap.org
2. Click **Sign Up** — create a free account
3. After signing in, click your username (top right) → **My API Keys**
4. Copy the **Default** key that's already there

> ⚠️ The key takes up to 10 minutes to activate after signup. If it gives an error, just wait.

---

### 1C. Groq API Key (for AI Treatment Plans)

1. Go to https://console.groq.com
2. Click **Sign Up** — create a free account
3. Click **API Keys** in the left sidebar
4. Click **Create API Key**
5. Copy the key — it starts with `gsk_`

---

## Step 2 — Set Up Your Project Folder

1. Create a new folder on your Desktop called `agriGuard`
2. Inside it, create these folders and files exactly:

```
agriGuard/
├── app.py
├── config.py
├── .env
├── modules/
│   ├── vision.py
│   ├── agent.py
│   ├── weather.py
│   └── pdf_report.py
└── mock/
    └── mock_data.json
```

3. Open VS Code
4. Click **File** → **Open Folder** → select your `agriGuard` folder

---

## Step 3 — Add Your API Keys

Open the `.env` file and paste this — replace the placeholders with your real keys:

```
HF_TOKEN=hf_your_huggingface_token_here
OPENWEATHER_API_KEY=your_openweathermap_key_here
GROQ_API_KEY=gsk_your_groq_key_here
```

> ⚠️ No spaces around the `=` sign. No quotes around the keys.

---

## Step 4 — Install Required Packages

Open the terminal in VS Code:
- Press **Ctrl + `** (backtick key, top left of keyboard)

Then paste this and press Enter:

```bash
pip install streamlit fpdf2 requests python-dotenv Pillow groq langchain
```

Wait for everything to install. It takes 2-5 minutes.

---

## Step 5 — Run the App

In the same terminal, make sure you are inside the `agriGuard` folder. Then run:

```bash
streamlit run app.py
```

Your browser will automatically open at:
```
http://localhost:8501
```

The app is now running. Upload a crop photo to test it.

---

## Step 6 — Open on Your Phone (Same WiFi)

1. Make sure your phone is connected to the **same WiFi** as your laptop
2. In the terminal, run:
```bash
ipconfig
```
3. Find the number next to **IPv4 Address** under **Wireless LAN adapter Wi-Fi**
   - It looks like: `192.168.1.5`
4. On your phone browser, go to:
```
http://192.168.1.5:8501
```
Replace with your actual number.

---

## Step 7 — Share With Anyone (ngrok)

To share the app with people not on your WiFi:

**Install ngrok:**
```bash
winget install Ngrok.Ngrok
```

**Sign up at** https://ngrok.com → copy your auth token from the dashboard

**Add your token:**
```bash
ngrok config add-authtoken your-token-here
```

**Open a second terminal** (Terminal → New Terminal in VS Code) and run:
```bash
ngrok http 8501
```

You will see a link like:
```
https://abc123.ngrok-free.app
```

Share this link with anyone — it works worldwide.

> ⚠️ Keep both terminals running. The link stops working if you close them.

---

## Understanding config.py

This is the most important file. It controls which parts are real vs mock (fake).

```python
USE_REAL_VISION_MODEL  = True    # True = real HuggingFace model
USE_REAL_WEATHER_API   = True    # True = real Karachi weather
USE_REAL_AGENT         = True    # True = real Groq AI treatment
USE_REAL_FLOWISE_AGENT = False   # Leave this False
```

Set any flag to `False` if that part isn't working — the app will use mock data instead and keep running.

---

## Project File Breakdown

| File | What it does |
|------|-------------|
| `app.py` | The main UI — runs the Streamlit interface |
| `config.py` | All settings and API keys in one place |
| `.env` | Your secret API keys — never share this file |
| `modules/vision.py` | Sends crop photo to HuggingFace and returns disease name |
| `modules/agent.py` | Sends disease to Groq AI and returns treatment plan |
| `modules/weather.py` | Fetches live weather from Karachi |
| `modules/pdf_report.py` | Generates the downloadable PDF report |
| `mock/mock_data.json` | Fake data used when APIs are turned off |

---

## How the Pipeline Works

```
📷 Farmer takes photo
        ↓
🦠 Vision Model (HuggingFace)
   Identifies the disease
        ↓
🌦️ Weather API (OpenWeatherMap)
   Checks Karachi humidity and rain
        ↓
🤖 AI Agent (Groq Llama 3)
   Generates treatment plan using RAG
        ↓
📄 PDF Report
   Farmer downloads and keeps it
```

---

## Common Errors and Fixes

| Error | Fix |
|-------|-----|
| `streamlit: command not found` | Run `python -m streamlit run app.py` |
| `ModuleNotFoundError` | Run `pip install streamlit fpdf2 requests python-dotenv Pillow` |
| `401 Unauthorized` | Your HuggingFace token is wrong — check `.env` file |
| `404 Not Found` | Wrong model ID in `config.py` |
| `Weather API error` | OpenWeatherMap key not activated yet — wait 10 minutes |
| `Groq error` | Check your Groq key in `.env` file |
| App not opening on phone | Make sure phone and laptop are on same WiFi |
| ngrok link not working | Make sure `streamlit run app.py` is running in another terminal |

---

## Stopping the App

In the terminal press:
```
Ctrl + C
```

---

## Important Notes

- Never share your `.env` file with anyone — it contains your secret keys
- The ngrok link changes every time you restart ngrok
- The HuggingFace model may take 20-30 seconds on first use — it wakes up from sleep
- All PDF reports are saved with the disease name in the filename so you can find them easily

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Vision AI | HuggingFace MobileNet V2 |
| Language AI | Llama 3 on Groq |
| RAG Pipeline | LangChain + FAISS |
| Weather | OpenWeatherMap API |
| PDF Generation | fpdf2 |
| Deployment | ngrok |

---

*AgriGuard AI · Hackathon Build · SDG 1 & SDG 2*
