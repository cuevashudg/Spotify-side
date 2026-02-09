"""
Personality engine for natural language insights.

Modules:
- narrator.py: Convert metrics into natural language commentary
- tone.py: Voice control (Friend, Analyst, Roast modes)
- roast_engine.py: Event-driven savage commentary (NEW!)

Usage:
    # Behavioral roast mode (works without Spotify features!)
    from personality import RoastEngine
    from analysis import BehaviorClassifier, load_tracks_from_json
    
    tracks = load_tracks_from_json("enriched_history.json")
    behavior = BehaviorClassifier(tracks)
    events = behavior.detect_behavioral_events()
    
    # Generate roasts from events
    roasts = RoastEngine.roast_multiple_events(events)
    for roast in roasts:
        print(f"🔥 {roast}")
"""

from .narrator import Narrator
from .tone import ToneType, Tone
from .roast_engine import RoastEngine

__all__ = ['Narrator', 'ToneType', 'Tone', 'RoastEngine']
