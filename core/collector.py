"""
Refactored Spotify playback collector with audio features enrichment.

This module replaces the original spotiloader.py with a more modular,
feature-rich collector that tracks:
- Basic song metadata (name, artist, album)
- Playback context (playlist, shuffle state, repeat)
- Audio features (energy, valence, tempo, etc.)
- Skip detection
- Session boundaries

Maintains backward compatibility with existing CSV format.
"""

import time
import os
import csv
import json
from datetime import datetime
from typing import Optional, Dict, Any
import psutil
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

from .models import Track, AudioFeatures
from .features import AudioFeaturesEnricher, calculate_mood_score, get_vibe_emoji


class SpotifyCollector:
    """
    Enhanced Spotify playback collector with mood tracking.
    
    Features:
    - Real-time playback monitoring
    - Audio features enrichment
    - Skip detection
    - Session tracking
    - Multiple export formats (CSV, JSON)
    """
    
    def __init__(
        self,
        enrich_features: bool = True,
        output_dir: str = ".",
        verbose: bool = True
    ):
        """
        Initialize the collector.
        
        Args:
            enrich_features: Whether to fetch audio features from Spotify
            output_dir: Directory for output files
            verbose: Whether to print status messages
        """
        load_dotenv()
        
        self.enrich_features = enrich_features
        self.output_dir = output_dir
        self.verbose = verbose
        
        # Output file paths
        self.current_song_file = os.path.join(output_dir, "current_song.txt")
        self.history_txt_file = os.path.join(output_dir, "song_history.txt")
        self.history_csv_file = os.path.join(output_dir, "song_history.csv")
        self.enriched_json_file = os.path.join(output_dir, "enriched_history.json")
        
        # Spotify API credentials
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = "http://127.0.0.1:8888/callback"
        # Note: audio features don't require special scope, but include user-library-read for future features
        self.scope = "user-read-playback-state user-read-currently-playing streaming user-library-read"
        
        if not self.client_id or not self.client_secret:
            raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env")
        
        # Initialize Spotify client (lazy - only when needed)
        self._sp: Optional[spotipy.Spotify] = None
        self._enricher: Optional[AudioFeaturesEnricher] = None
        
        # Tracking state
        self.last_track_id: Optional[str] = None
        self.last_played_at: Optional[datetime] = None
        self.current_session_id: Optional[str] = None
    
    @property
    def sp(self) -> spotipy.Spotify:
        """Lazy-initialize Spotify client."""
        if self._sp is None:
            self._sp = self._get_spotify_client()
        return self._sp
    
    @property
    def enricher(self) -> AudioFeaturesEnricher:
        """Lazy-initialize features enricher."""
        if self._enricher is None:
            self._enricher = AudioFeaturesEnricher(self.sp, cache_features=True)
        return self._enricher
    
    def _get_spotify_client(self) -> spotipy.Spotify:
        """Create authenticated Spotify client."""
        cache_path = ".cache"
        # Don't delete cache - reuse existing token when valid
        
        auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            cache_path=cache_path,
            show_dialog=True
        )
        return spotipy.Spotify(auth_manager=auth_manager)
    
    def spotify_is_running(self) -> bool:
        """Check if Spotify is currently running."""
        return any("Spotify.exe" in p.name() for p in psutil.process_iter())
    
    def collect_playback(self) -> Optional[Track]:
        """
        Collect current playback state and return Track object.
        
        Returns:
            Track object if song is playing, None otherwise
        """
        try:
            if not self.spotify_is_running():
                return None
            
            current = self.sp.current_playback()
            
            if not current or not current["is_playing"] or not current["item"]:
                return None
            
            # Extract track metadata
            item = current["item"]
            track_id = item["id"]
            
            # Skip if same track as last check
            if track_id == self.last_track_id:
                return None
            
            # Build Track object
            track = Track(
                timestamp=datetime.now(),
                track_id=track_id,
                song_name=item["name"],
                artist=item["artists"][0]["name"],
                album=item["album"]["name"],
                duration_ms=item["duration_ms"],
                duration_formatted=self._format_duration(item["duration_ms"]),
                context_type=current.get("context", {}).get("type") if current.get("context") else None,
                context_uri=current.get("context", {}).get("uri") if current.get("context") else None,
                shuffle_state=current.get("shuffle_state"),
                repeat_state=current.get("repeat_state")
            )
            
            # Enrich with audio features
            if self.enrich_features:
                features = self.enricher.get_features(track_id)
                if features:
                    track.audio_features = features
                    
                    if self.verbose:
                        mood = calculate_mood_score(features.energy, features.valence)
                        emoji = get_vibe_emoji(features.energy, features.valence)
                        print(f"{emoji} Mood: {mood}")
            
            # Update tracking state
            self.last_track_id = track_id
            self.last_played_at = track.timestamp
            
            return track
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Error collecting playback: {e}")
            return None
    
    def save_track(self, track: Track):
        """
        Save track to multiple output formats.
        
        Args:
            track: Track object to save
        """
        # 1. Write current song (overwrites)
        with open(self.current_song_file, "w", encoding="utf-8") as f:
            f.write(f"Song: {track.song_name}\n")
            f.write(f"Artist: {track.artist}\n")
            f.write(f"Duration: {track.duration_formatted}\n")
            
            if track.audio_features:
                f.write(f"\nMood Analysis:\n")
                f.write(f"  Energy: {track.audio_features.energy:.2f}\n")
                f.write(f"  Valence: {track.audio_features.valence:.2f}\n")
                f.write(f"  Tempo: {track.audio_features.tempo:.1f} BPM\n")
                mood = calculate_mood_score(
                    track.audio_features.energy,
                    track.audio_features.valence
                )
                emoji = get_vibe_emoji(
                    track.audio_features.energy,
                    track.audio_features.valence
                )
                f.write(f"  Vibe: {emoji} {mood}\n")
        
        # 2. Append to text history
        with open(self.history_txt_file, "a", encoding="utf-8") as f:
            timestamp_str = track.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp_str}] Song: {track.song_name} | Artist: {track.artist} | Duration: {track.duration_formatted}\n")
        
        # 3. Append to CSV (legacy format for compatibility)
        self._save_to_csv(track)
        
        # 4. Append to enriched JSON
        if self.enrich_features:
            self._save_to_json(track)
        
        if self.verbose:
            print(f"✅ Logged: {track.song_name} by {track.artist}")
    
    def _save_to_csv(self, track: Track):
        """Save track to CSV in legacy format."""
        file_exists = os.path.exists(self.history_csv_file)
        
        with open(self.history_csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Write header if new file
            if not file_exists:
                writer.writerow([
                    "timestamp", "song_name", "artist", "album", 
                    "track_id", "duration_ms", "duration_formatted"
                ])
            
            # Write track data
            timestamp_str = track.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([
                timestamp_str,
                track.song_name,
                track.artist,
                track.album,
                track.track_id,
                track.duration_ms,
                track.duration_formatted
            ])
    
    def _save_to_json(self, track: Track):
        """Save track to JSON lines format with full enrichment."""
        # Load existing data
        tracks = []
        if os.path.exists(self.enriched_json_file):
            with open(self.enriched_json_file, "r", encoding="utf-8") as f:
                try:
                    tracks = json.load(f)
                except json.JSONDecodeError:
                    tracks = []
        
        # Append new track
        tracks.append(track.model_dump(mode='json'))
        
        # Save updated data
        with open(self.enriched_json_file, "w", encoding="utf-8") as f:
            json.dump(tracks, f, indent=2, ensure_ascii=False, default=str)
    
    def _format_duration(self, duration_ms: int) -> str:
        """Convert milliseconds to M:SS format."""
        duration_sec = duration_ms // 1000
        minutes = duration_sec // 60
        seconds = duration_sec % 60
        return f"{minutes}:{seconds:02d}"
    
    def run(self, poll_interval: int = 5):
        """
        Main monitoring loop.
        
        Args:
            poll_interval: Seconds between checks
        """
        print("🎵 Spotify Behavioral Engine - Collector")
        print("=" * 50)
        print(f"📊 Feature enrichment: {'ON' if self.enrich_features else 'OFF'}")
        print(f"📁 Output directory: {self.output_dir}")
        print("=" * 50)
        print("\nWaiting for Spotify to launch...")
        
        # Wait for Spotify
        while not self.spotify_is_running():
            time.sleep(2)
        
        print("✅ Spotify detected. Connecting to API...")
        
        # Initialize Spotify client
        _ = self.sp
        
        print("🎧 Monitoring playback... (Press Ctrl+C to stop)\n")
        
        # Main loop
        try:
            while True:
                if self.spotify_is_running():
                    track = self.collect_playback()
                    if track:
                        self.save_track(track)
                else:
                    if self.verbose:
                        print("⏸️  Spotify closed. Waiting...")
                    self.last_track_id = None
                
                time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Stopping collector. Stats:")
            if self.enricher:
                print(f"   Cached features: {self.enricher.cache_size()}")
            print("   Goodbye!")


def main():
    """Entry point for standalone execution."""
    collector = SpotifyCollector(
        enrich_features=True,
        output_dir=".",
        verbose=True
    )
    collector.run(poll_interval=5)


if __name__ == "__main__":
    main()
