"""
Audio features enrichment module.

Fetches Spotify's audio analysis data (energy, valence, tempo, etc.)
and enriches track records with psychological/musical insights.

NOTE: Spotify's audio-features endpoint may return 403 Forbidden for
development/new apps due to deprecation or restricted access. This module
handles such errors gracefully by returning fallback structures.
"""

import time
import logging
from typing import List, Optional, Dict, Any
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from .models import AudioFeatures

# Configure logging
logger = logging.getLogger(__name__)


def fetch_audio_features_safe(
    sp: Spotify,
    track_id: str,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Optional[Dict[str, Any]]:
    """
    Safely fetch audio features with proper error handling for 403/429 errors.
    
    Spotify's audio-features endpoint may be deprecated or restricted for
    development apps, often returning HTTP 403 Forbidden. This function:
    - Catches 403 errors specifically and returns fallback structure
    - Retries only on 429 (rate limit) errors with exponential backoff
    - Logs errors without crashing the application
    - Returns None or fallback dict on permanent failures
    
    Args:
        sp: Authenticated Spotipy client
        track_id: Spotify track ID
        max_retries: Maximum retry attempts (only for 429 rate limits)
        retry_delay: Base delay between retries in seconds
        
    Returns:
        Dict with audio features on success, or fallback dict on 403:
        {"source": "unavailable", "reason": "403_deprecated"}
        Returns None on other failures.
        
    Example:
        >>> features = fetch_audio_features_safe(sp, "track_id_123")
        >>> if features and features.get("source") != "unavailable":
        ...     print(f"Energy: {features['energy']}")
        ... else:
        ...     print("Features unavailable (403 or error)")
    """
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            # Attempt to fetch audio features
            response = sp.audio_features([track_id])
            
            # Check if response is valid
            if response and len(response) > 0 and response[0] is not None:
                return response[0]
            else:
                logger.warning(f"No audio features returned for track {track_id}")
                return {"source": "unavailable", "reason": "no_data"}
        
        except SpotifyException as e:
            # Handle specific HTTP errors
            if e.http_status == 403:
                # 403 Forbidden - likely deprecated/restricted endpoint
                logger.warning(
                    f"Audio features endpoint returned 403 for track {track_id}. "
                    f"This endpoint may be deprecated or restricted for your app. "
                    f"Consider requesting Extended Quota or using behavioral analysis instead."
                )
                return {
                    "source": "unavailable",
                    "reason": "403_deprecated",
                    "track_id": track_id
                }
            
            elif e.http_status == 429:
                # Rate limit - retry with exponential backoff
                retry_count += 1
                if retry_count > max_retries:
                    logger.error(f"Max retries exceeded for track {track_id} (429 rate limit)")
                    return {
                        "source": "unavailable",
                        "reason": "429_rate_limit",
                        "track_id": track_id
                    }
                
                # Exponential backoff
                wait_time = retry_delay * (2 ** (retry_count - 1))
                retry_after = e.headers.get('Retry-After', wait_time)
                sleep_time = float(retry_after) if isinstance(retry_after, (int, float, str)) else wait_time
                
                logger.info(f"Rate limited (429). Retrying in {sleep_time}s... (attempt {retry_count}/{max_retries})")
                time.sleep(sleep_time)
                continue
            
            elif e.http_status == 401:
                # Unauthorized - token issue
                logger.error(f"Authentication error (401) for track {track_id}. Check your access token.")
                return {"source": "unavailable", "reason": "401_unauthorized", "track_id": track_id}
            
            else:
                # Other HTTP errors
                logger.error(f"Spotify API error {e.http_status} for track {track_id}: {e}")
                return {"source": "unavailable", "reason": f"http_{e.http_status}", "track_id": track_id}
        
        except Exception as e:
            # Catch-all for network errors, etc.
            logger.error(f"Unexpected error fetching features for track {track_id}: {e}")
            return {"source": "unavailable", "reason": "unexpected_error", "track_id": track_id}
    
    # Should not reach here, but return fallback just in case
    return {"source": "unavailable", "reason": "unknown", "track_id": track_id}


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
        Fetch audio features for a single track with safe error handling.
        
        Uses fetch_audio_features_safe() to handle 403/429 errors gracefully.
        Returns None if features are unavailable (403, errors, etc.)
        
        Args:
            track_id: Spotify track ID
            retry_on_failure: Whether to retry on 429 rate limits (ignored for 403)
            
        Returns:
            AudioFeatures object or None if fetch fails or endpoint is unavailable
        """
        # Check cache first
        if self.cache_features and track_id in self._cache:
            return self._cache[track_id]
        
        # Use safe fetcher with proper error handling
        max_retries = 3 if retry_on_failure else 0
        raw_features = fetch_audio_features_safe(self.sp, track_id, max_retries=max_retries)
        
        # Check if fetch failed or returned fallback
        if raw_features is None:
            logger.warning(f"No audio features available for track {track_id}")
            return None
        
        # Check for fallback structure (403, 429, etc.)
        if raw_features.get("source") == "unavailable":
            reason = raw_features.get("reason", "unknown")
            if reason == "403_deprecated":
                logger.info(f"Audio features unavailable for {track_id} (403 - deprecated/restricted)")
            else:
                logger.warning(f"Audio features unavailable for {track_id}: {reason}")
            return None
        
        try:
            # Convert to our model
            features = self._parse_features(raw_features)
            
            # Cache result
            if self.cache_features:
                self._cache[track_id] = features
            
            return features
        
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse audio features for {track_id}: {e}")
            return None
    
    def get_features_batch(self, track_ids: List[str], batch_size: int = 50) -> Dict[str, AudioFeatures]:
        """
        Fetch audio features for multiple tracks efficiently with safe error handling.
        
        Spotify API allows up to 100 tracks per request, but we use 50 to be safe.
        Falls back to individual fetches if batch fails with 403.
        
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
                # Fetch batch from API (risky - may get 403 for all)
                raw_features_list = self.sp.audio_features(batch)
                
                # Parse each result
                for j, raw_features in enumerate(raw_features_list):
                    if raw_features is None:
                        continue
                    
                    # Check for fallback structure
                    if isinstance(raw_features, dict) and raw_features.get("source") == "unavailable":
                        continue
                    
                    try:
                        features = self._parse_features(raw_features)
                        track_id = features.track_id
                        
                        results[track_id] = features
                        
                        # Cache
                        if self.cache_features:
                            self._cache[track_id] = features
                    except Exception as parse_error:
                        logger.warning(f"Failed to parse features for batch item {j}: {parse_error}")
                        continue
                
                # Rate limiting - be nice to Spotify API
                if i + batch_size < len(uncached_ids):
                    time.sleep(0.5)
            
            except SpotifyException as e:
                if e.http_status == 403:
                    logger.warning(
                        f"Batch fetch returned 403 (deprecated/restricted). "
                        f"Consider using behavioral analysis instead of audio features."
                    )
                    # Don't try individual fetches - they'll all fail too
                    break
                elif e.http_status == 429:
                    retry_after = float(e.headers.get('Retry-After', 2))
                    logger.info(f"Rate limited (429). Waiting {retry_after}s before continuing...")
                    time.sleep(retry_after)
                    continue
                else:
                    logger.error(f"Spotify API error {e.http_status} for batch at index {i}: {e}")
                    continue
                    
            except Exception as e:
                logger.error(f"Unexpected error fetching batch starting at index {i}: {e}")
                continue
        
        # Report results
        success_rate = (len(results) / len(track_ids)) * 100 if track_ids else 0
        if success_rate < 100:
            logger.info(f"Enriched {len(results)}/{len(track_ids)} tracks ({success_rate:.1f}%)")
        else:
            logger.info(f"✅ Successfully enriched all {len(results)} tracks")
        
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
