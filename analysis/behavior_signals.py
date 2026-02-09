"""
Signal-based behavioral inference engine.

Architecture:
- BehaviorSignal: Abstract base class for behavioral indicators
- Concrete signals: LateNightSignal, ReplaySignal, SessionLengthSignal
- BehaviorBaseline: Historical statistics for deviation detection
- BehaviorClassifier: Weighted scoring system that aggregates signals
- BehaviorState: Result with state, confidence, evidence, and intensity

Benefits:
- Extensible: Add new signals without modifying core logic
- Explainable: Each signal provides clear evidence
- Modular: Signals are isolated and reusable
- API-independent: No dependency on Spotify features
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from enum import Enum
from collections import Counter

from core.models import Track


# ============================================================================
# BEHAVIOR STATE & BASELINE
# ============================================================================


@dataclass
class BehaviorState:
    """
    Represents an inferred behavioral/emotional state.
    
    Based on listening patterns, not audio features.
    Includes secondary behaviors for nuanced, personalized output.
    """
    
    state: str
    """Primary behavior label (e.g., 'ruminating', 'focused')"""
    
    confidence: float
    """0.0-1.0 confidence in primary classification"""
    
    evidence: List[str] = field(default_factory=list)
    """Behavioral signals that led to this classification"""
    
    intensity: float = 0.5
    """0.0-1.0 intensity of the primary behavior"""
    
    secondary_behaviors: List[Tuple[str, float]] = field(default_factory=list)
    """Secondary behaviors as [(behavior_name, score), ...] for nuance"""
    
    def __repr__(self):
        secondary_str = ""
        if self.secondary_behaviors:
            secondary_str = f", secondary={[b[0] for b in self.secondary_behaviors]}"
        return f"BehaviorState(state='{self.state}', confidence={self.confidence:.2f}, intensity={self.intensity:.2f}{secondary_str})"


@dataclass
class BehaviorBaseline:
    """
    Historical statistics for a listener's baseline behavior.
    
    Used to detect deviations and compute relative scores.
    """
    
    avg_session_length_minutes: float
    """Average duration of a listening session"""
    
    avg_replay_rate: float
    """Fraction of repeated tracks in typical sessions"""
    
    avg_listening_hour: float
    """Average hour of day (0-24) when listening"""
    
    avg_context_switches: float
    """Average number of context changes per session"""
    
    typical_session_tracks: float
    """Average number of tracks per session"""
    
    @classmethod
    def compute(cls, sessions: List[List[Track]], all_tracks: List[Track]) -> "BehaviorBaseline":
        """
        Compute baseline from historical sessions.
        
        Args:
            sessions: List of track lists (raw session data)
            all_tracks: Complete track history for computing replay rates
            
        Returns:
            BehaviorBaseline with computed statistics
        """
        if not sessions:
            # Sensible defaults if no history
            return cls(
                avg_session_length_minutes=30.0,
                avg_replay_rate=0.15,
                avg_listening_hour=12.0,
                avg_context_switches=0.5,
                typical_session_tracks=15.0
            )
        
        # Convert to ListeningSession objects for property access
        listening_sessions = [
            ListeningSession(
                session_id=f"baseline_session_{i}",
                tracks=session_tracks,
                all_tracks_history=all_tracks
            )
            for i, session_tracks in enumerate(sessions)
        ]
        
        # Session duration
        durations = [s.duration_minutes for s in listening_sessions]
        avg_session_length = sum(durations) / len(durations) if durations else 30.0
        
        # Replay rates
        replay_rates = [s.replay_rate for s in listening_sessions]
        avg_replay_rate = sum(replay_rates) / len(replay_rates) if replay_rates else 0.15
        
        # Listening hours
        hours = [s.avg_hour for s in listening_sessions]
        avg_listening_hour = sum(hours) / len(hours) if hours else 12.0
        
        # Context switches
        switches = [s.context_switches for s in listening_sessions]
        avg_context_switches = sum(switches) / len(switches) if switches else 0.5
        
        # Tracks per session
        track_counts = [s.total_tracks for s in listening_sessions]
        typical_session_tracks = sum(track_counts) / len(track_counts) if track_counts else 15.0
        
        return cls(
            avg_session_length_minutes=avg_session_length,
            avg_replay_rate=avg_replay_rate,
            avg_listening_hour=avg_listening_hour,
            avg_context_switches=avg_context_switches,
            typical_session_tracks=typical_session_tracks
        )


# ============================================================================
# BEHAVIOR SIGNALS (ABSTRACT & CONCRETE)
# ============================================================================


class BehaviorSignal(ABC):
    """
    Abstract base for behavioral signals.
    
    Each signal evaluates a specific aspect of listening behavior
    and returns a score + evidence for its conclusions.
    """
    
    @abstractmethod
    def evaluate(
        self,
        session: "ListeningSession",
        baseline: BehaviorBaseline,
        all_tracks: List[Track]
    ) -> Dict[str, Tuple[float, List[str]]]:
        """
        Evaluate this signal against a session.
        
        Args:
            session: Current listening session
            baseline: Historical baseline for comparison
            all_tracks: All historical tracks (for frequency analysis)
            
        Returns:
            Dict mapping behavior_name -> (score, evidence_list)
            Score should be 0.0-1.0
            Evidence should contain 1-2 descriptive strings
        """
        pass


class LateNightSignal(BehaviorSignal):
    """
    Detects late-night listening patterns.
    
    Late-night (22:00-03:00) listening indicates different mental states:
    - Ruminating on specific tracks
    - Insomnia or sleep struggles
    - Winding down before bed
    """
    
    LATE_NIGHT_START = 22
    LATE_NIGHT_END = 3
    
    def evaluate(
        self,
        session: "ListeningSession",
        baseline: BehaviorBaseline,
        all_tracks: List[Track]
    ) -> Dict[str, Tuple[float, List[str]]]:
        """
        Evaluate late-night listening patterns.
        
        Returns:
            Scores for 'ruminating' behavior if late-night detected
        """
        avg_hour = session.avg_hour
        
        # Check if session is in late-night window
        is_late_night = (avg_hour >= self.LATE_NIGHT_START or avg_hour < self.LATE_NIGHT_END)
        
        if not is_late_night:
            return {}
        
        # Score for ruminating behavior (late night + replay)
        replay_factor = min(session.replay_rate / max(baseline.avg_replay_rate, 0.15), 1.0)
        late_night_score = 0.7 * replay_factor  # Base 0.7 for late night + replay factor
        
        evidence = [
            f"Late-night listening ({int(avg_hour):02d}:00)",
            f"Replay rate: {session.replay_rate:.0%} vs baseline {baseline.avg_replay_rate:.0%}"
        ]
        
        return {
            "ruminating": (late_night_score, evidence)
        }


class ReplaySignal(BehaviorSignal):
    """
    Detects replay-based behaviors.
    
    High replay rates indicate:
    - Comfort seeking (familiar music)
    - Song addiction (single track loops)
    - Routine-driven consumption
    """
    
    def evaluate(
        self,
        session: "ListeningSession",
        baseline: BehaviorBaseline,
        all_tracks: List[Track]
    ) -> Dict[str, Tuple[float, List[str]]]:
        """
        Evaluate replay behavior.
        
        Returns:
            Scores for 'comfort_seeking' (primary) and optionally 'routine_driven'
        """
        replay_rate = session.replay_rate
        baseline_replay = baseline.avg_replay_rate
        
        # Only score if replay is elevated vs baseline
        if replay_rate <= baseline_replay:
            return {}
        
        # Calculate deviation from baseline
        replay_deviation = replay_rate - baseline_replay
        normalized_deviation = min(replay_deviation / (baseline_replay + 0.1), 1.0)
        
        comfort_score = 0.5 + (normalized_deviation * 0.4)  # 0.5-0.9 range
        
        evidence = [
            f"Elevated replay rate: {replay_rate:.0%} "
            f"(baseline: {baseline_replay:.0%})"
        ]
        
        results = {
            "comfort_seeking": (comfort_score, evidence)
        }
        
        # Also score routine_driven if the replay is moderate (not extreme)
        # This allows both behaviors to compete
        if normalized_deviation < 0.5:  # Moderate elevation
            routine_score = 0.4 + (normalized_deviation * 0.3)
            results["routine_driven"] = (routine_score, ["Consistent replay pattern"])
        
        return results


class SessionLengthSignal(BehaviorSignal):
    """
    Detects behavior based on session length.
    
    Long sessions indicate:
    - Focused immersion (if low skip rate)
    - Zoning out / passive consumption
    - Energized / engaged listening
    """
    
    FOCUSED_SESSION_MINUTES = 60
    ZONING_OUT_MINUTES = 90
    
    def evaluate(
        self,
        session: "ListeningSession",
        baseline: BehaviorBaseline,
        all_tracks: List[Track]
    ) -> Dict[str, Tuple[float, List[str]]]:
        """
        Evaluate session length to infer behavior.
        
        Returns:
            Scores for 'focused', 'zoning_out', and/or 'routine_driven'
        """
        duration = session.duration_minutes
        results = {}
        
        # FOCUSED: 60-90 minutes + low context switches + low replay
        if duration >= self.FOCUSED_SESSION_MINUTES and duration < self.ZONING_OUT_MINUTES:
            if (session.context_switches <= 1 and 
                session.replay_rate < baseline.avg_replay_rate * 1.2):
                
                focus_score = min(duration / (self.FOCUSED_SESSION_MINUTES * 2), 0.9)
                results["focused"] = (
                    focus_score,
                    [f"Extended focused session ({duration:.0f} minutes)"]
                )
        
        # ZONING OUT: Very long session (90+ minutes, passive)
        if duration >= self.ZONING_OUT_MINUTES:
            zoning_score = min(duration / 180, 0.85)  # Cap at 0.85
            results["zoning_out"] = (
                zoning_score,
                [f"Extended passive session ({duration:.0f} minutes)"]
            )
        
        # ROUTINE_DRIVEN: Any moderate session (fallback)
        # This creates competition with focused/zoning behaviors
        if duration < self.FOCUSED_SESSION_MINUTES:
            routine_score = 0.5
            results["routine_driven"] = (routine_score, ["Regular session length"])
        elif duration < self.ZONING_OUT_MINUTES:
            # For focused-length sessions, also score routine as secondary
            routine_score = 0.3
            results["routine_driven"] = (routine_score, ["Extended but routine"])
        
        return results if results else {}


class ContextSwitchSignal(BehaviorSignal):
    """
    Detects searching / skipping behaviors.
    
    High context switches indicate:
    - Actively searching for something
    - Indecisive mood
    - High skip rate / restless behavior
    """
    
    def evaluate(
        self,
        session: "ListeningSession",
        baseline: BehaviorBaseline,
        all_tracks: List[Track]
    ) -> Dict[str, Tuple[float, List[str]]]:
        """
        Evaluate context switching (indicators of searching behavior).
        
        Returns:
            Scores for 'searching' if high switches detected
        """
        switches = session.context_switches
        baseline_switches = baseline.avg_context_switches
        
        # Only score if elevated vs baseline
        if switches <= baseline_switches:
            return {}
        
        switch_factor = min(switches / max(baseline_switches * 2, 3), 1.0)
        search_score = 0.6 + (switch_factor * 0.3)  # 0.6-0.9 range
        
        evidence = [
            f"High context switching: {switches} "
            f"(baseline: {baseline_switches:.1f})"
        ]
        
        return {
            "searching": (search_score, evidence)
        }


# ============================================================================
# LISTENING SESSION (ENHANCED)
# ============================================================================


class ListeningSession:
    """
    Represents a continuous listening session.
    
    Stores actual Track objects and computes derived properties
    for efficient behavioral analysis.
    """
    
    def __init__(
        self,
        session_id: str,
        tracks: List[Track],
        all_tracks_history: Optional[List[Track]] = None
    ):
        """
        Initialize a listening session.
        
        Args:
            session_id: Unique session identifier
            tracks: List of Track objects in this session (chronological order)
            all_tracks_history: Optional full track history for frequency analysis
        """
        self.session_id = session_id
        self.tracks = sorted(tracks, key=lambda t: t.timestamp)
        self.all_tracks_history = all_tracks_history or tracks
        
        # Pre-compute properties
        self._track_id_counts: Counter = self._compute_track_frequencies()
    
    def _compute_track_frequencies(self) -> Counter:
        """Count play frequency of each track across all history."""
        return Counter(t.track_id for t in self.all_tracks_history)
    
    @property
    def total_tracks(self) -> int:
        """Total number of tracks in this session."""
        return len(self.tracks)
    
    @property
    def duration_minutes(self) -> float:
        """Total duration of session in minutes."""
        if len(self.tracks) < 2:
            return 0.0
        
        time_span = self.tracks[-1].timestamp - self.tracks[0].timestamp
        return time_span.total_seconds() / 60
    
    @property
    def avg_hour(self) -> float:
        """Average hour of day (0-24) for this session."""
        if not self.tracks:
            return 12.0
        
        hours = [t.timestamp.hour for t in self.tracks]
        return sum(hours) / len(hours)
    
    @property
    def replay_rate(self) -> float:
        """Fraction of tracks in session that were played before."""
        if not self.tracks:
            return 0.0
        
        repeated = sum(
            1 for t in self.tracks 
            if self._track_id_counts.get(t.track_id, 0) > 1
        )
        
        return repeated / len(self.tracks)
    
    @property
    def context_switches(self) -> int:
        """Number of unique contexts (playlists/albums) switched through."""
        contexts = set(
            t.context_uri 
            for t in self.tracks 
            if t.context_uri
        )
        return len(contexts)
    
    @property
    def start_time(self) -> datetime:
        """Timestamp of first track in session."""
        return self.tracks[0].timestamp if self.tracks else datetime.now()
    
    @property
    def end_time(self) -> datetime:
        """Timestamp of last track in session."""
        return self.tracks[-1].timestamp if self.tracks else datetime.now()
    
    def __repr__(self):
        return (
            f"ListeningSession(id='{self.session_id}', "
            f"tracks={self.total_tracks}, "
            f"duration={self.duration_minutes:.0f}min"
        )


# ============================================================================
# BEHAVIOR CLASSIFIER
# ============================================================================


class BehaviorClassifier:
    """
    Classify listening behavior using signal-based weighted scoring.
    
    Instead of early returns, each signal contributes a score.
    The dominant behavior (highest score) becomes the classification.
    
    Extension: Add new signals by:
    1. Create a new BehaviorSignal subclass
    2. Add to self.signals list
    """
    
    # Define all available behaviors and their ranges
    BEHAVIORS = {
        "ruminating": {"description": "Late-night replay loops"},
        "comfort_seeking": {"description": "Repeat on, familiar music"},
        "searching": {"description": "High skip rate, indecisive"},
        "focused": {"description": "Long immersion, low interruption"},
        "zoning_out": {"description": "Extended passive listening"},
        "casual": {"description": "Standard listening patterns"}
    }
    
    def __init__(self, all_tracks: List[Track]):
        """
        Initialize classifier with track history.
        
        Args:
            all_tracks: Complete track history
        """
        self.all_tracks = sorted(all_tracks, key=lambda t: t.timestamp)
        
        # Precompute baseline from all tracks grouped into sessions
        sessions = self._group_into_sessions(all_tracks)
        self.baseline = BehaviorBaseline.compute(sessions, self.all_tracks)
        
        # Initialize all signals (add new ones here to extend)
        self.signals: List[BehaviorSignal] = [
            LateNightSignal(),
            ReplaySignal(),
            SessionLengthSignal(),
            ContextSwitchSignal(),
        ]
    
    def classify_session(self, session_tracks: List[Track]) -> BehaviorState:
        """
        Classify behavior for a listening session using signal-based scoring.
        
        Args:
            session_tracks: Tracks from one listening session
            
        Returns:
            BehaviorState with state, confidence, evidence, intensity
        """
        if not session_tracks:
            return BehaviorState(
                state="unknown",
                confidence=0.0,
                evidence=["Empty session"]
            )
        
        # Create ListeningSession object
        session = ListeningSession(
            session_id=f"session_{session_tracks[0].timestamp.isoformat()}",
            tracks=session_tracks,
            all_tracks_history=self.all_tracks
        )
        
        # Accumulate scores from all signals
        behavior_scores: Dict[str, Tuple[float, List[str]]] = {}
        
        for signal in self.signals:
            signal_results = signal.evaluate(session, self.baseline, self.all_tracks)
            
            for behavior, (score, evidence) in signal_results.items():
                if behavior not in behavior_scores:
                    behavior_scores[behavior] = (score, evidence)
                else:
                    # Average scores if multiple signals contribute
                    prev_score, prev_evidence = behavior_scores[behavior]
                    avg_score = (prev_score + score) / 2
                    behavior_scores[behavior] = (avg_score, prev_evidence + evidence)
        
        # If no signals fired, default to casual
        if not behavior_scores:
            return BehaviorState(
                state="casual",
                confidence=0.60,
                evidence=["Standard listening pattern"],
                intensity=0.5,
                secondary_behaviors=[]
            )
        
        # Sort behaviors by score (descending)
        sorted_behaviors = sorted(
            behavior_scores.items(),
            key=lambda x: x[1][0],
            reverse=True
        )
        
        # Primary behavior (highest score)
        state_name, (primary_score, primary_evidence) = sorted_behaviors[0]
        confidence = min(primary_score, 1.0)
        intensity = self._compute_intensity(session, state_name)
        
        # Secondary behaviors (next 2, if they exist)
        secondary_behaviors = []
        if len(sorted_behaviors) > 1:
            for behavior_name, (score, _) in sorted_behaviors[1:3]:
                secondary_behaviors.append((behavior_name, min(score, 1.0)))
        
        # Enhance evidence to mention secondary behaviors if they're significant
        evidence = primary_evidence
        if secondary_behaviors and secondary_behaviors[0][1] > 0.3:
            secondary_str = ", ".join(
                f"{name} ({score:.0%})" 
                for name, score in secondary_behaviors[:1]
            )
            evidence.append(f"Secondary: {secondary_str}")
        
        return BehaviorState(
            state=state_name,
            confidence=confidence,
            evidence=evidence,
            intensity=intensity,
            secondary_behaviors=secondary_behaviors
        )
    
    def classify_overall(self) -> BehaviorState:
        """
        Classify overall listening behavior across all history.
        
        Returns:
            Overall BehaviorState (routine-driven, chronic ruminator, etc.)
        """
        if not self.all_tracks:
            return BehaviorState(
                state="unknown",
                confidence=0.0,
                evidence=[]
            )
        
        # Group into sessions
        sessions = self._group_into_sessions(self.all_tracks)
        if not sessions:
            return BehaviorState(
                state="unknown",
                confidence=0.0,
                evidence=[]
            )
        
        # Classify each session, aggregate results
        state_counts: Dict[str, int] = {}
        all_secondary_behaviors: Dict[str, float] = {}
        
        for session_tracks in sessions:
            session_state = self.classify_session(session_tracks)
            state_counts[session_state.state] = state_counts.get(session_state.state, 0) + 1
            
            # Track secondary behaviors
            for behavior_name, score in session_state.secondary_behaviors:
                all_secondary_behaviors[behavior_name] = all_secondary_behaviors.get(behavior_name, 0) + score
        
        # Most common state
        dominant_state = max(state_counts.items(), key=lambda x: x[1])
        state_name, count = dominant_state
        
        confidence = count / len(sessions)
        
        evidence = [f"Dominant in {count}/{len(sessions)} sessions ({confidence:.0%})"]
        
        # Compute secondary behaviors (average across sessions)
        secondary_behaviors: List[Tuple[str, float]] = []
        if all_secondary_behaviors:
            secondary_avg = {
                behavior: score / len(sessions)
                for behavior, score in all_secondary_behaviors.items()
            }
            secondary_behaviors = sorted(
                secondary_avg.items(),
                key=lambda x: x[1],
                reverse=True
            )[:2]  # Top 2 secondary behaviors
        
        # Map to overall state
        overall_state_map = {
            "ruminating": "chronic_ruminator",
            "comfort_seeking": "comfort_oriented",
            "searching": "restless_searcher",
            "focused": "focused_listener",
            "zoning_out": "passive_listener",
            "casual": "routine_driven"
        }
        
        overall_name = overall_state_map.get(state_name, "eclectic")
        
        return BehaviorState(
            state=overall_name,
            confidence=confidence,
            evidence=evidence,
            intensity=self._compute_overall_intensity(),
            secondary_behaviors=secondary_behaviors
        )
    
    def _compute_intensity(self, session: ListeningSession, behavior: str) -> float:
        """
        Compute intensity for a specific behavior in a session.
        
        Args:
            session: The listening session
            behavior: The classified behavior
            
        Returns:
            0.0-1.0 intensity score
        """
        if behavior == "ruminating":
            return min(session.replay_rate * 1.5, 1.0)
        elif behavior == "comfort_seeking":
            return session.replay_rate
        elif behavior == "searching":
            return min(session.context_switches / 5, 1.0)
        elif behavior == "focused":
            return min(session.duration_minutes / 120, 1.0)
        elif behavior == "zoning_out":
            return min(session.duration_minutes / 180, 1.0)
        else:
            return 0.5
    
    def _compute_overall_intensity(self) -> float:
        """Compute overall listening intensity across all history."""
        if not self.all_tracks:
            return 0.0
        
        # Frequency component (tracks per day)
        time_span_days = (self.all_tracks[-1].timestamp - self.all_tracks[0].timestamp).days + 1
        tracks_per_day = len(self.all_tracks) / time_span_days
        frequency_score = min(tracks_per_day / 50, 1.0)  # Cap at 50 tracks/day
        
        # Session length component
        sessions = self._group_into_sessions(self.all_tracks)
        if sessions:
            avg_session_tracks = sum(len(s) for s in sessions) / len(sessions)
            session_score = min(avg_session_tracks / 30, 1.0)  # Cap at 30 tracks/session
        else:
            session_score = 0.0
        
        # Replay component
        track_counts = Counter(t.track_id for t in self.all_tracks)
        replay_score = min(
            sum(1 for c in track_counts.values() if c > 1) / len(track_counts),
            1.0
        )
        
        # Weighted average
        intensity = (frequency_score * 0.4) + (session_score * 0.3) + (replay_score * 0.3)
        
        return round(intensity, 3)
    
    def _group_into_sessions(
        self,
        tracks: List[Track],
        gap_minutes: int = 30
    ) -> List[List[Track]]:
        """
        Group tracks into sessions based on time gaps.
        
        Args:
            tracks: Tracks to group
            gap_minutes: Minutes between tracks before new session
            
        Returns:
            List of session track lists
        """
        if not tracks:
            return []
        
        sorted_tracks = sorted(tracks, key=lambda t: t.timestamp)
        sessions = []
        current_session = [sorted_tracks[0]]
        
        for track in sorted_tracks[1:]:
            gap = (track.timestamp - current_session[-1].timestamp).total_seconds() / 60
            
            if gap <= gap_minutes:
                current_session.append(track)
            else:
                sessions.append(current_session)
                current_session = [track]
        
        if current_session:
            sessions.append(current_session)
        
        return sessions
    
    # ========================================================================
    # BACKWARD COMPATIBILITY METHODS (for roast_engine integration)
    # ========================================================================
    
    def detect_behavioral_events(self) -> List[Dict]:
        """
        Detect specific behavioral events/anomalies.
        
        Returns event dictionaries for roast engine integration.
        
        Returns:
            List of event dictionaries with triggers for roast mode
        """
        events = []
        
        # Group into sessions
        sessions = self._group_into_sessions(self.all_tracks)
        
        # Precompute track counts
        track_counts = Counter(t.track_id for t in self.all_tracks)
        
        for session in sessions:
            # Late night replay loop
            avg_hour = sum(t.timestamp.hour for t in session) / len(session)
            if (22 <= avg_hour or avg_hour <= 3) and len(session) > 5:
                replays = [t for t in session if track_counts[t.track_id] > 3]
                if replays:
                    events.append({
                        "type": "late_night_replay",
                        "timestamp": session[0].timestamp,
                        "track": replays[0].song_name,
                        "count": track_counts[replays[0].track_id],
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
    
    def get_intensity_score(self) -> float:
        """
        Calculate overall listening intensity (0.0-1.0).
        
        Based on frequency, session length, and replay patterns.
        Higher = more intense/engaged listening.
        
        Returns:
            Intensity score between 0.0 and 1.0
        """
        return self._compute_overall_intensity()
    
    def get_deviation_score(self, recent_tracks: List[Track]) -> float:
        """
        Calculate how much recent behavior deviates from baseline.
        
        Args:
            recent_tracks: Recent listening history
            
        Returns:
            Deviation score (0.0 = consistent, 1.0 = very different)
        """
        if len(recent_tracks) < 5 or len(self.all_tracks) < 20:
            return 0.0
        
        # Calculate baseline patterns
        baseline_hours = [t.timestamp.hour for t in self.all_tracks]
        recent_hours = [t.timestamp.hour for t in recent_tracks]
        
        baseline_avg_hour = sum(baseline_hours) / len(baseline_hours)
        recent_avg_hour = sum(recent_hours) / len(recent_hours)
        
        hour_deviation = abs(baseline_avg_hour - recent_avg_hour) / 24
        
        # Replay deviation
        track_counts = Counter(t.track_id for t in self.all_tracks)
        baseline_replay_rate = sum(track_counts[t.track_id] > 1 for t in self.all_tracks) / len(self.all_tracks)
        recent_replay_rate = sum(track_counts[t.track_id] > 1 for t in recent_tracks) / len(recent_tracks)
        
        replay_deviation = abs(baseline_replay_rate - recent_replay_rate)
        
        # Combined deviation
        deviation = (hour_deviation * 0.5) + (replay_deviation * 0.5)
        
        return round(min(deviation, 1.0), 3)
