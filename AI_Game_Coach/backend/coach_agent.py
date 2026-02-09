def ai_game_coach(data):
    game = data.get("game")
    feedback = []

    matches = int(data.get("matches", 1))
    wins = int(data.get("wins", 0))
    win_rate = (wins / max(1, matches)) * 100

    # Common feedback for all games
    if win_rate < 40:
        feedback.append("Your win rate is low. Focus on improving basic strategies.")
    else:
        feedback.append("You have a decent win rate, but there is room for improvement.")

    # Game-specific strategy advice
    if game == "chess":
        if int(data.get("blunders", 0)) > 2:
            feedback.append("Avoid unnecessary piece sacrifices and check opponent threats.")
        feedback.append("Practice opening principles and endgame techniques regularly.")

    elif game == "carrom":
        if int(data.get("blunders", 0)) > 2:
            feedback.append("Reduce fouls by improving shot control.")
        feedback.append("Focus on accurate break shots and defensive positioning.")

    elif game == "ludo":
        feedback.append("Prioritize safe moves and avoid unnecessary risks.")
        feedback.append("Bring all tokens into play early for flexibility.")

    elif game == "uno":
        penalty = int(data.get("blunders", 0))
        wild = int(data.get("safe_moves", 0))

        if penalty > 3:
            feedback.append("You are drawing too many penalty cards. Play cautiously.")
        else:
            feedback.append("Good control over penalty cards.")

        feedback.append("Save wild cards for crucial moments near the end.")
        feedback.append("Try to track opponents’ colors and card counts.")

    elif game == "snake_ladder":
        snake_hits = int(data.get("endgame_losses", 0))
        if snake_hits > 3:
            feedback.append("Unlucky snake hits detected. Focus on probability-based pacing.")
        feedback.append("Maintain patience and avoid rushing moves.")

    # Final encouragement
    feedback.append("Consistent practice will significantly improve your gameplay.")

    return feedback
