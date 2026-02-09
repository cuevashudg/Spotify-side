"""
Analysis modules for behavioral pattern detection.

Modules:
- behavior.py: Behavioral classification without API features (NEW!)
- mood.py: Energy/valence trends (requires Spotify features)
- habits.py: Time patterns, top artists, streaks, session analytics

Usage:
    from analysis import BehaviorClassifier, HabitsAnalyzer, load_tracks_from_json
    
    tracks = load_tracks_from_json("enriched_history.json")
    behavior = BehaviorClassifier(tracks)  # Works without Spotify features!
    habits = HabitsAnalyzer(tracks)
    
    # Classify behavior
    state = behavior.classify_overall()
    events = behavior.detect_behavioral_events()
"""

from .mood import MoodAnalyzer, load_tracks_from_json
from .habits import HabitsAnalyzer
from .behavior_signals import (
    BehaviorClassifier,
    BehaviorState,
    BehaviorBaseline,
    BehaviorSignal,
    ListeningSession,
    LateNightSignal,
    ReplaySignal,
    SessionLengthSignal,
    ContextSwitchSignal,
)

__all__ = [
    # Behavioral signals (signal-based architecture)
    'BehaviorClassifier',
    'BehaviorState',
    'BehaviorBaseline',
    'BehaviorSignal',
    'ListeningSession',
    'LateNightSignal',
    'ReplaySignal',
    'SessionLengthSignal',
    'ContextSwitchSignal',
    # Other analysis
    'MoodAnalyzer',
    'HabitsAnalyzer',
    'load_tracks_from_json'
]
