"""
Migration script to enrich existing song history with audio features.

This script:
1. Reads your existing song_history.csv
2. Fetches audio features for each unique track
3. Exports enriched data to enriched_history.json

Usage:
    python scripts/enrich_history.py
"""

import os
import sys
import csv
import json
from datetime import datetime
from typing import List, Dict

# Add parent directory to path to import core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

from core.models import Track, AudioFeatures
from core.features import AudioFeaturesEnricher, calculate_mood_score, get_vibe_emoji


def load_csv_history(csv_path: str) -> List[Dict]:
    """
    Load existing song history from CSV.
    
    Args:
        csv_path: Path to song_history.csv
        
    Returns:
        List of track dictionaries
    """
    tracks = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tracks.append({
                "timestamp": row["timestamp"],
                "song_name": row["song_name"],
                "artist": row["artist"],
                "album": row["album"],
                "track_id": row["track_id"],
                "duration_ms": int(row["duration_ms"]),
                "duration_formatted": row["duration_formatted"]
            })
    
    return tracks


def get_spotify_client() -> spotipy.Spotify:
    """Create authenticated Spotify client."""
    load_dotenv()
    
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env")
    
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://127.0.0.1:8888/callback",
        scope="user-read-playback-state user-read-currently-playing",
        cache_path=".cache-enricher",
        show_dialog=False
    )
    
    return spotipy.Spotify(auth_manager=auth_manager)


def enrich_tracks(tracks: List[Dict], enricher: AudioFeaturesEnricher) -> List[Track]:
    """
    Enrich tracks with audio features.
    
    Args:
        tracks: List of track dictionaries from CSV
        enricher: AudioFeaturesEnricher instance
        
    Returns:
        List of enriched Track objects
    """
    # Get unique track IDs
    unique_track_ids = list(set(t["track_id"] for t in tracks))
    
    print(f"🎵 Found {len(tracks)} plays across {len(unique_track_ids)} unique tracks")
    print(f"📡 Fetching audio features from Spotify...\n")
    
    # Fetch features in batch
    features_map = enricher.get_features_batch(unique_track_ids)
    
    # Build enriched Track objects
    enriched_tracks = []
    
    for track_dict in tracks:
        # Parse timestamp
        try:
            timestamp = datetime.strptime(track_dict["timestamp"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            timestamp = datetime.now()
        
        # Create Track object
        track = Track(
            timestamp=timestamp,
            track_id=track_dict["track_id"],
            song_name=track_dict["song_name"],
            artist=track_dict["artist"],
            album=track_dict["album"],
            duration_ms=track_dict["duration_ms"],
            duration_formatted=track_dict["duration_formatted"]
        )
        
        # Add audio features if available
        if track_dict["track_id"] in features_map:
            track.audio_features = features_map[track_dict["track_id"]]
        
        enriched_tracks.append(track)
    
    return enriched_tracks


def export_enriched_json(tracks: List[Track], output_path: str):
    """
    Export enriched tracks to JSON.
    
    Args:
        tracks: List of Track objects
        output_path: Path to output JSON file
    """
    data = [track.model_dump(mode='json') for track in tracks]
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ Exported {len(tracks)} enriched tracks to: {output_path}")


def print_mood_summary(tracks: List[Track]):
    """
    Print a summary of mood analysis.
    
    Args:
        tracks: List of Track objects
    """
    tracks_with_features = [t for t in tracks if t.audio_features]
    
    if not tracks_with_features:
        print("\n⚠️  No audio features available for mood analysis")
        return
    
    # Calculate averages
    avg_energy = sum(t.audio_features.energy for t in tracks_with_features) / len(tracks_with_features)
    avg_valence = sum(t.audio_features.valence for t in tracks_with_features) / len(tracks_with_features)
    avg_tempo = sum(t.audio_features.tempo for t in tracks_with_features) / len(tracks_with_features)
    
    mood = calculate_mood_score(avg_energy, avg_valence)
    emoji = get_vibe_emoji(avg_energy, avg_valence)
    
    print("\n" + "="*50)
    print("📊 MOOD SUMMARY")
    print("="*50)
    print(f"Tracks analyzed: {len(tracks_with_features)}/{len(tracks)}")
    print(f"\nAverage Energy:  {avg_energy:.2f} (0=calm, 1=intense)")
    print(f"Average Valence: {avg_valence:.2f} (0=sad, 1=happy)")
    print(f"Average Tempo:   {avg_tempo:.1f} BPM")
    print(f"\nOverall Mood: {emoji} {mood}")
    print("="*50)


def main():
    """Main migration script."""
    print("🎵 Spotify History Enrichment Tool")
    print("="*50)
    
    # Check if CSV exists
    csv_path = "song_history.csv"
    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_path} not found")
        print("   Make sure you're running this from the Spotify-side directory")
        return
    
    # Load history
    print(f"📖 Loading history from {csv_path}...")
    tracks = load_csv_history(csv_path)
    
    if not tracks:
        print("❌ No tracks found in CSV")
        return
    
    # Initialize Spotify client
    print("🔑 Authenticating with Spotify...")
    sp = get_spotify_client()
    enricher = AudioFeaturesEnricher(sp, cache_features=True)
    
    # Enrich tracks
    enriched_tracks = enrich_tracks(tracks, enricher)
    
    # Export to JSON
    output_path = "enriched_history.json"
    export_enriched_json(enriched_tracks, output_path)
    
    # Print mood summary
    print_mood_summary(enriched_tracks)
    
    print("\n✨ Enrichment complete!")
    print(f"   You now have audio features for all your tracks")
    print(f"   Next: Run the new collector with audio features enabled")


if __name__ == "__main__":
    main()
