"""
Session detection and tracking logic.

A session is a continuous period of listening, detected by:
- Time gaps (>30 minutes = new session)
- Major context switches (playlist changes)
- Manual boundaries

Sessions reveal listening patterns and mood trajectories over time.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from .models import Track, ListeningSession


class SessionDetector:
    """
    Detects and tracks listening sessions.
    
    Sessions help identify:
    - How long you listen in one sitting
    - Mood evolution during a session
    - Skip patterns within sessions
    - Context switching behavior
    """
    
    def __init__(self, gap_threshold_minutes: int = 30):
        """
        Initialize session detector.
        
        Args:
            gap_threshold_minutes: Minutes of inactivity before new session
        """
        self.gap_threshold = timedelta(minutes=gap_threshold_minutes)
        self.current_session: Optional[ListeningSession] = None
        self.completed_sessions: List[ListeningSession] = []
    
    def process_track(self, track: Track) -> Optional[ListeningSession]:
        """
        Process a track and update session state.
        
        Args:
            track: Newly played track
            
        Returns:
            Completed session if one just ended, None otherwise
        """
        completed = None
        
        # First track ever
        if self.current_session is None:
            self._start_new_session(track)
            return None
        
        # Check for session boundary
        time_gap = track.timestamp - self.current_session.end_time
        
        if time_gap > self.gap_threshold:
            # Gap detected - complete current session
            completed = self._complete_session()
            self._start_new_session(track)
        else:
            # Continue current session
            self._add_to_session(track)
        
        return completed
    
    def _start_new_session(self, first_track: Track):
        """Start a new listening session."""
        session_id = first_track.timestamp.strftime("%Y-%m-%d_%H-%M")
        
        self.current_session = ListeningSession(
            session_id=session_id,
            start_time=first_track.timestamp,
            end_time=first_track.timestamp,
            track_ids=[first_track.track_id],
            total_tracks=1,
            total_duration_ms=first_track.duration_ms,
            unique_artists=1
        )
        
        # Add audio features if available
        if first_track.audio_features:
            self.current_session.avg_energy = first_track.audio_features.energy
            self.current_session.avg_valence = first_track.audio_features.valence
            self.current_session.avg_tempo = first_track.audio_features.tempo
        
        # Update track with session ID
        first_track.session_id = session_id
    
    def _add_to_session(self, track: Track):
        """Add track to current session."""
        if self.current_session is None:
            return
        
        # Update session metadata
        self.current_session.end_time = track.timestamp
        self.current_session.track_ids.append(track.track_id)
        self.current_session.total_tracks += 1
        self.current_session.total_duration_ms += track.duration_ms
        
        # Update audio feature averages (running average)
        if track.audio_features:
            n = self.current_session.total_tracks
            
            # Running average formula: new_avg = old_avg + (new_value - old_avg) / n
            if self.current_session.avg_energy is not None:
                self.current_session.avg_energy += (
                    track.audio_features.energy - self.current_session.avg_energy
                ) / n
            else:
                self.current_session.avg_energy = track.audio_features.energy
            
            if self.current_session.avg_valence is not None:
                self.current_session.avg_valence += (
                    track.audio_features.valence - self.current_session.avg_valence
                ) / n
            else:
                self.current_session.avg_valence = track.audio_features.valence
            
            if self.current_session.avg_tempo is not None:
                self.current_session.avg_tempo += (
                    track.audio_features.tempo - self.current_session.avg_tempo
                ) / n
            else:
                self.current_session.avg_tempo = track.audio_features.tempo
        
        # Update track with session ID
        track.session_id = self.current_session.session_id
    
    def _complete_session(self) -> ListeningSession:
        """Mark current session as complete and return it."""
        if self.current_session is None:
            return None
        
        completed = self.current_session
        self.completed_sessions.append(completed)
        self.current_session = None
        
        return completed
    
    def force_complete_session(self) -> Optional[ListeningSession]:
        """
        Manually complete the current session.
        
        Useful when stopping the collector to ensure the last
        session is properly recorded.
        
        Returns:
            Completed session or None if no active session
        """
        return self._complete_session()
    
    def get_session_summary(self) -> dict:
        """
        Get summary statistics for all sessions.
        
        Returns:
            Dictionary with session analytics
        """
        all_sessions = self.completed_sessions.copy()
        if self.current_session:
            all_sessions.append(self.current_session)
        
        if not all_sessions:
            return {"total_sessions": 0}
        
        total_tracks = sum(s.total_tracks for s in all_sessions)
        total_duration_ms = sum(s.total_duration_ms for s in all_sessions)
        avg_duration_ms = total_duration_ms / len(all_sessions)
        avg_tracks_per_session = total_tracks / len(all_sessions)
        
        # Calculate average session mood
        sessions_with_mood = [s for s in all_sessions if s.avg_energy is not None]
        if sessions_with_mood:
            avg_energy = sum(s.avg_energy for s in sessions_with_mood) / len(sessions_with_mood)
            avg_valence = sum(s.avg_valence for s in sessions_with_mood) / len(sessions_with_mood)
        else:
            avg_energy = None
            avg_valence = None
        
        return {
            "total_sessions": len(all_sessions),
            "total_tracks": total_tracks,
            "avg_tracks_per_session": round(avg_tracks_per_session, 1),
            "avg_session_duration_min": round(avg_duration_ms / 60000, 1),
            "avg_energy": round(avg_energy, 2) if avg_energy else None,
            "avg_valence": round(avg_valence, 2) if avg_valence else None
        }
