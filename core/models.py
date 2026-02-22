from dataclasses import dataclass

# New abstraction for behavioral signals
@dataclass
class BehaviorSignal:
    name: str
    value: float
    source: str  # e.g., 'audio_features', 'user_event', etc.
    confidence: float = 1.0  # Default to 1.0 if not probabilistic
"""
Data models for Spotify behavioral tracking.

Provides typed, validated data structures for tracks, audio features,
playback sessions, and listening behavior.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class AudioFeatures(BaseModel):
    """
    Spotify's audio analysis features for a track.
    
    These metrics provide psychological and musical insights:
    - energy: Intensity and activity level (0.0-1.0)
    - valence: Musical positivity/happiness (0.0-1.0)
    - danceability: How suitable for dancing (0.0-1.0)
    - acousticness: Confidence the track is acoustic (0.0-1.0)
    - instrumentalness: Predicts if track has no vocals (0.0-1.0)
    - speechiness: Presence of spoken words (0.0-1.0)
    - liveness: Presence of audience (0.0-1.0)
    """
    track_id: str
    energy: float = Field(ge=0.0, le=1.0)
    valence: float = Field(ge=0.0, le=1.0)
    danceability: float = Field(ge=0.0, le=1.0)
    acousticness: float = Field(ge=0.0, le=1.0)
    instrumentalness: float = Field(ge=0.0, le=1.0)
    speechiness: float = Field(ge=0.0, le=1.0)
    liveness: float = Field(ge=0.0, le=1.0)
    loudness: float  # dB, typically -60 to 0
    tempo: float  # BPM
    key: int = Field(ge=0, le=11)  # Pitch class (0=C, 1=C#, etc.)
    mode: int = Field(ge=0, le=1)  # 0=minor, 1=major
    time_signature: int  # Beats per measure
    duration_ms: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "track_id": "5wZZR79ILc8mLha7fKgQJd",
                "energy": 0.78,
                "valence": 0.65,
                "danceability": 0.72,
                "acousticness": 0.12,
                "instrumentalness": 0.0,
                "speechiness": 0.05,
                "liveness": 0.11,
                "loudness": -5.2,
                "tempo": 128.0,
                "key": 7,
                "mode": 1,
                "time_signature": 4,
                "duration_ms": 232116
            }
        }


class Track(BaseModel):
    """
    A logged song play with metadata and audio features.
    
    Represents a single listening event with context about what was played,
    when, and psychological characteristics of the track.
    """
    timestamp: datetime
    track_id: str
    song_name: str
    artist: str
    album: str
    duration_ms: int
    duration_formatted: str
    
    # Context about how it was played
    context_type: Optional[str] = None  # playlist, album, artist, collection
    context_uri: Optional[str] = None
    shuffle_state: Optional[bool] = None
    repeat_state: Optional[str] = None  # off, track, context
    
    # Enriched audio features (fetched separately)
    audio_features: Optional[AudioFeatures] = None
    
    # Session metadata
    session_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-20T15:01:07",
                "track_id": "5wZZR79ILc8mLha7fKgQJd",
                "song_name": "Be Right There - Sleepy Tom's Decade Mix",
                "artist": "Diplo",
                "album": "Be Right There (Sleepy Tom's Decade Mix)",
                "duration_ms": 232116,
                "duration_formatted": "3:52",
                "context_type": "playlist",
                "shuffle_state": True,
                "repeat_state": "off"
            }
        }


class SkipEvent(BaseModel):
    """
    A track that was skipped before completion.
    
    Skip psychology reveals a lot:
    - Why was it skipped?
    - How far into the song?
    - What was played next?
    """
    timestamp: datetime
    track_id: str
    song_name: str
    artist: str
    
    # Skip context
    played_duration_ms: int
    total_duration_ms: int
    skip_percentage: float  # How far through the song
    
    # Session context
    session_id: Optional[str] = None
    position_in_session: Optional[int] = None  # Was this the 5th song? 20th?
    
    # What replaced it
    next_track_id: Optional[str] = None
    next_track_name: Optional[str] = None
    
    @field_validator('skip_percentage', mode='before')
    @classmethod
    def calculate_skip_percentage(cls, v, info):
        """Auto-calculate skip percentage if not provided."""
        if v is None and 'played_duration_ms' in info.data and 'total_duration_ms' in info.data:
            return (info.data['played_duration_ms'] / info.data['total_duration_ms']) * 100
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-20T15:05:32",
                "track_id": "abc123",
                "song_name": "Sad Song",
                "artist": "Depresso",
                "played_duration_ms": 45000,
                "total_duration_ms": 210000,
                "skip_percentage": 21.4,
                "next_track_name": "Happy Banger"
            }
        }
