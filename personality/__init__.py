"""
Personality engine for natural language insights.

Modules:
- narrator.py: Convert metrics into natural language commentary
- tone.py: Voice control (Friend, Analyst, Roast modes)

Usage:
    from personality import Narrator, ToneType
    from analysis.mood import MoodAnalyzer, load_tracks_from_json
    from analysis.habits import HabitsAnalyzer
    
    tracks = load_tracks_from_json("enriched_history.json")
    mood = MoodAnalyzer(tracks)
    habits = HabitsAnalyzer(tracks)
    
    # Generate report with roast mode 😈
    narrator = Narrator(mood, habits, tone=ToneType.ROAST)
    print(narrator.generate_full_report())
"""

from .narrator import Narrator
from .tone import ToneType, Tone

__all__ = ['Narrator', 'ToneType', 'Tone']
