"""
Tone control for the personality narrator.

Defines different voices/personalities for insights:
- Friend Mode: Supportive and encouraging
- Analyst Mode: Objective and data-focused
- Roast Mode: Brutally honest and sarcastic 😈
"""

from typing import Dict, List
from enum import Enum


class ToneType(Enum):
    """Available narrator tones."""
    FRIEND = "friend"
    ANALYST = "analyst"
    ROAST = "roast"


class Tone:
    """
    Tone templates for generating commentary.
    
    Each tone has different phrasings for the same insight.
    """
    
    # === LISTENING TIME PATTERNS ===
    
    PEAK_HOUR = {
        ToneType.FRIEND: lambda h: f"You're most active around {h}:00! That's your jam time. 🎵",
        ToneType.ANALYST: lambda h: f"Peak listening activity occurs at {h}:00 hours.",
        ToneType.ROAST: lambda h: f"Let me guess, {h}:00 is when you avoid actual responsibilities? Classic."
    }
    
    LATE_NIGHT_LISTENER = {
        ToneType.FRIEND: lambda: "You're a night owl! Late night vibes hit different. 🌙",
        ToneType.ANALYST: lambda: "Listening activity concentrated in late evening hours (22:00-02:00).",
        ToneType.ROAST: lambda: "Up at 2am listening to sad songs? We've all been there... but not THIS much."
    }
    
    EARLY_MORNING_LISTENER = {
        ToneType.FRIEND: lambda: "Early bird gets the bops! Morning music sets a great tone for your day. ☀️",
        ToneType.ANALYST: lambda: "Primary listening window: 06:00-09:00 hours.",
        ToneType.ROAST: lambda: "Who voluntarily wakes up early to listen to music? Are you okay?"
    }
    
    WEEKEND_WARRIOR = {
        ToneType.FRIEND: lambda: "Weekend listener! You know how to kick back and enjoy. 🎉",
        ToneType.ANALYST: lambda: "Listening behavior peaks during weekend periods (Saturday-Sunday).",
        ToneType.ROAST: lambda: "Only listen on weekends? What, weekdays too busy being productive? Doubt it."
    }
    
    # === ARTIST BEHAVIOR ===
    
    TOP_ARTIST = {
        ToneType.FRIEND: lambda artist, pct: f"{artist} is your #1! {pct}% of your plays. Great taste! ⭐",
        ToneType.ANALYST: lambda artist, pct: f"Primary artist: {artist} ({pct}% of total plays).",
        ToneType.ROAST: lambda artist, pct: f"{artist} is {pct}% of your listening. Bro, there are OTHER artists. Explore."
    }
    
    ARTIST_OBSESSED = {
        ToneType.FRIEND: lambda artist, cnt: f"You LOVE {artist}! {cnt} plays shows true dedication. 💕",
        ToneType.ANALYST: lambda artist, cnt: f"High concentration: {artist} accounts for {cnt} plays.",
        ToneType.ROAST: lambda artist, cnt: f"{cnt} plays of {artist}?? They're not gonna date you, bestie."
    }
    
    DIVERSE_TASTE = {
        ToneType.FRIEND: lambda score: f"Love your variety! Diversity score: {score}. You're musically adventurous! 🌈",
        ToneType.ANALYST: lambda score: f"Listening diversity index: {score} (high variability).",
        ToneType.ROAST: lambda score: f"Diversity score {score}. Wow, you have the attention span of a goldfish."
    }
    
    # === REPEAT BEHAVIOR ===
    
    HIGH_REPEATER = {
        ToneType.FRIEND: lambda pct: f"You replay {pct}% of tracks. Nothing wrong with knowing what you like! 🔁",
        ToneType.ANALYST: lambda pct: f"Repeat rate: {pct}% (above average).",
        ToneType.ROAST: lambda pct: f"{pct}% repeats? Bro discovered 5 songs in 2010 and never looked back."
    }
    
    SONG_ADDICTION = {
        ToneType.FRIEND: lambda song, cnt: f"{song} is on repeat! {cnt} plays. It must be special. ❤️",
        ToneType.ANALYST: lambda song, cnt: f"Most repeated track: {song} ({cnt} plays).",
        ToneType.ROAST: lambda song, cnt: f"Played {song} {cnt} times. Are you okay? Do you need someone to talk to?"
    }
    
    LOW_REPEATER = {
        ToneType.FRIEND: lambda: "You're always discovering new music! Love the exploration. 🚀",
        ToneType.ANALYST: lambda: "Low repeat rate detected. High novelty-seeking behavior.",
        ToneType.ROAST: lambda: "Never replay anything? Commitment issues much?"
    }
    
    # === LISTENING STREAKS ===
    
    LONG_STREAK = {
        ToneType.FRIEND: lambda days: f"{days}-day streak! You're dedicated! Keep it going! 🔥",
        ToneType.ANALYST: lambda days: f"Current listening streak: {days} consecutive days.",
        ToneType.ROAST: lambda days: f"{days}-day streak. Congrats on being chronically online, I guess."
    }
    
    BROKE_STREAK = {
        ToneType.FRIEND: lambda: "The streak broke, but you can start a new one! No pressure. 💪",
        ToneType.ANALYST: lambda: "Streak discontinued. Previous longest: recorded.",
        ToneType.ROAST: lambda: "Broke your streak. Can't commit to anything, can you?"
    }
    
    # === MOOD PATTERNS (when features work) ===
    
    ENERGY_HIGH = {
        ToneType.FRIEND: lambda nrg: f"High energy vibes! Average: {nrg}. You like it intense! ⚡",
        ToneType.ANALYST: lambda nrg: f"Average energy level: {nrg} (high-intensity preference).",
        ToneType.ROAST: lambda nrg: f"Energy level {nrg}? Chill out. Not everything needs to be a workout."
    }
    
    ENERGY_LOW = {
        ToneType.FRIEND: lambda nrg: f"Chill vibes at {nrg} energy. You appreciate the calm. 😌",
        ToneType.ANALYST: lambda nrg: f"Average energy level: {nrg} (low-intensity preference).",
        ToneType.ROAST: lambda nrg: f"Energy {nrg}? You good? Should I be worried?"
    }
    
    VALENCE_SAD = {
        ToneType.FRIEND: lambda val: f"Mellow mood at {val} valence. Music for reflection. 🌧️",
        ToneType.ANALYST: lambda val: f"Average valence: {val} (melancholic tendency).",
        ToneType.ROAST: lambda val: f"Valence {val}? Who hurt you? Actually, don't answer that."
    }
    
    VALENCE_HAPPY = {
        ToneType.FRIEND: lambda val: f"Happy vibes! {val} valence. Love the positive energy! 😄",
        ToneType.ANALYST: lambda val: f"Average valence: {val} (positive affect).",
        ToneType.ROAST: lambda val: f"Valence {val}. Okay, we get it, you're happy. Calm down."
    }
    
    MOOD_SHIFT_DETECTED = {
        ToneType.FRIEND: lambda before, after: f"Mood shifted from {before} to {after}. Music adapts with you! 🌈",
        ToneType.ANALYST: lambda before, after: f"Significant mood transition: {before} → {after}.",
        ToneType.ROAST: lambda before, after: f"Went from {before} to {after}? That's called emotional whiplash, bro."
    }
    
    # === SESSION BEHAVIOR ===
    
    BINGE_SESSION = {
        ToneType.FRIEND: lambda tracks: f"Marathon session! {tracks} tracks in one go. Dedication! 🎧",
        ToneType.ANALYST: lambda tracks: f"Extended session detected: {tracks} consecutive tracks.",
        ToneType.ROAST: lambda tracks: f"{tracks} tracks straight? Go outside. Touch grass. Please."
    }
    
    SHORT_SESSION = {
        ToneType.FRIEND: lambda: "Quick listening bursts! You make the most of your time. ⏰",
        ToneType.ANALYST: lambda: "Session pattern: Short, frequent intervals.",
        ToneType.ROAST: lambda: "Can't even finish a full song? The TikTok generation strikes again."
    }
    
    # === GENERAL COMMENTARY ===
    
    NO_DATA = {
        ToneType.FRIEND: lambda: "Keep listening! I need more data to give you insights. 🎵",
        ToneType.ANALYST: lambda: "Insufficient data for comprehensive analysis.",
        ToneType.ROAST: lambda: "Not enough data. Go actually listen to music instead of reading this."
    }
    
    CONGRATULATIONS = {
        ToneType.FRIEND: lambda: "You have great taste! Keep vibing! ✨",
        ToneType.ANALYST: lambda: "Analysis complete. Patterns identified.",
        ToneType.ROAST: lambda: "Well, that was... something. Got any worse taste you wanna share?"
    }


def get_commentary(template: Dict, tone: ToneType, *args) -> str:
    """
    Get commentary for a specific template and tone.
    
    Args:
        template: Template dictionary (e.g., Tone.PEAK_HOUR)
        tone: ToneType to use
        *args: Arguments to pass to the template function
        
    Returns:
        Formatted commentary string
    """
    if tone in template:
        return template[tone](*args)
    return template[ToneType.ANALYST](*args)  # Fallback to analyst


def get_tone_emoji(tone: ToneType) -> str:
    """Get emoji for tone type."""
    return {
        ToneType.FRIEND: "💙",
        ToneType.ANALYST: "📊",
        ToneType.ROAST: "🔥"
    }.get(tone, "🎵")


def get_tone_description(tone: ToneType) -> str:
    """Get description of tone."""
    return {
        ToneType.FRIEND: "Supportive and encouraging",
        ToneType.ANALYST: "Objective and data-focused",
        ToneType.ROAST: "Brutally honest and sarcastic"
    }.get(tone, "Unknown")
