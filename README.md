# AI-Game-Coach
A project that analyzes gameplay improvements and highlights what to improve in your next session for small games and strategy-based experiences.

## Project Structure
```
AI_Game_Coach/
├── backend/
│   ├── app.py              # Flask API (auth, chat, profile, history, etc.)
│   ├── coach_agent.py      # Gemini-powered coaching agent + tip DB
│   ├── requirements.txt
│   └── .env.example        # Copy to .env and fill in real keys
├── frontend/
│   ├── assets/
│   │   └── game-bg.jpg.jpeg
│   ├── index.html          # Landing page
│   ├── login.html          # Login / Register / Guest
│   ├── dashboard.html      # Chat-based coaching dashboard
│   └── style.css
└── README.md
```

## Features
- **Authentication** – JWT-based register / login / logout (in-memory user store)
- **Guest mode** – Try the chat without an account (5 messages)
- **AI Coach** – Game-specific system prompts for Chess, FPS, MOBA, RPG, Racing, RTS, Fighting, Puzzle
- **Quick tips** – Per-game static tips served from `/api/coach/tips/<game>`
- **Profile & history** – Per-user chat history and stats
- **Leaderboard** – Top users ranked by messages sent
- **Graceful fallback** – If `GEMINI_API_KEY` is missing, the backend still works using a deterministic local response

## Frontend Pages
- Home page: `index.html`
- Login page: `login.html`
- Dashboard: `dashboard.html`

## Quick Start

### 1. Backend
```bash
cd AI_Game_Coach/backend

# (optional) create a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# (optional) set up environment variables
cp .env.example .env               # then edit .env to add your Gemini key

# run the server
python app.py
```
The API will be available at **http://localhost:5000**.

The server prints a startup banner, then runs Flask in debug mode on `0.0.0.0:5000`.

### 2. Frontend
You can open the HTML files directly, but for the dashboard to call the API with
no CORS issues the easiest approach is to serve the `frontend/` directory with
any static file server, e.g.:

```bash
cd AI_Game_Coach/frontend
python3 -m http.server 8080
```
Then visit **http://localhost:8080** in your browser.

The login/dashboard pages talk to `http://localhost:5000/api` by default. If you
host the frontend on a different port, just adjust the `API_BASE` constant at
the top of each page's `<script>` block, or use a reverse proxy.

## API Endpoints
| Method | Path                        | Auth | Description                            |
|--------|-----------------------------|------|----------------------------------------|
| GET    | `/api/health`               | –    | Health check                           |
| POST   | `/api/register`             | –    | Create a new account                   |
| POST   | `/api/login`                | –    | Log in                                 |
| POST   | `/api/logout`               | JWT  | Log out (clears server-side history)   |
| GET    | `/api/user/profile`         | JWT  | Current user profile + stats           |
| GET    | `/api/user/history`         | JWT  | Full chat history (optional `?game=`)  |
| POST   | `/api/coach/chat`           | JWT  | Authenticated chat                     |
| POST   | `/api/coach/chat/guest`     | –    | Guest chat (5 messages max)            |
| POST   | `/api/coach/clear`          | JWT  | Clear conversation history             |
| GET    | `/api/coach/tips/<game>`    | –    | Quick tips for a game                  |
| GET    | `/api/leaderboard`          | –    | Top 10 users by messages sent          |

## Configuration
Environment variables (loaded from `.env` if present):

| Variable         | Purpose                                              | Default                            |
|------------------|------------------------------------------------------|------------------------------------|
| `SECRET_KEY`     | Flask session signing                                | `ai-game-coach-secret-2026`        |
| `JWT_SECRET_KEY` | JWT signing                                          | `jwt-secret-key-2026`              |
| `GEMINI_API_KEY` | Enables real Gemini responses (optional)             | unset → uses local fallback        |
