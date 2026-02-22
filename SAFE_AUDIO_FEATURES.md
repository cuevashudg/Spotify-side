# Safe Audio Features Fetching

## Overview

Spotify's `GET /v1/audio-features` endpoint may return **HTTP 403 Forbidden** errors for development or new apps, despite being documented in the official API reference. This appears to be due to:

1. **Endpoint deprecation** or restricted access for new apps
2. **Extended Quota requirements** (apps in "Development Mode" limited to 25 users)
3. **Spotify's evolving API policies** around sensitive audio features

Our solution: **graceful fallback** with detailed error handling.

---

## The Problem

### Typical Error
```python
spotipy.exceptions.SpotifyException: http status: 403, code:-1
Reason: Forbidden
```

### Why It Happens
- **Development Mode**: Apps with <25 users may have restricted access
- **Deprecated Endpoint**: Spotify may be phasing out audio-features for new apps
- **Quota Issues**: Insufficient Extended Quota Mode approval

---

## The Solution: `fetch_audio_features_safe()`

A robust wrapper function that:
- ✅ **Catches 403 errors** specifically and returns fallback structure
- ✅ **Retries only on 429** (rate limit) with exponential backoff
- ✅ **Logs errors** without crashing your application
- ✅ **Returns structured fallback** for unavailable features
- ✅ **Never retries on 403** (no point if endpoint is blocked)

### Function Signature

```python
from core.features import fetch_audio_features_safe

def fetch_audio_features_safe(
    sp: Spotify,
    track_id: str,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Optional[Dict[str, Any]]:
    """
    Safely fetch audio features with proper 403/429 handling.
    
    Returns:
        - Full features dict on success
        - Fallback dict on 403: {"source": "unavailable", "reason": "403_deprecated"}
        - None on other failures
    """
```

---

## Usage Examples

### Example 1: Basic Usage

```python
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from core.features import fetch_audio_features_safe

# Create Spotify client
sp = Spotify(auth_manager=SpotifyOAuth(...))

# Fetch features safely
track_id = "3n3Ppam7vgaVa1iaRUc9Lp"
features = fetch_audio_features_safe(sp, track_id)

# Check result
if features is None:
    print("Unexpected error occurred")

elif features.get("source") == "unavailable":
    reason = features.get("reason")
    print(f"Features unavailable: {reason}")
    
    if reason == "403_deprecated":
        print("Endpoint blocked - use behavioral analysis instead")

else:
    # Success!
    print(f"Energy: {features['energy']:.2f}")
    print(f"Valence: {features['valence']:.2f}")
```

### Example 2: Integrated with AudioFeaturesEnricher

```python
from core import AudioFeaturesEnricher

# Create enricher (now uses safe fetcher internally)
enricher = AudioFeaturesEnricher(sp, cache_features=True)

# Get features (returns None on 403 or errors)
features = enricher.get_features("track_id_here")

if features:
    print(f"Mood: {features.energy} energy, {features.valence} valence")
else:
    print("Features unavailable - falling back to behavioral analysis")
```

### Example 3: Batch Processing with Fallback

```python
from core import AudioFeaturesEnricher
from analysis.behavior import BehaviorClassifier

enricher = AudioFeaturesEnricher(sp)
classifier = BehaviorClassifier()

# Try to enrich tracks
track_ids = ["id1", "id2", "id3"]
enriched = enricher.get_features_batch(track_ids)

# Check success rate
if len(enriched) < len(track_ids):
    print(f"⚠️  Only {len(enriched)}/{len(track_ids)} tracks enriched")
    print("💡 Using behavioral classification instead...")
    
    # Fall back to behavioral analysis
    behavior_state = classifier.classify_session(tracks)
    print(f"Detected behavior: {behavior_state.primary_state}")
```

---

## Return Values

### Success Case
```python
{
    "tempo": 120.5,
    "energy": 0.83,
    "valence": 0.45,
    "danceability": 0.68,
    "mode": 1,
    "key": 5,
    "acousticness": 0.12,
    # ... all standard audio features
}
```

### 403 Forbidden (Deprecated/Restricted)
```python
{
    "source": "unavailable",
    "reason": "403_deprecated",
    "track_id": "3n3Ppam7vgaVa1iaRUc9Lp"
}
```

### 429 Rate Limited (After Max Retries)
```python
{
    "source": "unavailable",
    "reason": "429_rate_limit",
    "track_id": "3n3Ppam7vgaVa1iaRUc9Lp"
}
```

### 401 Unauthorized
```python
{
    "source": "unavailable",
    "reason": "401_unauthorized",
    "track_id": "3n3Ppam7vgaVa1iaRUc9Lp"
}
```

### Other Errors
```python
{
    "source": "unavailable",
    "reason": "unexpected_error",
    "track_id": "3n3Ppam7vgaVa1iaRUc9Lp"
}
```

---

## Testing

Run the test script to verify behavior:

```bash
python scripts/test_safe_features.py
```

Expected output:
```
==================================================================
TESTING SAFE AUDIO FEATURES FETCHER
==================================================================

📀 Testing: Mr. Brightside - The Killers
   Track ID: 3n3Ppam7vgaVa1iaRUc9Lp
------------------------------------------------------------------
   ⚠️  Result: Unavailable
   Reason: 403_deprecated
   ℹ️  This is expected if Spotify restricted the endpoint.
   💡 Suggestion: Use behavioral analysis instead.
```

---

## Error Handling Flow

```
┌─────────────────────────┐
│ fetch_audio_features_   │
│        safe()           │
└──────────┬──────────────┘
           │
           ├──> [API Call]
           │
           ├──> Success? ──> Return full features dict
           │
           ├──> 403? ──────> Log warning
           │                 Return fallback dict
           │                 (DO NOT RETRY)
           │
           ├──> 429? ──────> Retry with exponential backoff
           │                 (up to max_retries)
           │                 If still failing: return fallback
           │
           ├──> 401? ──────> Log auth error
           │                 Return fallback dict
           │
           └──> Other? ────> Log error
                             Return fallback dict
```

---

## Integration with Existing Code

The `AudioFeaturesEnricher` class has been updated to use `fetch_audio_features_safe()` internally:

```python
# OLD (crashes on 403)
raw_features = self.sp.audio_features([track_id])[0]

# NEW (safe, returns None on 403)
raw_features = fetch_audio_features_safe(self.sp, track_id, max_retries=3)
```

**No changes needed** to existing code using `AudioFeaturesEnricher`!

---

## Fallback Strategy: Behavioral Analysis

When audio features are unavailable (403), use our **behavioral classification system**:

```python
from analysis.behavior import BehaviorClassifier

classifier = BehaviorClassifier()
behavior = classifier.classify_session(tracks)

print(f"State: {behavior.primary_state}")
print(f"Confidence: {behavior.confidence:.2f}")
print(f"Indicators: {behavior.indicators}")
```

**Advantages over audio features:**
- ✅ No API dependency (no 403 errors!)
- ✅ More personalized (based on actual listening patterns)
- ✅ Captures emotional context (replay behavior, time-of-day)
- ✅ Interview-worthy technical achievement

See `BEHAVIORAL_SYSTEM.md` for full details.

---

## Resolving 403 Errors (Long-term)

If you want to re-enable audio features:

1. **Check Spotify Developer Dashboard**
   - Verify app is in "Extended Quota Mode"
   - Confirm redirect URI matches exactly
   - Check if app exceeds 25-user Development Mode limit

2. **Request Extended Quota**
   - Submit quota extension request if needed
   - May take several days for approval

3. **Alternative: Audio Analysis Endpoint**
   - Use `GET /v1/audio-analysis/{id}` instead
   - Provides deeper data (sections, bars, beats)
   - May have better availability for new apps

---

## Key Takeaways

✅ **403 errors are now handled gracefully** - your app won't crash
✅ **Retry logic only for 429** - no wasted API calls on deprecated endpoints  
✅ **Structured fallback** - easy to detect and handle unavailable features
✅ **Behavioral analysis works independently** - no audio features needed
✅ **Production-ready** - safe for deployment with proper logging

**When in doubt, use behavioral analysis instead of audio features!** 🚀
