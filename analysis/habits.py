"""
Listening habits analysis module.

Analyzes patterns like:
- Most active listening times
- Day of week preferences
- Artist/genre loyalty
- Listening duration patterns
"""

from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter, defaultdict
import statistics

from core.models import Track


class HabitsAnalyzer:
    """
    Analyze listening behavior patterns and habits.
    """
    
    def __init__(self, tracks: List[Track]):
        """
        Initialize analyzer with track history.
        
        Args:
            tracks: List of Track objects
        """
        self.tracks = tracks
    
    def get_listening_hours(self) -> Dict:
        """
        Analyze most active listening hours.
        
        Returns:
            Dictionary with hour distribution and peak times
        """
        hour_counts = Counter(track.timestamp.hour for track in self.tracks)
        
        if not hour_counts:
            return {"error": "No tracks found"}
        
        total = sum(hour_counts.values())
        
        # Convert to percentage and sort
        hour_distribution = {
            hour: {
                "count": count,
                "percentage": round((count / total) * 100, 1)
            }
            for hour, count in sorted(hour_counts.items())
        }
        
        # Find peak hours (top 3)
        top_hours = hour_counts.most_common(3)
        
        return {
            "total_tracks": total,
            "distribution": hour_distribution,
            "peak_hours": [
                {"hour": hour, "count": count}
                for hour, count in top_hours
            ],
            "most_active_hour": top_hours[0][0] if top_hours else None
        }
    
    def get_day_of_week_pattern(self) -> Dict:
        """
        Analyze listening patterns by day of week.
        
        Returns:
            Dictionary with day distribution
        """
        day_names = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        ]
        
        day_counts = Counter(track.timestamp.weekday() for track in self.tracks)
        
        if not day_counts:
            return {"error": "No tracks found"}
        
        total = sum(day_counts.values())
        
        distribution = {
            day_names[day]: {
                "count": day_counts.get(day, 0),
                "percentage": round((day_counts.get(day, 0) / total) * 100, 1)
            }
            for day in range(7)
        }
        
        most_active_day = max(day_counts.items(), key=lambda x: x[1])
        
        return {
            "total_tracks": total,
            "distribution": distribution,
            "most_active_day": day_names[most_active_day[0]],
            "is_weekend_listener": self._is_weekend_listener(day_counts)
        }
    
    def _is_weekend_listener(self, day_counts: Counter) -> bool:
        """Determine if user primarily listens on weekends."""
        weekend = day_counts.get(5, 0) + day_counts.get(6, 0)
        weekday = sum(day_counts.get(i, 0) for i in range(5))
        
        if weekend + weekday == 0:
            return False
        
        return weekend > weekday
    
    def get_top_artists(self, limit: int = 10) -> List[Dict]:
        """
        Get most played artists.
        
        Args:
            limit: Number of artists to return
            
        Returns:
            List of artists with play counts
        """
        artist_counts = Counter(track.artist for track in self.tracks)
        
        total = len(self.tracks)
        
        return [
            {
                "artist": artist,
                "play_count": count,
                "percentage": round((count / total) * 100, 1)
            }
            for artist, count in artist_counts.most_common(limit)
        ]
    
    def get_listening_streaks(self) -> Dict:
        """
        Analyze consecutive days of listening.
        
        Returns:
            Dictionary with streak statistics
        """
        if not self.tracks:
            return {"error": "No tracks found"}
        
        # Get unique days
        days = sorted(set(
            track.timestamp.date()
            for track in self.tracks
        ))
        
        if not days:
            return {"error": "No listening days found"}
        
        # Calculate streaks
        streaks = []
        current_streak = 1
        
        for i in range(1, len(days)):
            if (days[i] - days[i-1]).days == 1:
                current_streak += 1
            else:
                if current_streak > 1:
                    streaks.append(current_streak)
                current_streak = 1
        
        if current_streak > 1:
            streaks.append(current_streak)
        
        # Calculate current streak
        today = datetime.now().date()
        current_active_streak = 0
        
        for i in range(len(days) - 1, -1, -1):
            if (today - days[i]).days == current_active_streak:
                current_active_streak += 1
            else:
                break
        
        return {
            "total_listening_days": len(days),
            "total_streaks": len(streaks),
            "longest_streak": max(streaks) if streaks else 1,
            "average_streak": round(statistics.mean(streaks), 1) if streaks else 1,
            "current_streak": current_active_streak,
            "first_listen": days[0].isoformat(),
            "last_listen": days[-1].isoformat()
        }
    
    def get_session_patterns(self) -> Dict:
        """
        Analyze listening session patterns.
        
        Returns:
            Dictionary with session statistics
        """
        # Group tracks by session (30 min gap = new session)
        sessions = []
        current_session = []
        
        sorted_tracks = sorted(self.tracks, key=lambda t: t.timestamp)
        
        for track in sorted_tracks:
            if not current_session:
                current_session.append(track)
            else:
                last_track = current_session[-1]
                gap = (track.timestamp - last_track.timestamp).total_seconds() / 60
                
                if gap <= 30:
                    current_session.append(track)
                else:
                    if current_session:
                        sessions.append(current_session)
                    current_session = [track]
        
        if current_session:
            sessions.append(current_session)
        
        if not sessions:
            return {"error": "No sessions found"}
        
        session_lengths = [len(s) for s in sessions]
        session_durations = [
            sum(t.duration_ms for t in s) / 60000  # Convert to minutes
            for s in sessions
        ]
        
        return {
            "total_sessions": len(sessions),
            "avg_tracks_per_session": round(statistics.mean(session_lengths), 1),
            "avg_session_duration_min": round(statistics.mean(session_durations), 1),
            "longest_session_tracks": max(session_lengths),
            "shortest_session_tracks": min(session_lengths),
            "longest_session_min": round(max(session_durations), 1),
            "total_listening_time_hours": round(sum(session_durations) / 60, 1)
        }
    
    def get_repeat_behavior(self) -> Dict:
        """
        Analyze track repetition patterns.
        
        Returns:
            Dictionary with repeat statistics
        """
        track_counts = Counter(track.track_id for track in self.tracks)
        
        repeat_tracks = {
            track_id: count
            for track_id, count in track_counts.items()
            if count > 1
        }
        
        if not repeat_tracks:
            return {
                "total_unique_tracks": len(track_counts),
                "repeated_tracks": 0,
                "repeat_percentage": 0
            }
        
        # Find most repeated tracks
        most_repeated = []
        for track_id in sorted(repeat_tracks, key=repeat_tracks.get, reverse=True)[:5]:
            # Find track details
            track = next((t for t in self.tracks if t.track_id == track_id), None)
            if track:
                most_repeated.append({
                    "song": track.song_name,
                    "artist": track.artist,
                    "play_count": repeat_tracks[track_id]
                })
        
        return {
            "total_unique_tracks": len(track_counts),
            "repeated_tracks": len(repeat_tracks),
            "repeat_percentage": round((len(repeat_tracks) / len(track_counts)) * 100, 1),
            "most_repeated": most_repeated,
            "diversity_score": round(len(track_counts) / len(self.tracks), 3)
        }
    
    def get_context_preferences(self) -> Dict:
        """
        Analyze playback context preferences (playlist, album, etc.).
        
        Returns:
            Dictionary with context distribution
        """
        context_counts = Counter(
            track.context_type if track.context_type else "unknown"
            for track in self.tracks
        )
        
        total = len(self.tracks)
        
        shuffle_count = sum(1 for t in self.tracks if t.shuffle_state is True)
        
        return {
            "total_tracks": total,
            "context_distribution": {
                context: {
                    "count": count,
                    "percentage": round((count / total) * 100, 1)
                }
                for context, count in context_counts.most_common()
            },
            "shuffle_usage": {
                "count": shuffle_count,
                "percentage": round((shuffle_count / total) * 100, 1)
            }
        }
