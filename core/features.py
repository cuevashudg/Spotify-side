"""
Audio features enrichment module.

Fetches Spotify's audio analysis data (energy, valence, tempo, etc.)
and enriches track records with psychological/musical insights.
"""

import time
from typing import List, Optional, Dict, Any
from spotipy import Spotify
from .models import AudioFeatures


class AudioFeaturesEnricher:
    """
    Fetches and caches audio features from Spotify API.
    
    Features include:
    - Mood metrics (energy, valence)
    - Musical characteristics (tempo, key, mode)
    - Production qualities (acousticness, instrumentalness)
    
    Usage:
        enricher = AudioFeaturesEnricher(spotify_client)
        features = enricher.get_features("track_id_here")
        batch_features = enricher.get_features_batch(["id1", "id2", ...])
    """
    
    def __init__(self, spotify_client: Spotify, cache_features: bool = True):
        """
        Initialize the enricher.
        
        Args:
            spotify_client: Authenticated Spotipy client
            cache_features: Whether to cache features in memory (reduces API calls)
        """
        self.sp = spotify_client
        self.cache_features = cache_features
        self._cache: Dict[str, AudioFeatures] = {}
    
    def get_features(self, track_id: str, retry_on_failure: bool = True) -> Optional[AudioFeatures]:
        """
        Fetch audio features for a single track.
        
        Args:
            track_id: Spotify track ID
            retry_on_failure: Whether to retry once on API failure
            
        Returns:
            AudioFeatures object or None if fetch fails
        """
        # Check cache first
        if self.cache_features and track_id in self._cache:
            return self._cache[track_id]
        
        try:
            # Fetch from Spotify API
            raw_features = self.sp.audio_features([track_id])[0]
            
            if raw_features is None:
                print(f"⚠️  No audio features available for track {track_id}")
                return None
            
            # Convert to our model
            features = self._parse_features(raw_features)
            
            # Cache result
            if self.cache_features:
                self._cache[track_id] = features
            
            return features
            
        except Exception as e:
            print(f"❌ Error fetching features for {track_id}: {e}")
            
            # Retry logic
            if retry_on_failure:
                print("   Retrying in 2 seconds...")
                time.sleep(2)
                return self.get_features(track_id, retry_on_failure=False)
            
            return None
    
    def get_features_batch(self, track_ids: List[str], batch_size: int = 50) -> Dict[str, AudioFeatures]:
        """
        Fetch audio features for multiple tracks efficiently.
        
        Spotify API allows up to 100 tracks per request, but we use 50 to be safe.
        
        Args:
            track_ids: List of Spotify track IDs
            batch_size: Number of tracks per API request (max 100)
            
        Returns:
            Dictionary mapping track_id -> AudioFeatures
        """
        results = {}
        uncached_ids = []
        
        # Check cache first
        if self.cache_features:
            for track_id in track_ids:
                if track_id in self._cache:
                    results[track_id] = self._cache[track_id]
                else:
                    uncached_ids.append(track_id)
        else:
            uncached_ids = track_ids
        
        # Fetch uncached tracks in batches
        for i in range(0, len(uncached_ids), batch_size):
            batch = uncached_ids[i:i + batch_size]
            
            try:
                # Fetch batch from API
                raw_features_list = self.sp.audio_features(batch)
                
                # Parse each result
                for raw_features in raw_features_list:
                    if raw_features is None:
                        continue
                    
                    features = self._parse_features(raw_features)
                    track_id = features.track_id
                    
                    results[track_id] = features
                    
                    # Cache
                    if self.cache_features:
                        self._cache[track_id] = features
                
                # Rate limiting - be nice to Spotify API
                if len(uncached_ids) > batch_size:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"❌ Error fetching batch starting at index {i}: {e}")
                continue
        
        # Report results
        success_rate = (len(results) / len(track_ids)) * 100 if track_ids else 0
        print(f"✅ Enriched {len(results)}/{len(track_ids)} tracks ({success_rate:.1f}%)")
        
        return results
    
    def _parse_features(self, raw_features: Dict[str, Any]) -> AudioFeatures:
        """
        Convert Spotify API response to our AudioFeatures model.
        
        Args:
            raw_features: Raw JSON response from Spotify API
            
        Returns:
            Validated AudioFeatures object
        """
        return AudioFeatures(
            track_id=raw_features["id"],
            energy=raw_features["energy"],
            valence=raw_features["valence"],
            danceability=raw_features["danceability"],
            acousticness=raw_features["acousticness"],
            instrumentalness=raw_features["instrumentalness"],
            speechiness=raw_features["speechiness"],
            liveness=raw_features["liveness"],
            loudness=raw_features["loudness"],
            tempo=raw_features["tempo"],
            key=raw_features["key"],
            mode=raw_features["mode"],
            time_signature=raw_features["time_signature"],
            duration_ms=raw_features["duration_ms"]
        )
    
    def clear_cache(self):
        """Clear the in-memory feature cache."""
        self._cache.clear()
        print("🗑️  Feature cache cleared")
    
    def cache_size(self) -> int:
        """Return number of cached features."""
        return len(self._cache)


def calculate_mood_score(energy: float, valence: float) -> str:
    """
    Classify mood based on energy and valence dimensions.
    
    Russell's Circumplex Model of Affect:
    - High energy + High valence = Excited/Happy
    - High energy + Low valence = Angry/Tense
    - Low energy + High valence = Calm/Relaxed
    - Low energy + Low valence = Sad/Depressed
    
    Args:
        energy: Energy level (0.0-1.0)
        valence: Musical positivity (0.0-1.0)
        
    Returns:
        Mood label string
    """
    if energy > 0.6:
        if valence > 0.6:
            return "Energetic & Happy"
        elif valence < 0.4:
            return "Intense & Aggressive"
        else:
            return "Energetic & Neutral"
    elif energy < 0.4:
        if valence > 0.6:
            return "Calm & Peaceful"
        elif valence < 0.4:
            return "Melancholic & Low"
        else:
            return "Reflective & Subdued"
    else:
        if valence > 0.6:
            return "Upbeat & Pleasant"
        elif valence < 0.4:
            return "Somber & Tense"
        else:
            return "Balanced & Neutral"


def get_vibe_emoji(energy: float, valence: float) -> str:
    """
    Get emoji representation of mood.
    
    Args:
        energy: Energy level (0.0-1.0)
        valence: Musical positivity (0.0-1.0)
        
    Returns:
        Emoji string
    """
    if energy > 0.6 and valence > 0.6:
        return "🔥😄"  # High energy, high valence
    elif energy > 0.6 and valence < 0.4:
        return "⚡😤"  # High energy, low valence
    elif energy < 0.4 and valence > 0.6:
        return "🌙😌"  # Low energy, high valence
    elif energy < 0.4 and valence < 0.4:
        return "🌧️😢"  # Low energy, low valence
    else:
        return "🎵😐"  # Neutral
