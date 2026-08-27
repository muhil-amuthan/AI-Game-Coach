from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from flask_bcrypt import Bcrypt
from coach_agent import get_coach_response, clear_session, get_session_stats
import database as db
from dotenv import load_dotenv
import os
import uuid
import re
from datetime import timedelta, datetime

# Load environment variables
load_dotenv()

# Initialize Database Schema
db.init_db()

# ─────────────────────────────────────────────
#  App Configuration
# ─────────────────────────────────────────────
app = Flask(__name__)

# Secret keys from environment with secure production fallbacks
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    # In development, fall back; in production, advise setting SECRET_KEY
    secret_key = "ai-game-coach-dev-secret-key-change-me-in-production-2026"
app.secret_key = secret_key

jwt_secret_key = os.getenv("JWT_SECRET_KEY")
if not jwt_secret_key:
    jwt_secret_key = "jwt-dev-secret-key-change-me-in-production-2026-32bytes"
app.config["JWT_SECRET_KEY"] = jwt_secret_key
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

# ─────────────────────────────────────────────
#  CORS Configuration
# ─────────────────────────────────────────────
# Configurable CORS origins for production (Vercel) & local dev
cors_env = os.getenv("CORS_ORIGINS") or os.getenv("FRONTEND_URL")
if cors_env and cors_env.strip() != "*":
    allowed_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
    # Also support regex matching for Vercel preview URLs
    allowed_origins.append(re.compile(r"^https://.*\.vercel\.app$"))
else:
    # Allow all origins by default (safe for API with Bearer token authentication)
    allowed_origins = "*"

CORS(
    app,
    resources={r"/api/*": {"origins": allowed_origins}},
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    supports_credentials=True
)

jwt = JWTManager(app)
bcrypt = Bcrypt(app)


# ─────────────────────────────────────────────
#  Auth Routes
# ─────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def register():
    """Register a new user with persistent database storage."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid JSON body."}), 400

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

        if db.get_user(username):
            return jsonify({
                "success": False,
                "message": "Username already taken. Please choose another."
            }), 409

        if db.get_user_by_email(email):
            return jsonify({
                "success": False,
                "message": "Email already registered."
            }), 409

        # ── Create user ───────────────────────────────────────────────
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = db.create_user(username=username, email=email, password_hash=password_hash)

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
        if not data:
            return jsonify({"success": False, "message": "Invalid JSON body."}), 400

        username = data.get("username", "").strip().lower()
        password = data.get("password", "").strip()

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username and password are required."
            }), 400

        user = db.get_user(username)

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
        db.increment_user_session(username)
        # Fetch updated stats
        updated_user = db.get_user(username)

        access_token = create_access_token(identity=username)

        return jsonify({
            "success": True,
            "message": f"Welcome back, {username}! 🎮",
            "access_token": access_token,
            "username": username,
            "email": user["email"],
            "stats": updated_user["stats"] if updated_user else user["stats"]
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
    """Logout user (clear their active session history)."""
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
    user = db.get_user(username)

    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    recent_sessions = db.get_recent_sessions(username, limit=5)
    all_history = db.get_user_history(username)

    return jsonify({
        "success": True,
        "username": username,
        "email": user["email"],
        "created_at": user["created_at"],
        "stats": user["stats"],
        "recent_sessions": recent_sessions,
        "total_chats": len(all_history)
    }), 200


@app.route("/api/user/history", methods=["GET"])
@jwt_required()
def get_history():
    """Get full chat history for user."""
    username = get_jwt_identity()
    game_filter = request.args.get("game", None)

    history = db.get_user_history(username, game_filter=game_filter)

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
        if not data:
            return jsonify({"success": False, "message": "Invalid JSON body."}), 400

        message   = data.get("message", "").strip()
        game_type = data.get("game_type", "general").strip().lower()
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
            # Update user stats in persistent database
            db.update_user_stats(username, game_type)
            # Save to persistent chat log
            db.save_chat_log(username, game_type, message, result["response"])

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
        if not data:
            return jsonify({"success": False, "message": "Invalid JSON body."}), 400

        message    = data.get("message", "").strip()
        game_type  = data.get("game_type", "general").strip().lower()
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
    tips = generate_quick_tips(game_type.lower())
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
    """Get top users by messages sent from persistent database."""
    board = db.get_leaderboard(limit=10)
    return jsonify({
        "success": True,
        "leaderboard": board
    }), 200


# ─────────────────────────────────────────────
#  Health Check Route
# ─────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    """System health check endpoint."""
    db_ok = db.check_db_health()
    status_code = 200 if db_ok else 503
    return jsonify({
        "status": "online" if db_ok else "degraded",
        "service": "AI Game Coach API",
        "version": "2.0.0",
        "database": "connected" if db_ok else "unavailable",
        "timestamp": datetime.now().isoformat()
    }), status_code


# ─────────────────────────────────────────────
#  Entry Point for Local Development
# ─────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV", "production").lower() == "development"
    print("🎮 AI Game Coach Backend Starting...")
    print(f"📡 API running at: http://0.0.0.0:{port}")
    print("🔑 JWT Authentication: Enabled")
    print("💾 Database: Persistent SQLite (initialized)")
    app.run(debug=debug_mode, host="0.0.0.0", port=port)