from flask import Flask, request, jsonify
from flask_cors import CORS
from coach_agent import ai_game_coach
import os

app = Flask(__name__)
CORS(app)

# ---------- HOME ROUTE ----------
@app.route("/")
def home():
    return "AI Game Coach Backend is Running 🚀"

# ---------- ANALYZE ROUTE ----------
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json

    game = data.get("game", "")
    matches = int(data.get("matches", 0))
    wins = int(data.get("wins", 0))

    # Common stats
    blunders = int(data.get("blunders", 0))
    endgame_losses = int(data.get("endgame_losses", 0))
    safe_moves = int(data.get("safe_moves", 0))
    risky_moves = int(data.get("risky_moves", 0))

    # Game-specific stats
    fouls = blunders
    break_success = safe_moves
    penalty_cards = risky_moves
    wild_card_usage = safe_moves
    snake_hits = endgame_losses

    game_data = {
        "matches": matches,
        "wins": wins,
        "blunders": blunders,
        "endgame_losses": endgame_losses,
        "safe_moves": safe_moves,
        "risky_moves": risky_moves,
        "fouls": fouls,
        "break_success": break_success,
        "penalty_cards": penalty_cards,
        "wild_card_usage": wild_card_usage,
        "snake_hits": snake_hits
    }

    feedback = ai_game_coach(game, game_data)

    return jsonify({
        "game": game,
        "ai_coach_feedback": feedback
    })

# ---------- MAIN (IMPORTANT FOR DEPLOYMENT) ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
