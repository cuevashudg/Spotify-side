# MoodScoringEngine: Accepts signals, computes averages, delegates to existing logic
class MoodScoringEngine:
    def __init__(self, signals: list[BehaviorSignal]):
        self.signals = signals

    def get_avg_energy_valence(self) -> tuple[float, float]:
        energies = [s.value for s in self.signals if s.name == "energy"]
        valences = [s.value for s in self.signals if s.name == "valence"]
        avg_energy = statistics.mean(energies) if energies else 0.0
        avg_valence = statistics.mean(valences) if valences else 0.0
        return avg_energy, avg_valence

    def calculate_mood(self):
        avg_energy, avg_valence = self.get_avg_energy_valence()
        mood = calculate_mood_score(avg_energy, avg_valence)
        emoji = get_vibe_emoji(avg_energy, avg_valence)
        return mood, emoji, avg_energy, avg_valence
from core.models import BehaviorSignal
# Helper: Convert AudioFeatures to list[BehaviorSignal]
def audio_features_to_signals(audio_features) -> list:
    """
    Convert AudioFeatures object to a list of BehaviorSignal objects.
    Only includes energy and valence for mood scoring.
    """
    if audio_features is None:
        return []
    return [
        BehaviorSignal(name="energy", value=audio_features.energy, source="audio_features", confidence=1.0),
        BehaviorSignal(name="valence", value=audio_features.valence, source="audio_features", confidence=1.0)
    ]
"""
Mood analysis module - Track energy and valence trends over time.

Analyzes:
- Daily mood patterns
- Mood shifts during sessions
- Energy/valence trajectories
- Correlation between mood and listening behavior
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import statistics

from core.models import Track
from core.features import calculate_mood_score, get_vibe_emoji


class MoodAnalyzer:
    """
    Analyze mood trends from listening history.
    
    Mood is calculated from audio features:
    - Energy: Intensity level (0.0-1.0)
    - Valence: Musical positivity (0.0-1.0)
    """
    
    def __init__(self, tracks: List[Track]):
        """
        Initialize analyzer with track history.
        
        Args:
            tracks: List of Track objects with audio features
        """
        self.tracks = tracks
        self.tracks_with_features = [
            t for t in tracks if t.audio_features is not None
        ]
    
    def get_overall_mood(self) -> Dict:
        """
        Calculate overall mood statistics using MoodScoringEngine.
        
        Returns:
            Dictionary with average energy, valence, and mood label
        """
        if not self.tracks_with_features:
            return {
                "error": "No tracks with audio features",
                "total_tracks": len(self.tracks)
            }

        signals = []
        tempos = []
        for t in self.tracks_with_features:
            signals.extend(audio_features_to_signals(t.audio_features))
            tempos.append(t.audio_features.tempo)

        engine = MoodScoringEngine(signals)
        avg_energy, avg_valence = engine.get_avg_energy_valence()
        avg_tempo = statistics.mean(tempos)
        mood, emoji, _, _ = engine.calculate_mood()

        energies = [s.value for s in signals if s.name == "energy"]
        valences = [s.value for s in signals if s.name == "valence"]

        return {
            "total_tracks": len(self.tracks),
            "tracks_analyzed": len(self.tracks_with_features),
            "avg_energy": round(avg_energy, 3),
            "avg_valence": round(avg_valence, 3),
            "avg_tempo": round(avg_tempo, 1),
            "mood_label": mood,
            "emoji": emoji,
            "energy_std": round(statistics.stdev(energies), 3) if len(energies) > 1 else 0,
            "valence_std": round(statistics.stdev(valences), 3) if len(valences) > 1 else 0
        }
    
    def get_mood_by_hour(self) -> Dict[int, Dict]:
        """
        Group mood statistics by hour of day using MoodScoringEngine.
        
        Returns:
            Dictionary mapping hour (0-23) to mood stats
        """
        hour_tracks = defaultdict(list)
        for track in self.tracks_with_features:
            hour = track.timestamp.hour
            hour_tracks[hour].append(track)

        hour_moods = {}
        for hour, tracks in hour_tracks.items():
            signals = []
            for t in tracks:
                signals.extend(audio_features_to_signals(t.audio_features))
            engine = MoodScoringEngine(signals)
            avg_energy, avg_valence = engine.get_avg_energy_valence()
            mood, emoji, _, _ = engine.calculate_mood()
            hour_moods[hour] = {
                "count": len(tracks),
                "avg_energy": round(avg_energy, 3),
                "avg_valence": round(avg_valence, 3),
                "mood": mood,
                "emoji": emoji
            }
        return dict(sorted(hour_moods.items()))
    
    def get_mood_by_day(self) -> Dict[str, Dict]:
        """
        Group mood statistics by day using MoodScoringEngine.
        
        Returns:
            Dictionary mapping date string to mood stats
        """
        day_tracks = defaultdict(list)
        for track in self.tracks_with_features:
            day = track.timestamp.strftime("%Y-%m-%d")
            day_tracks[day].append(track)

        day_moods = {}
        for day, tracks in day_tracks.items():
            signals = []
            for t in tracks:
                signals.extend(audio_features_to_signals(t.audio_features))
            engine = MoodScoringEngine(signals)
            avg_energy, avg_valence = engine.get_avg_energy_valence()
            mood, emoji, _, _ = engine.calculate_mood()
            day_moods[day] = {
                "count": len(tracks),
                "avg_energy": round(avg_energy, 3),
                "avg_valence": round(avg_valence, 3),
                "mood": mood,
                "emoji": emoji
            }
        return dict(sorted(day_moods.items()))
    
    def detect_mood_shifts(self, window_size: int = 5) -> List[Dict]:
        """
        Detect significant mood shifts in listening sessions.
        
        Args:
            window_size: Number of tracks to compare for shift detection
            
        Returns:
            List of detected mood shifts with timestamps
        """
        if len(self.tracks_with_features) < window_size * 2:
            return []
        
        shifts = []
        
        for i in range(window_size, len(self.tracks_with_features) - window_size):
            # Compare previous window to next window
            before = self.tracks_with_features[i - window_size:i]
            after = self.tracks_with_features[i:i + window_size]
            
            before_energy = statistics.mean([t.audio_features.energy for t in before])
            after_energy = statistics.mean([t.audio_features.energy for t in after])
            
            before_valence = statistics.mean([t.audio_features.valence for t in before])
            after_valence = statistics.mean([t.audio_features.valence for t in after])
            
            energy_delta = after_energy - before_energy
            valence_delta = after_valence - before_valence
            
            # Detect significant shifts (threshold: 0.3)
            if abs(energy_delta) > 0.3 or abs(valence_delta) > 0.3:
                track = self.tracks_with_features[i]
                
                before_mood = calculate_mood_score(before_energy, before_valence)
                after_mood = calculate_mood_score(after_energy, after_valence)
                
                shifts.append({
                    "timestamp": track.timestamp.isoformat(),
                    "track": f"{track.song_name} by {track.artist}",
                    "before_mood": before_mood,
                    "after_mood": after_mood,
                    "energy_delta": round(energy_delta, 3),
                    "valence_delta": round(valence_delta, 3),
                    "shift_type": self._classify_shift(energy_delta, valence_delta)
                })
        
        return shifts
    
    def _classify_shift(self, energy_delta: float, valence_delta: float) -> str:
        """Classify the type of mood shift."""
        if energy_delta > 0.3 and valence_delta > 0.3:
            return "Energizing & Uplifting"
        elif energy_delta > 0.3 and valence_delta < -0.3:
            return "Intensifying & Darkening"
        elif energy_delta < -0.3 and valence_delta > 0.3:
            return "Calming & Brightening"
        elif energy_delta < -0.3 and valence_delta < -0.3:
            return "Mellowing & Saddening"
        elif abs(energy_delta) > 0.3:
            return "Energy Shift"
        else:
            return "Mood Shift"
    
    def get_mood_extremes(self) -> Dict:
        """
        Find the most extreme mood tracks.
        
        Returns:
            Dictionary with highest/lowest energy and valence tracks
        """
        if not self.tracks_with_features:
            return {}
        
        # Sort by energy
        by_energy = sorted(
            self.tracks_with_features,
            key=lambda t: t.audio_features.energy
        )
        
        # Sort by valence
        by_valence = sorted(
            self.tracks_with_features,
            key=lambda t: t.audio_features.valence
        )
        
        def track_dict(track: Track) -> Dict:
            return {
                "song": track.song_name,
                "artist": track.artist,
                "energy": round(track.audio_features.energy, 3),
                "valence": round(track.audio_features.valence, 3),
                "timestamp": track.timestamp.isoformat()
            }
        
        return {
            "highest_energy": track_dict(by_energy[-1]),
            "lowest_energy": track_dict(by_energy[0]),
            "happiest": track_dict(by_valence[-1]),
            "saddest": track_dict(by_valence[0])
        }


def load_tracks_from_json(filepath: str) -> List[Track]:
    """
    Load tracks from enriched_history.json.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        List of Track objects
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    tracks = []
    for item in data:
        # Parse timestamp
        timestamp = datetime.fromisoformat(item["timestamp"])
        
        # Create Track object
        track = Track(
            timestamp=timestamp,
            track_id=item["track_id"],
            song_name=item["song_name"],
            artist=item["artist"],
            album=item["album"],
            duration_ms=item["duration_ms"],
            duration_formatted=item["duration_formatted"]
        )
        
        # Add audio features if present
        if item.get("audio_features"):
            from core.models import AudioFeatures
            track.audio_features = AudioFeatures(**item["audio_features"])
        
        tracks.append(track)
    
    return tracks
