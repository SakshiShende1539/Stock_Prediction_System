# Stock Prediction WhatsApp Agent — Complete Setup Guide

Full end-to-end guide from zero to working WhatsApp alerts.

---

## 🏗️ Architecture

```
    ┌──────────────────────┐
    │   FastAPI Server     │  ← Single source of truth
    │   Port: 5001         │    (real stock data + predictions)
    │   /predict endpoint  │
    └──────┬───────────────┘
           │
           ├──────────────┐
           ▼              ▼
    ┌──────────────┐  ┌──────────────┐
    │  Streamlit   │  │     n8n      │
    │  Port: 8501  │  │  Port: 5678  │
    │  Dashboard   │  │  Automation  │
    └──────────────┘  └──────┬───────┘
                             │
                             ▼
                      ┌─────────────┐
                      │   Twilio    │
                      │  WhatsApp   │
                      └─────────────┘
```

---

## 📋 Prerequisites

- **macOS / Linux / Windows** with a terminal
- **Python 3.9+** (`python3 --version`)
- **Node.js 18+** (`node --version`)
- **Twilio account** with WhatsApp sandbox enabled
- **Your phone** joined to the Twilio sandbox

---

## 🗂️ PART 1 — Project Setup

### Step 1.1: Create project folder

```bash
mkdir stock-agent
cd stock-agent
```

### Step 1.2: Save these 3 files in the folder

- `prediction_api.py` (FastAPI server)
- `app.py` (Streamlit dashboard)
- `Stock_Prediction_WhatsApp_Agent_BUY_only.json` (n8n workflow)

### Step 1.3: Create a Python virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### Step 1.4: Install Python dependencies

```bash
pip install fastapi uvicorn yfinance streamlit requests pandas plotly
```

---

## 🚀 PART 2 — Start FastAPI (Terminal 1)

FastAPI is the brain. It must start first because everything else depends on it.

### Step 2.1: Open Terminal 1

```bash
cd stock-agent
source venv/bin/activate
```

### Step 2.2: Start FastAPI

```bash
uvicorn prediction_api:app --host 0.0.0.0 --port 5001 --reload
```

### Step 2.3: Look for this success message

```
INFO:     Uvicorn running on http://0.0.0.0:5001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

### Step 2.4: Test it in a browser

Open:

```
http://localhost:5001/predict?symbol=RELIANCE
```

You should see JSON like this:

```json
{
  "symbol": "RELIANCE",
  "prediction": 2847.55,
  "short_ma": 2840.12,
  "long_ma": 2795.30,
  "signal": "BUY",
  "timestamp": "2026-04-19T18:20:33.123Z"
}
```

✅ **If you see JSON → Part 2 is done.**
❌ **If you see an error → STOP and fix it before moving on.**

### 🛑 KEEP THIS TERMINAL OPEN — do not close it.

---

## 🖥️ PART 3 — Start Streamlit Dashboard (Terminal 2)

### Step 3.1: Open a NEW terminal window (Cmd + N or Ctrl + Shift + T)

```bash
cd stock-agent
source venv/bin/activate
```

### Step 3.2: Start Streamlit

```bash
streamlit run app.py
```

### Step 3.3: Look for this success message

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

### Step 3.4: Open the dashboard

Your browser should open automatically. If not, visit:

```
http://localhost:8501
```

You'll see a dashboard with:
- ✅ Green "API online" banner at the top
- Live predictions for RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK
- BUY/SELL/HOLD counts
- Per-stock cards with prices
- Signal distribution chart
- Price comparison chart

### 🛑 KEEP THIS TERMINAL OPEN.

---

## 🔌 PART 4 — Twilio WhatsApp Setup (One-time)

### Step 4.1: Get Twilio credentials

1. Go to https://console.twilio.com
2. Sign up (free)
3. On the dashboard, copy:
   - **Account SID** (starts with `AC...`)
   - **Auth Token** (click "show")

### Step 4.2: Enable WhatsApp Sandbox

1. In Twilio Console → **Messaging → Try it out → Send a WhatsApp message**
2. You'll see a sandbox number: `+1 415 523 8886`
3. You'll see a join code like: `join <two-words>` (e.g., `join happy-tiger`)

### Step 4.3: Join the sandbox from YOUR phone

1. Open WhatsApp on your phone
2. Send a new message to `+1 415 523 8886`
3. Type the join code (e.g., `join happy-tiger`)
4. Send
5. Twilio replies: "Connected to sandbox. You can now receive messages..."

✅ **Your phone number is now whitelisted for Twilio WhatsApp.**

---

## ⚙️ PART 5 — Start n8n (Terminal 3)

### Step 5.1: Install n8n (one-time)

```bash
npm install -g n8n
```

### Step 5.2: Open a NEW terminal window

### Step 5.3: Start n8n

```bash
n8n start
```

### Step 5.4: Look for this success message

```
Editor is now accessible via:
http://localhost:5678
```

### Step 5.5: Open n8n in browser

```
http://localhost:5678
```

Create an owner account on first run.

### 🛑 KEEP THIS TERMINAL OPEN.

---

## 🔐 PART 6 — Add Twilio Credentials to n8n

### Step 6.1: In n8n, click **Credentials** (left sidebar)

### Step 6.2: Click **Add Credential** → search **Twilio** → select **Twilio API**

### Step 6.3: Fill in

- **Account SID**: paste from Twilio console
- **Auth Token**: paste from Twilio console

### Step 6.4: Click **Save**

Name it something like "Twilio account" — you'll reference this name next.

---

## 📥 PART 7 — Import the Workflow

### Step 7.1: In n8n, click **Workflows** (left sidebar)

### Step 7.2: Click **Add workflow** → top-right **"..."** menu → **Import from File**

### Step 7.3: Select `Stock_Prediction_WhatsApp_Agent_BUY_only.json`

### Step 7.4: Fix the HTTP Request URL

1. Click the **Get Prediction** node
2. Change the URL to:

```
http://host.docker.internal:5001/predict?symbol=RELIANCE
```

- If n8n is running **natively** (not Docker): use `http://localhost:5001/predict?symbol=RELIANCE`
- If n8n is running **in Docker**: use `http://host.docker.internal:5001/predict?symbol=RELIANCE`

### Step 7.5: Fix the Twilio credential

1. Click the **Send WhatsApp** node
2. In the **Credential** dropdown, select the Twilio credential you created in Part 6
3. Verify **From**: `whatsapp:+14155238886` (Twilio sandbox number — don't change)
4. Verify **To**: `whatsapp:+91XXXXXXXXXX` ← change to YOUR phone number (the one you joined the sandbox with)

### Step 7.6: Save the workflow

Click **Save** (top-right).

---

## ✅ PART 8 — Test End-to-End

### Step 8.1: Execute workflow manually

Click **Execute workflow** (big button at bottom of canvas).

### Step 8.2: Watch each node turn green

```
Cron Trigger ✓ → Get Prediction ✓ → Parse JSON ✓ → Is BUY Signal? ✓
                                                           ├── true → Send WhatsApp ✓ (if BUY)
                                                           └── false → Log Non-BUY ✓ (if not BUY)
```

### Step 8.3: Check outcomes

**If signal was BUY:**
- Send WhatsApp fires ✅
- Your phone receives a WhatsApp message

**If signal was SELL or HOLD:**
- Log Non-BUY fires ✅
- No WhatsApp sent (this is correct behavior)
- "Node was not executed" on Send WhatsApp is NORMAL

### Step 8.4: Force a BUY for testing

If you want to test WhatsApp without waiting for a real BUY signal:

1. Click **Is BUY Signal?** node
2. Temporarily change condition value from `BUY` to the current signal (e.g., `HOLD`)
3. Execute workflow
4. WhatsApp arrives
5. Change it back to `BUY`

---

## 🔄 PART 9 — Activate Automatic Runs

### Step 9.1: Toggle workflow to Active

Top-right of workflow screen: click the **Inactive** toggle → it turns **Active**.

### Step 9.2: Cron runs every 5 minutes

Now n8n automatically:
- Fetches prediction from FastAPI every 5 min
- If signal is BUY → sends WhatsApp
- Otherwise → logs the skip

---

## 🌐 Port Reference Sheet

| Service | Port | URL | Purpose |
|---|---|---|---|
| FastAPI | 5001 | http://localhost:5001 | Prediction engine |
| Streamlit | 8501 | http://localhost:8501 | Dashboard |
| n8n | 5678 | http://localhost:5678 | WhatsApp automation |
| Twilio Sandbox | — | +1 415 523 8886 | WhatsApp sender |

---

## 🖥️ Terminal Summary

You need **3 terminals open at once**:

**Terminal 1 — FastAPI**
```bash
cd stock-agent && source venv/bin/activate
uvicorn prediction_api:app --host 0.0.0.0 --port 5001 --reload
```

**Terminal 2 — Streamlit**
```bash
cd stock-agent && source venv/bin/activate
streamlit run app.py
```

**Terminal 3 — n8n**
```bash
n8n start
```

---

## 🐞 Troubleshooting

### Problem: "ERR_CONNECTION_REFUSED" on localhost:5678
**Fix**: n8n isn't running. Run `n8n start` in a terminal.

### Problem: Parse JSON shows "Invalid JSON from API" + Streamlit HTML
**Fix**: n8n URL is pointing at Streamlit (8501) instead of FastAPI (5001). Update Get Prediction URL.

### Problem: Signal is always NONE / UNKNOWN
**Fix**: FastAPI isn't running. Start it in Terminal 1.

### Problem: "Node was not executed" on Send WhatsApp
**Fix**: This is NORMAL. The signal wasn't BUY. Check Log Non-BUY node to see the actual signal returned.

### Problem: Twilio error "Channel with specified From not found"
**Fix**:
- From must be `whatsapp:+14155238886` (Twilio sandbox)
- To must be your number, and your number must have joined the sandbox

### Problem: WhatsApp not arriving even though workflow says it sent
**Fix**: You haven't joined the Twilio sandbox. Send `join <code>` to +14155238886 from your phone.

### Problem: n8n running in Docker can't reach FastAPI
**Fix**: Change the URL from `localhost` to `host.docker.internal`:
```
http://host.docker.internal:5001/predict?symbol=RELIANCE
```

### Problem: Port already in use
**Fix (macOS/Linux)**:
```bash
lsof -ti:5001 | xargs kill -9    # kills whatever's on port 5001
```

---

## ⏹️ How to Stop Everything

In each terminal, press **Ctrl + C**.

To restart later, just re-run each terminal's command.

---

## 🎯 Success Criteria Checklist

- [ ] `http://localhost:5001/predict?symbol=RELIANCE` returns JSON
- [ ] `http://localhost:8501` shows the dashboard with green "API online"
- [ ] `http://localhost:5678` loads n8n editor
- [ ] Twilio sandbox joined from your phone
- [ ] n8n workflow imported
- [ ] Get Prediction URL points to port 5001
- [ ] Twilio credentials attached to Send WhatsApp node
- [ ] "To" number matches your WhatsApp number
- [ ] Executing workflow turns all nodes green
- [ ] Forced BUY test delivers WhatsApp to your phone
- [ ] Workflow toggle set to Active

When all boxes are checked, you're done. 🚀
