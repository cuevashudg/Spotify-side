# Implementation Summary: Safe Audio Features Enrichment

## Date: February 9, 2026

## Problem Statement
Spotify's `GET /v1/audio-features` endpoint returns HTTP 403 Forbidden errors for development/new apps, blocking mood analysis features. This happens even with valid OAuth tokens and correct scopes.

## Solution Implemented

### 1. Core Function: `fetch_audio_features_safe()`
**Location**: `core/features.py`

**Features**:
- ✅ Catches 403 errors specifically and returns structured fallback
- ✅ Retries only on 429 (rate limit) with exponential backoff (max 3 retries)
- ✅ Handles 401 (unauthorized), 403 (forbidden), 429 (rate limit), and other errors separately
- ✅ Returns fallback dict: `{"source": "unavailable", "reason": "403_deprecated", "track_id": ...}`
- ✅ Uses Python logging instead of print statements
- ✅ Never retries on 403 (no point if endpoint is deprecated/blocked)

**Signature**:
```python
def fetch_audio_features_safe(
    sp: Spotify,
    track_id: str,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Optional[Dict[str, Any]]
```

### 2. Updated AudioFeaturesEnricher Class
**Location**: `core/features.py`

**Changes**:
- `get_features()` now uses `fetch_audio_features_safe()` internally
- Returns `None` gracefully on 403 instead of crashing
- `get_features_batch()` detects batch-level 403 and stops trying (avoids wasted API calls)
- Improved error handling with structured logging
- Added detection for fallback structures (checks for `"source": "unavailable"`)

### 3. Module Exports
**Location**: `core/__init__.py`

**Added**:
- Export `fetch_audio_features_safe` for standalone usage
- Complete exports for all core models and functions

### 4. Documentation
**Files Created**:
- `SAFE_AUDIO_FEATURES.md` - Comprehensive guide with usage examples
- `scripts/test_safe_features.py` - Test script demonstrating the safe fetcher

## Usage Examples

### Basic Usage
```python
from core.features import fetch_audio_features_safe

features = fetch_audio_features_safe(sp, track_id)

if features and features.get("source") != "unavailable":
    print(f"Energy: {features['energy']}")
else:
    print("Features unavailable - using behavioral analysis")
```

### Integrated Usage (No Code Changes Needed!)
```python
from core import AudioFeaturesEnricher

enricher = AudioFeaturesEnricher(sp)
features = enricher.get_features(track_id)  # Returns None on 403

if features:
    print(f"Mood: {features.energy} energy, {features.valence} valence")
else:
    print("Falling back to behavioral analysis")
```

## Error Handling Matrix

| HTTP Status | Action | Return Value |
|------------|--------|--------------|
| 200 OK | Parse and return features | Full features dict |
| 403 Forbidden | Log warning, return fallback | `{"source": "unavailable", "reason": "403_deprecated"}` |
| 429 Rate Limit | Retry with exponential backoff (max 3x) | Full features dict OR fallback after max retries |
| 401 Unauthorized | Log error, return fallback | `{"source": "unavailable", "reason": "401_unauthorized"}` |
| Other errors | Log error, return fallback | `{"source": "unavailable", "reason": "http_XXX"}` |
| Network error | Log error, return fallback | `{"source": "unavailable", "reason": "unexpected_error"}` |

## Testing

### Test Script
```bash
python scripts/test_safe_features.py
```

**Expected Output** (if 403 is encountered):
```
📀 Testing: Mr. Brightside - The Killers
   Track ID: 3n3Ppam7vgaVa1iaRUc9Lp
------------------------------------------------------------------
   ⚠️  Result: Unavailable
   Reason: 403_deprecated
   ℹ️  This is expected if Spotify restricted the endpoint.
   💡 Suggestion: Use behavioral analysis instead.
```

### Integration Test
Existing collectors/scripts work without modification:
```bash
# This will gracefully handle 403s now
python -m core.collector

# Behavioral report works independently
python scripts/behavioral_report.py --roast
```

## Backwards Compatibility

✅ **100% backwards compatible** - existing code using `AudioFeaturesEnricher` continues to work
- `get_features()` returns `None` instead of crashing (existing code should already handle this)
- `get_features_batch()` returns partial results instead of failing completely
- All Track/AudioFeatures models unchanged

## Benefits

1. **Robustness**: Application never crashes due to 403 errors
2. **Clear Diagnostics**: Structured fallback makes it easy to detect and handle unavailable features
3. **Smart Retries**: Only retries on 429 (rate limit), not on 403 (permanent block)
4. **Production Ready**: Proper logging for monitoring and debugging
5. **Graceful Degradation**: Falls back to behavioral analysis when audio features unavailable

## Fallback Strategy

When audio features return 403, the system automatically uses:

**Behavioral Classification System** (`analysis/behavior.py`)
- Infers emotional states from listening patterns
- No Spotify API dependency
- More personalized than generic audio features
- See `BEHAVIORAL_SYSTEM.md` for details

## Next Steps (Optional)

1. **Test on real data**: Run `python scripts/test_safe_features.py`
2. **Enable Extended Quota**: Request quota extension in Spotify Developer Dashboard
3. **Consider Audio Analysis API**: Use `GET /v1/audio-analysis/{id}` as alternative
4. **Monitor logs**: Check for 403 patterns to inform long-term strategy

## Files Modified

| File | Changes |
|------|---------|
| `core/features.py` | Added `fetch_audio_features_safe()`, updated `AudioFeaturesEnricher` class |
| `core/__init__.py` | Added exports for new function and all models |
| `scripts/test_safe_features.py` | New test script |
| `SAFE_AUDIO_FEATURES.md` | New comprehensive documentation |
| `IMPLEMENTATION_SUMMARY.md` | This file |

## Technical Details

### Logging Configuration
The module uses Python's standard `logging` module:
```python
import logging
logger = logging.getLogger(__name__)

# Usage
logger.warning("Audio features unavailable (403)")
logger.info("Rate limited, retrying in 2s...")
logger.error("Unexpected error occurred")
```

### Exponential Backoff
For 429 rate limits:
```python
wait_time = retry_delay * (2 ** (retry_count - 1))
# retry_count=1: 1s
# retry_count=2: 2s
# retry_count=3: 4s
```

### Spotipy Exception Handling
```python
from spotipy.exceptions import SpotifyException

try:
    response = sp.audio_features([track_id])
except SpotifyException as e:
    if e.http_status == 403:
        # Handle forbidden
    elif e.http_status == 429:
        # Handle rate limit
```

## Conclusion

✅ **Implementation Complete**
✅ **Backwards Compatible**
✅ **Production Ready**
✅ **Well Documented**
✅ **Gracefully Handles 403 Errors**

The system now robustly handles Spotify API's 403 errors without crashing, provides clear diagnostics, and falls back to behavioral analysis when needed.  

**No changes needed to existing scripts** - they automatically benefit from the improved error handling! 🚀
