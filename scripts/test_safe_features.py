"""
Test script for safe audio features fetching.

Demonstrates how fetch_audio_features_safe() handles:
- Successful fetches (returns full features dict)
- 403 errors (returns fallback dict with reason)
- 429 rate limits (retries with exponential backoff)
- Other errors (returns fallback dict)

Usage:
    python scripts/test_safe_features.py
"""

import os
import sys
import logging
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.features import fetch_audio_features_safe

# Configure logging to see detailed messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_safe_fetcher():
    """Test the safe audio features fetcher with real tracks."""
    
    # Load environment
    load_dotenv()
    
    # Create Spotify client
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri="http://127.0.0.1:8888/callback",
        scope="user-read-playback-state"
    ))
    
    # Test with some popular track IDs
    test_tracks = [
        ("3n3Ppam7vgaVa1iaRUc9Lp", "Mr. Brightside - The Killers"),
        ("0VjIjW4GlUZAMYd2vXMi3b", "Blinding Lights - The Weeknd"),
        ("7qiZfU4dY1lWllzX7mPBI", "Shape of You - Ed Sheeran"),
    ]
    
    print("\n" + "="*70)
    print("TESTING SAFE AUDIO FEATURES FETCHER")
    print("="*70 + "\n")
    
    for track_id, track_name in test_tracks:
        print(f"\n📀 Testing: {track_name}")
        print(f"   Track ID: {track_id}")
        print("-" * 70)
        
        # Fetch with safe method
        result = fetch_audio_features_safe(sp, track_id, max_retries=2)
        
        # Analyze result
        if result is None:
            print("   ❌ Result: None (unexpected error)")
        
        elif result.get("source") == "unavailable":
            reason = result.get("reason", "unknown")
            print(f"   ⚠️  Result: Unavailable")
            print(f"   Reason: {reason}")
            
            if reason == "403_deprecated":
                print("   ℹ️  This is expected if Spotify restricted the endpoint.")
                print("   💡 Suggestion: Use behavioral analysis instead.")
            elif reason == "429_rate_limit":
                print("   ℹ️  Rate limited even after retries.")
                print("   💡 Suggestion: Reduce polling frequency.")
        
        else:
            # Success! Print key features
            print(f"   ✅ Result: Success")
            print(f"   Energy: {result.get('energy', 'N/A'):.2f}")
            print(f"   Valence: {result.get('valence', 'N/A'):.2f}")
            print(f"   Tempo: {result.get('tempo', 'N/A'):.1f} BPM")
            print(f"   Danceability: {result.get('danceability', 'N/A'):.2f}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    
    print("\n💡 Key Takeaways:")
    print("   - 403 errors are caught and logged without crashing")
    print("   - Fallback dicts let your code continue gracefully")
    print("   - Retries only happen on 429 (rate limit), not 403")
    print("   - Behavioral analysis works without audio features!")


if __name__ == "__main__":
    test_safe_fetcher()
