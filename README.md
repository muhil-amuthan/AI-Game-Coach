<div align="center">

# 🎮 AI Game Coach

**An AI-powered strategy assistant that analyzes your gameplay and tells you exactly what to improve in your next session.**

A full-stack web app with a Flask + JWT backend and a neon-styled static frontend. Choose your game (Chess, FPS, MOBA, RPG, Racing, RTS, Fighting, Puzzle…), chat with a game-specific AI coach, and get personalized tips backed by Gemini (with a graceful local fallback when no API key is configured).

</div>

---

## ✨ Features

- 🤖 **Game-aware AI coach** – Custom system prompts for 8 game categories plus a general mode
- 🧑‍💻 **Auth + Guest mode** – JWT-secured accounts, with a 5-message guest trial for visitors
- 💬 **Persistent chat history** – Per-user conversation memory using Gemini's chat API
- 💡 **Quick tips sidebar** – Static, game-specific advice served from the API
- 🏆 **Leaderboard** – Ranks users by messages sent
- 📊 **Profile & stats** – Tracks sessions, messages sent, favorite game, and rank points
- 🌐 **CORS-enabled API** – Drop-in compatible with any frontend
- 🛟 **Graceful fallback** – Works fully end-to-end even without a `GEMINI_API_KEY`

---

## 🧰 Tech Stack

| Layer    | Technology                                                 |
|----------|------------------------------------------------------------|
| Backend  | Python 3.10+, Flask 3, Flask-JWT-Extended, Flask-Bcrypt, Flask-CORS |
| AI       | Google Gemini 1.5 Flash (`google-generativeai`) with local-rule fallback |
| Frontend | Vanilla HTML / CSS / JavaScript (no build step)            |
| Data     | In-memory dictionaries (swap for Redis / a real DB in prod)|

---

## 📁 Project Structure

```
AI_Game_Coach/
├── backend/
│   ├── app.py              # Flask API: auth, chat, profile, history, leaderboard
│   ├── coach_agent.py      # Gemini-powered coaching agent + per-game tip DB
│   ├── requirements.txt
│   └── .env.example        # Copy to .env and fill in real keys
├── frontend/
│   ├── assets/
│   │   └── game-bg.jpg.jpeg
│   ├── index.html          # Landing page
│   ├── login.html          # Login / Register / Guest entry
│   ├── dashboard.html      # Chat-based coaching dashboard
│   └── style.css
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

You need **Python 3.10+** installed. A `GEMINI_API_KEY` is **optional** — without it the backend uses a deterministic local response so you can demo the full flow.

### 1. Clone & enter the project
```bash
git clone https://github.com/muhil-amuthan/AI-Game-Coach.git
cd AI-Game-Coach
```

### 2. Backend
```bash
cd AI_Game_Coach/backend

# Create & activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) configure environment variables
cp .env.example .env                   # then edit .env to add your Gemini key

# Start the server
python app.py
```
The API will be listening on **http://localhost:5000** and you should see:

```
🎮 AI Game Coach Backend Starting...
📡 API running at: http://localhost:5000
🔑 JWT Authentication: Enabled
🤖 Gemini AI: Connected       # or "fallback mode" if no key
```

### 3. Frontend
Open a new terminal:
```bash
cd AI_Game_Coach/frontend
python3 -m http.server 8080
```
Now visit **http://localhost:8080** in your browser.

> **Frontend API Connection:** The frontend automatically connects to `http://localhost:5000/api` during local development, and to your deployed Render URL in production. You can also click **⚙️ Configure API URL** anytime in the login/dashboard UI to switch environments on the fly.

---

## 🌐 Deploy to Render (Backend) & Vercel (Frontend)

This repository is pre-configured with **`render.yaml`** (for Render Blueprints) and **`vercel.json`** (for Vercel Edge Hosting).

```
                      ┌──────────────────────────────────────┐
                      │          Vercel (Frontend)           │
                      │  https://your-game-coach.vercel.app  │
                      └──────────────────┬───────────────────┘
                                         │
                                         │ HTTPS / REST API
                                         ▼
                      ┌──────────────────────────────────────┐
                      │           Render (Backend)           │
                      │ https://ai-game-coach.onrender.com   │
                      │            [Flask + JWT]             │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                                  Google Gemini API
```

---

### Step 1: Deploy the Backend on Render

You can deploy the backend using Render's Blueprint or as a standard Web Service.

#### Option A: 1-Click Blueprint (Recommended)
1. Push this repository to your GitHub account.
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** → **Blueprint**.
4. Connect your GitHub repository.
5. Render detects `render.yaml` automatically and configures:
   - **Runtime:** Python 3.11
   - **Plan:** Free
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
   - **Health Check Path:** `/api/health`
6. Under **Environment Variables**, provide your `GEMINI_API_KEY` (optional, for Gemini AI) and your `FRONTEND_URL` (your Vercel URL once created).
7. Click **Apply**.
8. Once deployed, copy your backend URL (e.g., `https://ai-game-coach-backend-xxxx.onrender.com`).
9. Verify by opening `https://<your-render-url>/api/health` in your browser. It should return `{"status":"online", ...}`.

#### Option B: Manual Web Service
1. In Render Dashboard, click **New +** → **Web Service**.
2. Select your repository.
3. Configure the settings:
   - **Root Directory:** `AI_Game_Coach/backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
   - **Plan:** Free
4. Under **Advanced** → **Health Check Path**, enter: `/api/health`
5. Under **Environment Variables**, add:
   - `FLASK_ENV` = `production`
   - `SECRET_KEY` = `(generate a random 64-char string)`
   - `JWT_SECRET_KEY` = `(generate a random 64-char string)`
   - `CORS_ORIGINS` = `*`
   - `GEMINI_API_KEY` = `(your Google Gemini API key)`
6. Click **Create Web Service**.

> **Note on Render Free Tier:** Render spins down free services after 15 minutes of inactivity. When a request arrives, it may take 30–50 seconds to wake up (cold start). The frontend has built-in detection and status messages to inform the user during wake-ups.

---

### Step 2: Deploy the Frontend on Vercel

1. Log in to [Vercel](https://vercel.com/) and click **Add New...** → **Project**.
2. Import your GitHub repository (`AI-Game-Coach`).
3. In **Project Settings**:
   - **Framework Preset:** Other
   - **Root Directory:** Leave as `./` (or select `AI_Game_Coach/frontend` — both work with the included `vercel.json` configs).
4. Click **Deploy**.
5. Once deployment completes, Vercel gives you a live production URL (e.g., `https://ai-game-coach-xxxx.vercel.app`).

---

### Step 3: Connect Frontend to Backend

You have two easy ways to point the frontend to your Render backend:

#### Method 1: Instant In-Browser Setup (Zero Code Change)
1. Open your live Vercel URL in your browser.
2. Click **Login** or **Dashboard**.
3. Click the **⚙️ Configure API URL** link at the bottom of the login card (or **⚙️ API Settings** on the dashboard sidebar).
4. Paste your Render backend URL (e.g., `https://ai-game-coach-backend-xxxx.onrender.com`).
5. Click **OK**. The frontend saves this to your browser storage and instantly connects!

#### Method 2: Default in Code (For All Users)
1. Open `AI_Game_Coach/frontend/config.js`.
2. Update line 10 with your live Render backend URL:
   ```javascript
   const DEFAULT_PROD_API = "https://<your-render-service>.onrender.com/api";
   ```
3. Commit and push to GitHub:
   ```bash
   git add AI_Game_Coach/frontend/config.js
   git commit -m "chore: set production Render backend URL"
   git push origin main
   ```
4. Vercel will automatically redeploy with the updated URL.

---

## 🔌 API Reference

Base URL: `http://localhost:5000/api`

| Method | Path                          | Auth   | Description                              |
|--------|-------------------------------|--------|------------------------------------------|
| GET    | `/api/health`                 | —      | Health check                             |
| POST   | `/api/register`               | —      | Create a new account                     |
| POST   | `/api/login`                  | —      | Log in, returns a JWT                    |
| POST   | `/api/logout`                 | JWT    | Log out (clears server-side history)     |
| GET    | `/api/user/profile`           | JWT    | Current user profile + stats             |
| GET    | `/api/user/history`           | JWT    | Full chat history (optional `?game=`)    |
| POST   | `/api/coach/chat`             | JWT    | Authenticated chat                       |
| POST   | `/api/coach/chat/guest`       | —      | Guest chat (5 messages max per session)  |
| POST   | `/api/coach/clear`            | JWT    | Clear conversation history               |
| GET    | `/api/coach/tips/<game_type>` | —      | Quick tips for a game                    |
| GET    | `/api/leaderboard`            | —      | Top 10 users by messages sent            |

### Example: register and chat
```bash
# 1) Register
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"hunter22","email":"alice@example.com"}'
# → { "access_token": "<JWT>", ... }

# 2) Chat
curl -X POST http://localhost:5000/api/coach/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT>" \
  -d '{"message":"What opening should I play as white?","game_type":"chess"}'
# → { "success": true, "response": "...", "quick_tips": [...], ... }
```

---

## ⚙️ Configuration

All settings are read from environment variables (loaded from `.env` if present). See `backend/.env.example` for the full list.

| Variable         | Purpose                                          | Default                                                       |
|------------------|--------------------------------------------------|---------------------------------------------------------------|
| `SECRET_KEY`     | Flask session signing key                        | development fallback (≥32 bytes)                              |
| `JWT_SECRET_KEY` | JWT signing key                                  | development fallback (≥32 bytes)                              |
| `GEMINI_API_KEY` | Enables real Gemini responses (optional)         | unset → uses local-rule fallback that still produces a reply  |

Get a Gemini key at <https://aistudio.google.com/app/apikey>.

---

## 🛠️ Troubleshooting

| Symptom                                           | Likely cause                                | Fix                                                                 |
|---------------------------------------------------|---------------------------------------------|---------------------------------------------------------------------|
| `Address already in use` when starting `app.py`   | Another process is on port 5000            | `lsof -i :5000` and kill it, or change the port in `app.py`        |
| `ModuleNotFoundError: flask`                      | Dependencies not installed                  | `pip install -r requirements.txt` inside your activated venv        |
| Frontend shows "Cannot connect to the server"     | Backend not running, or wrong API origin   | Start the backend first; check `API_BASE` in the page's JS         |
| `InsecureKeyLengthWarning` from PyJWT             | Custom `JWT_SECRET_KEY` shorter than 32 B  | Use a longer secret in `.env`                                       |
| Gemini answers are generic                        | `GEMINI_API_KEY` not set                    | Expected — fallback mode is deterministic. Add a key for real LLM.  |

---

## 🧪 Verifying the Install

A quick health check once both services are running:
```bash
curl http://localhost:5000/api/health
# → { "status": "online", "service": "AI Game Coach API", "version": "2.0.0", ... }
```

---

## 🗺️ Roadmap

- [ ] Swap the in-memory store for SQLite/Postgres + SQLAlchemy
- [ ] Persistent conversation history with search
- [ ] Voice input for the chat
- [ ] Streaming responses (server-sent events)
- [ ] More game categories (Smash Bros., Rocket League, Apex…)
- [ ] Docker Compose for one-command startup

---

## 📄 License

This project is provided as-is for educational and personal use. Add a `LICENSE` file if you plan to open-source it formally.

---

## 🙏 Credits

- Game system prompts curated from publicly available community knowledge
- Built with [Flask](https://flask.palletsprojects.com/) and [Google Gemini](https://aistudio.google.com/)
- Fonts: [Orbitron](https://fonts.google.com/specimen/Orbitron) and [Rajdhani](https://fonts.google.com/specimen/Rajdhani) via Google Fonts
