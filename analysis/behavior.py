"""
Behavioral classification - Infer emotional states from listening patterns.

Instead of relying on Spotify's valence/mood metadata, we classify behavior
based on ACTIONS, not audio features. This is:
- More reliable (no API dependency)
- More personal (uses YOUR patterns)
- More interesting (human behavior > metadata)

Behavioral States:
- ruminating: Late-night replay loops
- searching: High skip rate, no settling
- focused: Long continuous sessions, low skips
- comfort_seeking: Repeat on, shuffle off
- energized: High tempo, high activity
- zoning_out: Long passive sessions
"""

from datetime import datetime, time
from typing import List, Dict, Optional
from collections import Counter

from core.models import Track


class BehaviorState:
    """
    Represents an inferred behavioral/emotional state.
    
    Based on listening patterns, not audio features.
    """
    
    def __init__(
        self,
        state: str,
        confidence: float,
        evidence: List[str],
        intensity: float = 0.5
    ):
        """
        Initialize behavioral state.
        
        Args:
            state: Behavior label (e.g., "ruminating", "focused")
            confidence: 0.0-1.0 confidence in classification
            evidence: List of behavioral signals that led to this classification
            intensity: 0.0-1.0 intensity of the behavior
        """
        self.state = state
        self.confidence = confidence
        self.evidence = evidence
        self.intensity = intensity
    
    def __repr__(self):
        return f"BehaviorState(state='{self.state}', confidence={self.confidence:.2f})"


class BehaviorClassifier:
    """
    Classify listening behavior without relying on Spotify features.
    
    Uses temporal patterns, replay behavior, skip rates, and context
    to infer emotional/behavioral states.
    """
    
    def __init__(self, tracks: List[Track]):
        """
        Initialize classifier with track history.
        
        Args:
            tracks: List of Track objects
        """
        self.tracks = sorted(tracks, key=lambda t: t.timestamp)
        self._track_counts = Counter(t.track_id for t in tracks)
    
    def classify_session(self, session_tracks: List[Track]) -> BehaviorState:
        """
        Classify behavior for a single listening session.
        
        Args:
            session_tracks: Tracks from one session
            
        Returns:
            BehaviorState classification
        """
        if not session_tracks:
            return BehaviorState("unknown", 0.0, [])
        
        # Gather behavioral signals
        evidence = []
        confidence_scores = []
        
        # Time of day
        avg_hour = sum(t.timestamp.hour for t in session_tracks) / len(session_tracks)
        is_late_night = 22 <= avg_hour or avg_hour <= 3
        
        # Replay behavior
        replay_count = sum(1 for t in session_tracks if self._track_counts[t.track_id] > 1)
        replay_rate = replay_count / len(session_tracks) if session_tracks else 0
        
        # Context switches
        contexts = [t.context_uri for t in session_tracks if t.context_uri]
        context_switches = len(set(contexts)) if contexts else 0
        
        # Shuffle/repeat state (if available)
        shuffle_states = [t.shuffle_state for t in session_tracks if t.shuffle_state is not None]
        repeat_states = [t.repeat_state for t in session_tracks if t.repeat_state]
        
        shuffle_off = shuffle_states and not any(shuffle_states)
        repeat_on = repeat_states and any(s != "off" for s in repeat_states)
        
        # Session length
        session_duration = (session_tracks[-1].timestamp - session_tracks[0].timestamp).total_seconds() / 60
        
        # === CLASSIFICATION LOGIC ===
        
        # 1. RUMINATING: Late night + high replay + shuffle off
        if is_late_night and replay_rate > 0.3 and shuffle_off:
            evidence.append(f"Late night listening ({int(avg_hour)}:00)")
            evidence.append(f"High replay rate ({replay_rate:.0%})")
            evidence.append("Shuffle disabled")
            return BehaviorState(
                "ruminating",
                confidence=0.85,
                evidence=evidence,
                intensity=min(replay_rate * 1.5, 1.0)
            )
        
        # 2. COMFORT SEEKING: Repeat on + shuffle off + moderate replay
        if repeat_on and shuffle_off and replay_rate > 0.2:
            evidence.append("Repeat enabled")
            evidence.append("Shuffle disabled")
            evidence.append(f"{replay_rate:.0%} replay rate")
            return BehaviorState(
                "comfort_seeking",
                confidence=0.80,
                evidence=evidence,
                intensity=replay_rate
            )
        
        # 3. SEARCHING: High context switches + short tracks
        if context_switches > 3 and len(session_tracks) > 10:
            evidence.append(f"{context_switches} context switches")
            evidence.append(f"{len(session_tracks)} tracks in session")
            return BehaviorState(
                "searching",
                confidence=0.75,
                evidence=evidence,
                intensity=min(context_switches / 5, 1.0)
            )
        
        # 4. FOCUSED: Long session + low context switches + low replay
        if session_duration > 60 and context_switches <= 1 and replay_rate < 0.2:
            evidence.append(f"{session_duration:.0f}-minute session")
            evidence.append("Minimal context switching")
            evidence.append("Low replay rate")
            return BehaviorState(
                "focused",
                confidence=0.80,
                evidence=evidence,
                intensity=min(session_duration / 120, 1.0)
            )
        
        # 5. ZONING OUT: Long passive session
        if session_duration > 90:
            evidence.append(f"{session_duration:.0f}-minute session")
            evidence.append("Extended passive listening")
            return BehaviorState(
                "zoning_out",
                confidence=0.70,
                evidence=evidence,
                intensity=min(session_duration / 180, 1.0)
            )
        
        # Default: casual
        evidence.append("Standard listening pattern")
        return BehaviorState(
            "casual",
            confidence=0.60,
            evidence=evidence,
            intensity=0.5
        )
    
    def classify_overall(self) -> BehaviorState:
        """
        Classify overall listening behavior across all history.
        
        Returns:
            Overall BehaviorState
        """
        if not self.tracks:
            return BehaviorState("unknown", 0.0, [])
        
        evidence = []
        
        # Overall replay tendency
        total_replays = sum(1 for count in self._track_counts.values() if count > 1)
        replay_tendency = total_replays / len(set(t.track_id for t in self.tracks))
        
        # Time preferences
        hours = [t.timestamp.hour for t in self.tracks]
        avg_hour = sum(hours) / len(hours)
        
        # Listening frequency
        days = set(t.timestamp.date() for t in self.tracks)
        consistency = len(days) / ((self.tracks[-1].timestamp.date() - self.tracks[0].timestamp.date()).days + 1)
        
        # Classify based on dominant pattern
        if replay_tendency > 0.4:
            evidence.append(f"High replay tendency ({replay_tendency:.0%})")
            if avg_hour >= 22 or avg_hour <= 3:
                evidence.append("Late-night listening preference")
                return BehaviorState("chronic_ruminator", 0.75, evidence, intensity=replay_tendency)
            else:
                return BehaviorState("comfort_oriented", 0.70, evidence, intensity=replay_tendency)
        
        if consistency > 0.7:
            evidence.append(f"Consistent daily listening ({consistency:.0%})")
            return BehaviorState("routine_driven", 0.80, evidence, intensity=consistency)
        
        evidence.append("Varied listening patterns")
        return BehaviorState("eclectic", 0.65, evidence, intensity=0.5)
    
    def detect_behavioral_events(self) -> List[Dict]:
        """
        Detect specific behavioral events/anomalies.
        
        Returns:
            List of event dictionaries with triggers for roast mode
        """
        events = []
        
        # Group into sessions (30 min gap)
        sessions = self._group_into_sessions()
        
        for session in sessions:
            # Late night replay loop
            avg_hour = sum(t.timestamp.hour for t in session) / len(session)
            if (22 <= avg_hour or avg_hour <= 3) and len(session) > 5:
                replays = [t for t in session if self._track_counts[t.track_id] > 3]
                if replays:
                    events.append({
                        "type": "late_night_replay",
                        "timestamp": session[0].timestamp,
                        "track": replays[0].song_name,
                        "count": self._track_counts[replays[0].track_id],
                        "hour": int(avg_hour)
                    })
            
            # Skip spree (context switches indicate skipping)
            contexts = [t.context_uri for t in session if t.context_uri]
            if len(set(contexts)) > 5:
                events.append({
                    "type": "skip_spree",
                    "timestamp": session[0].timestamp,
                    "switches": len(set(contexts)),
                    "tracks": len(session)
                })
            
            # Comfort loop (repeat + shuffle off)
            shuffle_off = all(not t.shuffle_state for t in session if t.shuffle_state is not None)
            repeat_on = any(t.repeat_state != "off" for t in session if t.repeat_state)
            
            if shuffle_off and repeat_on and len(session) > 8:
                events.append({
                    "type": "comfort_loop",
                    "timestamp": session[0].timestamp,
                    "duration_min": (session[-1].timestamp - session[0].timestamp).total_seconds() / 60
                })
            
            # Binge session
            duration_hours = (session[-1].timestamp - session[0].timestamp).total_seconds() / 3600
            if duration_hours > 4:
                events.append({
                    "type": "binge_session",
                    "timestamp": session[0].timestamp,
                    "duration_hours": duration_hours,
                    "tracks": len(session)
                })
        
        return events
    
    def _group_into_sessions(self, gap_minutes: int = 30) -> List[List[Track]]:
        """Group tracks into sessions based on time gaps."""
        if not self.tracks:
            return []
        
        sessions = []
        current_session = [self.tracks[0]]
        
        for track in self.tracks[1:]:
            gap = (track.timestamp - current_session[-1].timestamp).total_seconds() / 60
            
            if gap <= gap_minutes:
                current_session.append(track)
            else:
                sessions.append(current_session)
                current_session = [track]
        
        if current_session:
            sessions.append(current_session)
        
        return sessions
    
    def get_intensity_score(self) -> float:
        """
        Calculate overall listening intensity (0.0-1.0).
        
        Based on frequency, session length, and replay patterns.
        Higher = more intense/engaged listening.
        """
        if not self.tracks:
            return 0.0
        
        # Frequency component
        time_span_days = (self.tracks[-1].timestamp - self.tracks[0].timestamp).days + 1
        tracks_per_day = len(self.tracks) / time_span_days
        frequency_score = min(tracks_per_day / 50, 1.0)  # Cap at 50 tracks/day
        
        # Session length component
        sessions = self._group_into_sessions()
        avg_session_length = sum(len(s) for s in sessions) / len(sessions) if sessions else 0
        session_score = min(avg_session_length / 30, 1.0)  # Cap at 30 tracks/session
        
        # Replay component (high replay = high engagement)
        replay_score = min(sum(c > 1 for c in self._track_counts.values()) / len(self._track_counts), 1.0)
        
        # Weighted average
        intensity = (frequency_score * 0.4) + (session_score * 0.3) + (replay_score * 0.3)
        
        return round(intensity, 3)
    
    def get_deviation_score(self, recent_tracks: List[Track]) -> float:
        """
        Calculate how much recent behavior deviates from baseline.
        
        Args:
            recent_tracks: Recent listening history
            
        Returns:
            Deviation score (0.0 = consistent, 1.0 = very different)
        """
        if len(recent_tracks) < 5 or len(self.tracks) < 20:
            return 0.0
        
        # Calculate baseline patterns
        baseline_hours = [t.timestamp.hour for t in self.tracks]
        recent_hours = [t.timestamp.hour for t in recent_tracks]
        
        baseline_avg_hour = sum(baseline_hours) / len(baseline_hours)
        recent_avg_hour = sum(recent_hours) / len(recent_hours)
        
        hour_deviation = abs(baseline_avg_hour - recent_avg_hour) / 24
        
        # Replay deviation
        baseline_replay_rate = sum(self._track_counts[t.track_id] > 1 for t in self.tracks) / len(self.tracks)
        recent_replay_rate = sum(self._track_counts[t.track_id] > 1 for t in recent_tracks) / len(recent_tracks)
        
        replay_deviation = abs(baseline_replay_rate - recent_replay_rate)
        
        # Combined deviation
        deviation = (hour_deviation * 0.5) + (replay_deviation * 0.5)
        
        return round(min(deviation, 1.0), 3)
