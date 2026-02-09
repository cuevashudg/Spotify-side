"""
Personality narrator - Convert metrics into natural language insights.

Transforms cold analytics into warm (or savage) commentary.
"""

from typing import List, Dict
from analysis.mood import MoodAnalyzer
from analysis.habits import HabitsAnalyzer
from .tone import Tone, ToneType, get_commentary, get_tone_emoji, get_tone_description


class Narrator:
    """
    Natural language narrator for listening insights.
    
    Converts analytics into personality-driven commentary.
    """
    
    def __init__(self, mood_analyzer: MoodAnalyzer, habits_analyzer: HabitsAnalyzer, tone: ToneType = ToneType.FRIEND):
        """
        Initialize narrator.
        
        Args:
            mood_analyzer: MoodAnalyzer instance
            habits_analyzer: HabitsAnalyzer instance
            tone: Tone type (FRIEND, ANALYST, or ROAST)
        """
        self.mood = mood_analyzer
        self.habits = habits_analyzer
        self.tone = tone
    
    def set_tone(self, tone: ToneType):
        """Change narrator tone."""
        self.tone = tone
    
    def generate_full_report(self) -> str:
        """
        Generate complete listening report with personality.
        
        Returns:
            Formatted report string
        """
        lines = []
        
        # Header
        emoji = get_tone_emoji(self.tone)
        tone_desc = get_tone_description(self.tone)
        
        lines.append(f"\n{emoji} SPOTIMOOD REPORT ({tone_desc})")
        lines.append("=" * 60)
        
        # Listening habits
        lines.append(self._narrate_time_patterns())
        lines.append(self._narrate_artist_behavior())
        lines.append(self._narrate_repeat_behavior())
        lines.append(self._narrate_streaks())
        lines.append(self._narrate_sessions())
        
        # Mood analysis (if available)
        mood_section = self._narrate_mood()
        if mood_section:
            lines.append(mood_section)
        
        # Closing
        lines.append("\n" + "=" * 60)
        lines.append(get_commentary(Tone.CONGRATULATIONS, self.tone))
        lines.append("=" * 60 + "\n")
        
        return "\n".join(lines)
    
    def _narrate_time_patterns(self) -> str:
        """Generate commentary on listening time patterns."""
        lines = ["\n📅 WHEN YOU LISTEN"]
        
        hours = self.habits.get_listening_hours()
        
        if "error" not in hours:
            peak_hour = hours['most_active_hour']
            lines.append(get_commentary(Tone.PEAK_HOUR, self.tone, peak_hour))
            
            # Late night listener?
            if peak_hour >= 22 or peak_hour <= 2:
                lines.append(get_commentary(Tone.LATE_NIGHT_LISTENER, self.tone))
            # Early bird?
            elif 6 <= peak_hour <= 9:
                lines.append(get_commentary(Tone.EARLY_MORNING_LISTENER, self.tone))
        
        # Day of week
        days = self.habits.get_day_of_week_pattern()
        if "error" not in days:
            if days.get('is_weekend_listener'):
                lines.append(get_commentary(Tone.WEEKEND_WARRIOR, self.tone))
        
        return "\n".join(lines)
    
    def _narrate_artist_behavior(self) -> str:
        """Generate commentary on artist preferences."""
        lines = ["\n⭐ YOUR ARTISTS"]
        
        top_artists = self.habits.get_top_artists(limit=3)
        
        if top_artists:
            # Top artist
            top = top_artists[0]
            lines.append(get_commentary(
                Tone.TOP_ARTIST, self.tone,
                top['artist'], top['percentage']
            ))
            
            # Obsessed?
            if top['percentage'] > 15:
                lines.append(get_commentary(
                    Tone.ARTIST_OBSESSED, self.tone,
                    top['artist'], top['play_count']
                ))
        
        # Diversity
        repeats = self.habits.get_repeat_behavior()
        if repeats.get('diversity_score'):
            score = repeats['diversity_score']
            if score > 0.7:
                lines.append(get_commentary(Tone.DIVERSE_TASTE, self.tone, score))
        
        return "\n".join(lines)
    
    def _narrate_repeat_behavior(self) -> str:
        """Generate commentary on repeat patterns."""
        lines = ["\n🔁 REPEAT BEHAVIOR"]
        
        repeats = self.habits.get_repeat_behavior()
        
        repeat_pct = repeats.get('repeat_percentage', 0)
        
        if repeat_pct > 30:
            lines.append(get_commentary(Tone.HIGH_REPEATER, self.tone, repeat_pct))
        elif repeat_pct < 10:
            lines.append(get_commentary(Tone.LOW_REPEATER, self.tone))
        else:
            # Default commentary for moderate repeat rates
            lines.append(get_commentary(Tone.MODERATE_REPEATER, self.tone, repeat_pct))
        
        # Most repeated song
        most_repeated = repeats.get('most_repeated', [])
        if most_repeated:
            top_repeat = most_repeated[0]
            if top_repeat['play_count'] >= 5:
                lines.append(get_commentary(
                    Tone.SONG_ADDICTION, self.tone,
                    top_repeat['song'], top_repeat['play_count']
                ))
        
        return "\n".join(lines)
    
    def _narrate_streaks(self) -> str:
        """Generate commentary on listening streaks."""
        lines = ["\n🔥 LISTENING STREAK"]
        
        streaks = self.habits.get_listening_streaks()
        
        if "error" not in streaks:
            current = streaks.get('current_streak', 0)
            longest = streaks.get('longest_streak', 0)
            
            if current >= 3:
                lines.append(get_commentary(Tone.LONG_STREAK, self.tone, current))
            elif current == 0 and longest > 0:
                lines.append(get_commentary(Tone.BROKE_STREAK, self.tone))
            else:
                # Default commentary for active but short streaks
                lines.append(get_commentary(Tone.ACTIVE_LISTENER, self.tone, current))
        else:
            lines.append("Streak data unavailable")
        
        return "\n".join(lines)
    
    def _narrate_sessions(self) -> str:
        """Generate commentary on session patterns."""
        lines = ["\n🎧 SESSION PATTERNS"]
        
        sessions = self.habits.get_session_patterns()
        
        if "error" not in sessions:
            avg_tracks = sessions.get('avg_tracks_per_session', 0)
            longest = sessions.get('longest_session_tracks', 0)
            
            # Binge sessions?
            if longest > 50:
                lines.append(get_commentary(Tone.BINGE_SESSION, self.tone, longest))
            elif avg_tracks < 5:
                lines.append(get_commentary(Tone.SHORT_SESSION, self.tone))
            else:
                # Default commentary for normal session patterns
                lines.append(get_commentary(Tone.NORMAL_SESSION, self.tone, avg_tracks))
            
            total_hours = sessions.get('total_listening_time_hours', 0)
            if self.tone == ToneType.ANALYST:
                lines.append(f"Total listening time: {total_hours} hours")
            elif self.tone == ToneType.ROAST and total_hours > 50:
                lines.append(f"{total_hours} hours? That's like... a part-time job. Get a hobby.")
        else:
            lines.append("Session data unavailable")
        
        return "\n".join(lines)
    
    def _narrate_mood(self) -> str:
        """Generate commentary on mood patterns."""
        overall = self.mood.get_overall_mood()
        
        if "error" in overall:
            return ""  # No mood data available
        
        lines = ["\n😊 YOUR MOOD"]
        
        energy = overall.get('avg_energy', 0)
        valence = overall.get('avg_valence', 0)
        
        # Energy commentary
        if energy > 0.7:
            lines.append(get_commentary(Tone.ENERGY_HIGH, self.tone, energy))
        elif energy < 0.4:
            lines.append(get_commentary(Tone.ENERGY_LOW, self.tone, energy))
        
        # Valence commentary
        if valence > 0.7:
            lines.append(get_commentary(Tone.VALENCE_HAPPY, self.tone, valence))
        elif valence < 0.4:
            lines.append(get_commentary(Tone.VALENCE_SAD, self.tone, valence))
        
        # Mood label
        mood_label = overall.get('mood_label', '')
        emoji = overall.get('emoji', '')
        if mood_label:
            lines.append(f"{emoji} Overall vibe: {mood_label}")
        
        # Mood shifts
        shifts = self.mood.detect_mood_shifts()
        if shifts and len(shifts) > 0:
            recent_shift = shifts[-1]
            lines.append(get_commentary(
                Tone.MOOD_SHIFT_DETECTED, self.tone,
                recent_shift['before_mood'],
                recent_shift['after_mood']
            ))
        
        return "\n".join(lines)
    
    def generate_quick_summary(self) -> str:
        """
        Generate a short one-paragraph summary.
        
        Returns:
            Brief summary string
        """
        parts = []
        
        # Top artist
        top_artists = self.habits.get_top_artists(limit=1)
        if top_artists:
            top = top_artists[0]
            parts.append(f"Top artist: {top['artist']} ({top['percentage']}%)")
        
        # Peak time
        hours = self.habits.get_listening_hours()
        if "error" not in hours:
            parts.append(f"Peak hour: {hours['most_active_hour']}:00")
        
        # Streak
        streaks = self.habits.get_listening_streaks()
        if "error" not in streaks:
            current = streaks.get('current_streak', 0)
            if current > 0:
                parts.append(f"{current}-day streak")
        
        # Mood
        overall = self.mood.get_overall_mood()
        if "error" not in overall:
            parts.append(f"Mood: {overall['mood_label']}")
        
        return " | ".join(parts) if parts else "Keep listening to build your profile!"
