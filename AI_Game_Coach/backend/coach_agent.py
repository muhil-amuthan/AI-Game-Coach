import os
from dotenv import load_dotenv

load_dotenv()

# Try to import the Gemini client; allow fallback when unavailable
try:
    import google.generativeai as genai
    _HAS_GENAI = True
except Exception:
    genai = None
    _HAS_GENAI = False

# ─────────────────────────────────────────────
#  Configure Gemini (optional)
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if _HAS_GENAI and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        _USE_GENAI = True
    except Exception:
        _USE_GENAI = False
else:
    _USE_GENAI = False

# ─────────────────────────────────────────────
#  Game-specific system prompts
# ─────────────────────────────────────────────
GAME_PROMPTS = {
    "chess": """You are an elite Chess AI coach with grandmaster-level knowledge.
        You specialize in:
        - Opening theory (ECO codes, variations, transpositions)
        - Tactical patterns (forks, pins, skewers, discovered attacks, zwischenzug)
        - Strategic concepts (pawn structure, piece activity, king safety)
        - Endgame technique (Lucena, Philidor, opposition, triangulation)
        - Game analysis with move-by-move explanations
        Always suggest concrete moves in algebraic notation when relevant.
        Be encouraging but precise and technically accurate.""",

    "fps": """You are a professional FPS gaming coach with expertise in
        CS2, Valorant, Apex Legends, Overwatch 2, and Warzone.
        You specialize in:
        - Aim mechanics (crosshair placement, flicking, tracking, spray control)
        - Game sense (rotations, economy, information gathering)
        - Map knowledge (angles, positions, common spots)
        - Team communication and coordination
        - Mental performance and tilt management
        Give practical, actionable drills and tips. Reference specific maps/agents when helpful.""",

    "moba": """You are a Diamond+ MOBA coach specializing in
        League of Legends and Dota 2.
        You specialize in:
        - Champion/hero mechanics and combos
        - Macro play (objectives, rotations, wave management)
        - Draft and counter-picking strategies
        - Role-specific responsibilities (carry, support, jungler)
        - Vision control and map awareness
        Always consider the current meta and patch context.""",

    "rpg": """You are an expert RPG and MMO guide with deep knowledge of
        Elden Ring, World of Warcraft, Genshin Impact, and similar titles.
        You specialize in:
        - Character builds and stat optimization
        - Boss strategies and mechanics
        - Efficient progression paths and leveling guides
        - Lore and quest guidance
        - Team composition for raids and co-op
        Tailor advice to the player's current progression stage.""",

    "racing": """You are a professional sim racing coach with expertise in
        F1 series, Forza Motorsport, Gran Turismo, and iRacing.
        You specialize in:
        - Racing lines (braking points, apex selection, exit speed)
        - Car setup and tuning (suspension, aero, differential)
        - Track-specific strategies and sector improvements
        - Tire management and pit strategy
        - Consistency building techniques
        Provide technical setup advice when asked.""",

    "strategy": """You are a grandmaster-level RTS coach specializing in
        StarCraft II, Age of Empires IV, and Civilization series.
        You specialize in:
        - Build orders and opening strategies
        - Macro fundamentals (economy, production, expansion)
        - Micro techniques (unit control, formation, focus fire)
        - Scouting and intelligence gathering
        - Late-game decision making and tech trees
        Always explain the 'why' behind strategic decisions.""",

    "fighting": """You are an EVO-level fighting game coach with expertise in
        Street Fighter 6, Tekken 8, Mortal Kombat, and Guilty Gear.
        You specialize in:
        - Combo routes and execution techniques
        - Frame data analysis (advantage/disadvantage states)
        - Matchup knowledge and counter-strategies
        - Neutral game and footsies
        - Mental stack management and defense
        Reference specific character moves and frame numbers when relevant.""",

    "puzzle": """You are a puzzle and brain game expert specializing in
        Sudoku, Portal series, The Witness, and logic puzzles.
        You specialize in:
        - Logical deduction techniques and solving strategies
        - Pattern recognition and spatial reasoning
        - Hint systems that guide without spoiling
        - Progressive difficulty approaches
        - Mental frameworks for different puzzle types
        Guide the player to discover solutions rather than just giving answers.""",

    "general": """You are an elite multi-game AI coach with expertise
        across all gaming genres.
        You can help with:
        - Game-specific strategy and mechanics
        - Skill improvement and practice routines
        - Mental performance and focus techniques
        - Career development in competitive gaming
        - Hardware and settings optimization
        Always ask clarifying questions to provide the most relevant advice.
        Be encouraging, specific, and practical in all responses."""
}

# ─────────────────────────────────────────────
#  Conversation history storage (in-memory)
# ─────────────────────────────────────────────
# In production, use Redis or a database
conversation_histories = {}


def get_coach_response(
    user_message: str,
    game_type: str = "general",
    session_id: str = "default",
    username: str = "Player"
) -> dict:
    """
    Get AI coaching response using Gemini.

    Args:
        user_message: The player's question or message
        game_type: The game category (chess, fps, moba, etc.)
        session_id: Unique session identifier for conversation history
        username: Player's name for personalized responses

    Returns:
        dict with 'response', 'game_type', 'session_id', 'tips'
    """

    try:
        # ── Select system prompt ──────────────────────────────────────
        game_key = game_type.lower().strip()
        system_prompt = GAME_PROMPTS.get(game_key, GAME_PROMPTS["general"])

        # Add username personalization
        system_prompt += f"\n\nYou are coaching a player named {username}. " \
                         f"Address them by name occasionally to make it personal. " \
                         f"Keep responses concise but comprehensive (150-300 words max). " \
                         f"Use emojis sparingly for readability. " \
                         f"Format with bullet points when listing multiple tips."

        # If Gemini is available and configured, use it. Otherwise return
        # a lightweight fallback response so the backend remains usable
        if _USE_GENAI and genai is not None:
            # ── Initialize model ──────────────────────────────────
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_prompt
            )

            # ── Manage conversation history ───────────────────────
            if session_id not in conversation_histories:
                conversation_histories[session_id] = []

            history = conversation_histories[session_id]

            # Start or continue chat
            chat = model.start_chat(history=history)

            # Send message and get response
            response = chat.send_message(user_message)
            response_text = response.text

            # Update history (keep last 20 exchanges to manage context)
            conversation_histories[session_id] = chat.history[-20:]

        else:
            # Simple fallback: echo + short advice using quick tips
            quick_tips = generate_quick_tips(game_key)
            response_text = (
                f"Hi {username}, here's a quick tip for {game_key}: {quick_tips[0]}\n\n" 
                f"You said: {user_message[:400]}"
            )

            # Add to conversation history as a minimal record
            if session_id not in conversation_histories:
                conversation_histories[session_id] = []
            conversation_histories[session_id].append({"user": user_message, "bot": response_text})

        # ── Generate quick tips sidebar ───────────────────────────────
        quick_tips = generate_quick_tips(game_key)

        # Compute message count (handles both Gemini list-of-Content and
        # fallback list-of-dict storage shapes).
        history = conversation_histories.get(session_id, [])
        if history and isinstance(history[0], dict):
            msg_count = len(history)
        else:
            msg_count = len(history) // 2

        return {
            "success": True,
            "response": response_text,
            "game_type": game_key,
            "session_id": session_id,
            "quick_tips": quick_tips,
            "message_count": msg_count
        }

    except Exception as e:
        error_message = str(e)

        # Handle specific API errors gracefully
        if "API_KEY_INVALID" in error_message:
            user_error = "Invalid API key. Please check your configuration."
        elif "QUOTA_EXCEEDED" in error_message:
            user_error = "API quota exceeded. Please try again later."
        elif "SAFETY" in error_message.upper():
            user_error = "Message flagged by safety filters. Please rephrase."
        else:
            user_error = "Coach is temporarily unavailable. Please try again."

        return {
            "success": False,
            "response": user_error,
            "error": error_message,
            "game_type": game_type,
            "session_id": session_id
        }


def generate_quick_tips(game_type: str) -> list:
    """Return static quick tips for the selected game."""

    tips_db = {
        "chess": [
            "♟️ Control the center with pawns on e4/d4",
            "🏰 Castle early to protect your king",
            "⚡ Develop knights before bishops",
            "👁️ Always check your opponent's threats first",
            "🔄 Rooks belong on open files"
        ],
        "fps": [
            "🎯 Pre-aim at head height always",
            "👂 Use headphones - sound = information",
            "🚶 Walk when near enemies to avoid footsteps",
            "💰 Learn economy management in CS2/Valorant",
            "🗺️ Study 2-3 maps deeply before branching out"
        ],
        "moba": [
            "🗺️ Check minimap every 5 seconds",
            "🏰 Always take objectives after winning fights",
            "📊 CS (creep score) matters more than kills",
            "🌊 Manage wave state to control pressure",
            "👁️ Buy vision control items every back"
        ],
        "rpg": [
            "💾 Save frequently in multiple slots",
            "⚖️ Balance offense and defense in builds",
            "🗺️ Explore thoroughly before progressing",
            "📖 Read item descriptions carefully",
            "🔄 Try different builds to find your style"
        ],
        "racing": [
            "🏁 Brake in a straight line, accelerate out",
            "👀 Look ahead to where you want to go",
            "🔄 Smooth inputs beat aggressive inputs",
            "⛽ Manage tire temperature, not just grip",
            "📏 Find the geometric apex, not visual apex"
        ],
        "strategy": [
            "💰 Never let resources sit uncollected",
            "🔍 Scout every 2-3 minutes minimum",
            "⚡ Attack while expanding when possible",
            "🏗️ Queue units continuously from all buildings",
            "🎯 Always have a clear win condition in mind"
        ],
        "fighting": [
            "🛡️ Learn to block before learning combos",
            "📊 Understand +/- frames for safe play",
            "🎯 Punish whiffed moves consistently",
            "🔄 Practice BnB combos until muscle memory",
            "🧠 Study your opponent's habits mid-match"
        ],
        "puzzle": [
            "🔍 Observe everything before touching anything",
            "📝 Note what changes and what doesn't",
            "🔄 If stuck, try the opposite approach",
            "🧩 Break complex puzzles into smaller parts",
            "💡 Environmental storytelling holds clues"
        ],
        "general": [
            "🎮 Consistent practice beats long sessions",
            "📊 Review your losses more than your wins",
            "🧠 Focus on one skill at a time",
            "💤 Sleep is crucial for skill consolidation",
            "🤝 Play with players slightly better than you"
        ]
    }

    return tips_db.get(game_type, tips_db["general"])


def clear_session(session_id: str) -> bool:
    """Clear conversation history for a session."""
    if session_id in conversation_histories:
        del conversation_histories[session_id]
        return True
    return False


def get_session_stats(session_id: str) -> dict:
    """Get statistics for a coaching session.

    The conversation history uses two different storage shapes:
      * Real Gemini path: list of `protos.Content` objects (one per turn, both
        user and model, so 2 per exchange).
      * Fallback path: list of `{"user": ..., "bot": ...}` dicts (1 per turn).
    We normalise both to the number of user messages.
    """
    if session_id not in conversation_histories:
        return {"message_count": 0, "session_active": False}

    history = conversation_histories[session_id]
    if not history:
        return {"message_count": 0, "session_active": False, "history_length": 0}

    if isinstance(history[0], dict):
        # Fallback format: one dict per turn
        message_count = len(history)
    else:
        # Gemini format: alternating user/model → 2 entries per turn
        message_count = len(history) // 2

    return {
        "message_count": message_count,
        "session_active": True,
        "history_length": len(history)
    }