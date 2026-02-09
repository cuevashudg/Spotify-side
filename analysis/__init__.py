"""
Analysis modules for behavioral pattern detection.

Modules:
- mood.py: Energy/valence trends, mood shifts, emotional extremes
- habits.py: Time patterns, top artists, streaks, session analytics

Usage:
    from analysis.mood import MoodAnalyzer, load_tracks_from_json
    from analysis.habits import HabitsAnalyzer
    
    tracks = load_tracks_from_json("enriched_history.json")
    mood = MoodAnalyzer(tracks)
    habits = HabitsAnalyzer(tracks)
"""

from .mood import MoodAnalyzer, load_tracks_from_json
from .habits import HabitsAnalyzer

__all__ = ['MoodAnalyzer', 'HabitsAnalyzer', 'load_tracks_from_json']
