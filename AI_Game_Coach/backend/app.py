from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from flask_bcrypt import Bcrypt
from coach_agent import get_coach_response, clear_session, get_session_stats
from dotenv import load_dotenv
import os
import uuid
from datetime import timedelta, datetime

load_dotenv()

# ─────────────────────────────────────────────
#  App Configuration
# ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv(
    "SECRET_KEY",
    "ai-game-coach-development-secret-key-change-me-2026-please",
)
app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY",
    "jwt-development-secret-key-change-me-2026-please-use-32-bytes",
)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

CORS(app, origins=["*"], supports_credentials=True)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# ─────────────────────────────────────────────
#  In-Memory "Database" (replace with real DB)
# ─────────────────────────────────────────────
users_db = {}        # { username: { password_hash, email, created_at, stats } }
chat_logs_db = {}    # { username: [ {game, message, response, timestamp} ] }

# ─────────────────────────────────────────────
#  Helper Functions
# ─────────────────────────────────────────────
def get_user(username: str) -> dict | None:
    return users_db.get(username)


def save_chat_log(username: str, game: str, message: str, response: str):
    if username not in chat_logs_db:
        chat_logs_db[username] = []
    chat_logs_db[username].append({
        "game": game,
        "message": message,
        "response": response,
        "timestamp": datetime.now().isoformat()
    })
    # Keep only last 100 messages per user
    chat_logs_db[username] = chat_logs_db[username][-100:]


# ─────────────────────────────────────────────
#  Auth Routes
# ─────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def register():
    """Register a new user."""
    try:
        data = request.get_json()

        username = data.get("username", "").strip().lower()
        password = data.get("password", "").strip()
        email    = data.get("email", "").strip().lower()

        # ── Validation ────────────────────────────────────────────────
        if not username or not password or not email:
            return jsonify({
                "success": False,
                "message": "Username, password, and email are required."
            }), 400

        if len(username) < 3:
            return jsonify({
                "success": False,
                "message": "Username must be at least 3 characters."
            }), 400

        if len(password) < 6:
            return jsonify({
                "success": False,
                "message": "Password must be at least 6 characters."
            }), 400

        if "@" not in email:
            return jsonify({
                "success": False,
                "message": "Invalid email address."
            }), 400

        if username in users_db:
            return jsonify({
                "success": False,
                "message": "Username already taken. Please choose another."
            }), 409

        # Check email uniqueness
        for u in users_db.values():
            if u["email"] == email:
                return jsonify({
                    "success": False,
                    "message": "Email already registered."
                }), 409

        # ── Create user ───────────────────────────────────────────────
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        users_db[username] = {
            "password_hash": password_hash,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "stats": {
                "sessions": 0,
                "messages_sent": 0,
                "favorite_game": "general",
                "rank_points": 0
            }
        }

        # Create JWT token
        access_token = create_access_token(identity=username)

        return jsonify({
            "success": True,
            "message": f"Welcome to AI Game Coach, {username}! 🎮",
            "access_token": access_token,
            "username": username,
            "email": email
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Registration failed. Please try again.",
            "error": str(e)
        }), 500


@app.route("/api/login", methods=["POST"])
def login():
    """Login an existing user."""
    try:
        data = request.get_json()

        username = data.get("username", "").strip().lower()
        password = data.get("password", "").strip()

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username and password are required."
            }), 400

        user = get_user(username)

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid username or password."
            }), 401

        if not bcrypt.check_password_hash(user["password_hash"], password):
            return jsonify({
                "success": False,
                "message": "Invalid username or password."
            }), 401

        # Update session count
        users_db[username]["stats"]["sessions"] += 1

        access_token = create_access_token(identity=username)

        return jsonify({
            "success": True,
            "message": f"Welcome back, {username}! 🎮",
            "access_token": access_token,
            "username": username,
            "email": user["email"],
            "stats": user["stats"]
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Login failed. Please try again.",
            "error": str(e)
        }), 500


@app.route("/api/logout", methods=["POST"])
@jwt_required()
def logout():
    """Logout user (clear their session history)."""
    username = get_jwt_identity()
    clear_session(f"session_{username}")
    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    }), 200


# ─────────────────────────────────────────────
#  User Routes
# ─────────────────────────────────────────────
@app.route("/api/user/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get user profile and stats."""
    username = get_jwt_identity()
    user = get_user(username)

    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    chat_history = chat_logs_db.get(username, [])

    return jsonify({
        "success": True,
        "username": username,
        "email": user["email"],
        "created_at": user["created_at"],
        "stats": user["stats"],
        "recent_sessions": chat_history[-5:],  # Last 5 chats
        "total_chats": len(chat_history)
    }), 200


@app.route("/api/user/history", methods=["GET"])
@jwt_required()
def get_history():
    """Get full chat history for user."""
    username = get_jwt_identity()
    game_filter = request.args.get("game", None)

    history = chat_logs_db.get(username, [])

    if game_filter:
        history = [h for h in history if h["game"] == game_filter]

    return jsonify({
        "success": True,
        "history": history,
        "total": len(history)
    }), 200


# ─────────────────────────────────────────────
#  Coach Routes
# ─────────────────────────────────────────────
@app.route("/api/coach/chat", methods=["POST"])
@jwt_required()
def chat():
    """Main coaching chat endpoint (authenticated)."""
    try:
        username  = get_jwt_identity()
        data      = request.get_json()

        message   = data.get("message", "").strip()
        game_type = data.get("game_type", "general").strip()
        session_id = f"session_{username}"

        if not message:
            return jsonify({
                "success": False,
                "message": "Message cannot be empty."
            }), 400

        if len(message) > 1000:
            return jsonify({
                "success": False,
                "message": "Message too long. Max 1000 characters."
            }), 400

        # Get AI response
        result = get_coach_response(
            user_message=message,
            game_type=game_type,
            session_id=session_id,
            username=username
        )

        if result["success"]:
            # Update user stats
            if username in users_db:
                users_db[username]["stats"]["messages_sent"] += 1
                users_db[username]["stats"]["favorite_game"] = game_type

            # Save to chat log
            save_chat_log(username, game_type, message, result["response"])

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Coach request failed. Please try again.",
            "error": str(e)
        }), 500


@app.route("/api/coach/chat/guest", methods=["POST"])
def chat_guest():
    """Guest chat endpoint (no auth, limited to 5 messages)."""
    try:
        data       = request.get_json()
        message    = data.get("message", "").strip()
        game_type  = data.get("game_type", "general").strip()
        session_id = data.get("session_id", str(uuid.uuid4()))

        if not message:
            return jsonify({
                "success": False,
                "message": "Message cannot be empty."
            }), 400

        # Check guest message limit
        stats = get_session_stats(session_id)
        if stats["message_count"] >= 5:
            return jsonify({
                "success": False,
                "message": "Guest limit reached (5 messages). Please register for unlimited coaching!",
                "limit_reached": True
            }), 429

        result = get_coach_response(
            user_message=message,
            game_type=game_type,
            session_id=session_id,
            username="Player"
        )

        result["session_id"]      = session_id
        result["messages_left"]   = max(0, 5 - result.get("message_count", 0))

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Coach request failed.",
            "error": str(e)
        }), 500


@app.route("/api/coach/clear", methods=["POST"])
@jwt_required()
def clear_chat():
    """Clear conversation history."""
    username = get_jwt_identity()
    clear_session(f"session_{username}")
    return jsonify({
        "success": True,
        "message": "Conversation cleared. Starting fresh! 🔄"
    }), 200


@app.route("/api/coach/tips/<game_type>", methods=["GET"])
def get_tips(game_type):
    """Get quick tips for a game without AI call."""
    from coach_agent import generate_quick_tips
    tips = generate_quick_tips(game_type)
    return jsonify({
        "success": True,
        "game_type": game_type,
        "tips": tips
    }), 200


# ─────────────────────────────────────────────
#  Leaderboard Route
# ─────────────────────────────────────────────
@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    """Get top users by messages sent."""
    board = []
    for uname, udata in users_db.items():
        board.append({
            "username": uname,
            "messages_sent": udata["stats"]["messages_sent"],
            "sessions": udata["stats"]["sessions"],
            "favorite_game": udata["stats"]["favorite_game"],
            "rank_points": udata["stats"]["rank_points"]
        })

    board.sort(key=lambda x: x["messages_sent"], reverse=True)

    return jsonify({
        "success": True,
        "leaderboard": board[:10]
    }), 200


# ─────────────────────────────────────────────
#  Health Check
# ─────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "service": "AI Game Coach API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }), 200


# ─────────────────────────────────────────────
#  Run
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("🎮 AI Game Coach Backend Starting...")
    print("📡 API running at: http://localhost:5000")
    print("🔑 JWT Authentication: Enabled")
    print("🤖 Gemini AI: Connected")
    app.run(debug=True, host="0.0.0.0", port=5000)