# Spotimood - Spotify Behavioral Mood Engine

A Python application that monitors your Spotify playback in real-time, classifies your listening behavior, and generates personalized, roast-mode commentary. Unlike traditional feature-based analysis, **Spotimood uses behavioral inference** to understand your emotional state and listening patterns.

## Why Spotimood? 🎵

- **No API Limitations**: Works even when Spotify's audio-features endpoint returns 403 errors
- **Behavioral Insights**: Analyzes replay patterns, time-of-day listening, shuffle/repeat behavior
- **Personality-Driven**: Natural language narrator with friend, analyst, and roast modes
- **Production-Ready**: Safe error handling, comprehensive logging, modular architecture
- **Interview-Worthy**: Demonstrates technical depth in API integration, behavioral analysis, event-driven design

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd spotimood

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Spotify Developer App

1. Visit https://developer.spotify.com/dashboard
2. Create a new app and accept terms
3. Copy **Client ID** and **Client Secret**
4. Set Redirect URI to `http://127.0.0.1:8888/callback`

### 3. Configure Environment

Create `.env` in project root:
```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

### 4. Start Monitoring

```bash
# Launch Spotify first, then:
python -m core.collector

# Or with feature enrichment disabled (if 403 errors):
python -m core.collector --no-features
```

The collector will:
- ✅ Detect Spotify playback
- ✅ Log songs to `enriched_history.json`
- ✅ Track listening sessions and patterns
- ✅ Generate mood/behavior analysis

## Key Features

### 🧠 Behavioral Classification
Infers emotional states from listening patterns without API features:
- **Ruminating**: Replaying the same track repeatedly
- **Comfort Seeking**: Playing familiar songs from favorite artists
- **Searching**: Diverse songs in shuffle mode, frequent skips
- **Focused**: Extended listening sessions with minimal distractions
- **Zoning Out**: Long sessions with familiar content

See [BEHAVIORAL_SYSTEM.md](BEHAVIORAL_SYSTEM.md) for full details.

### 🎤 Roast Mode
Event-driven commentary on your listening habits:
- Late night replays: *"It's 2 AM and you're still on track 3... we get it, it slaps."*
- Skip sprees: *"You skipped 5 songs in a row. Picky mood today?"*
- Comfort loops: *"Playing the same artist again? Loyalty or desperation?"*
- Binge sessions: *"4+ hours straight. That's not a playlist, that's a lifestyle."*

See [BEHAVIORAL_ENGINE_README.md](BEHAVIORAL_ENGINE_README.md) for examples.

### 🛡️ Safe Audio Features (HTTP 403 Handling)
Robust fallback when Spotify's audio-features endpoint is unavailable:
```python
from core.features import fetch_audio_features_safe

# Returns None instead of crashing on 403
features = fetch_audio_features_safe(sp, track_id)

if features:
    print(f"Energy: {features['energy']}")
else:
    print("Using behavioral analysis instead")
```

See [SAFE_AUDIO_FEATURES.md](SAFE_AUDIO_FEATURES.md) for technical details.

## Project Structure

```
spotimood/
├── core/                      # Data collection & enrichment
│   ├── models.py             # Track, AudioFeatures, ListeningSession
│   ├── collector.py          # Real-time playback logger
│   ├── features.py           # Safe audio features fetching
│   └── sessions.py           # Session detection (30-min gaps)
│
├── analysis/                 # Behavioral & pattern analysis
│   ├── behavior.py           # BehaviorClassifier (API-independent)
│   ├── habits.py             # Time patterns, artists, streaks
│   └── mood.py               # Energy/valence mood scoring
│
├── personality/              # Natural language generation
│   ├── narrator.py           # Tone-based reporting
│   ├── roast_engine.py       # Event-driven commentary
│   └── tone.py               # FRIEND, ANALYST, ROAST modes
│
├── scripts/                  # CLI tools
│   ├── behavioral_report.py  # Generate analysis with optional roast
│   ├── analyze_history.py    # Detailed analysis
│   ├── weekly_report.py      # Weekly summary
│   ├── roast_me.py           # Personality-driven report
│   └── test_safe_features.py # Test audio features fetcher
│
└── api/                      # Future API endpoints
```

## Usage Examples

### Generate Behavioral Report

```bash
# Standard report
python scripts/behavioral_report.py

# With roast mode commentary
python scripts/behavioral_report.py --roast
```

Output:
```
🎵 BEHAVIORAL ANALYSIS REPORT
═══════════════════════════════════════════════════════════════

EMOTIONAL STATE
  Primary: Comfort Seeking (78% confidence)
  Confidence: 0.78
  Indicators: ['high_replay_rate', 'favorite_artist', 'evening_listening']
  
🎤 ROAST ALERT 🎤
  "Playing the same artist again? That's not a vibe check, that's a security blanket."

HABITS
  Top Artist: The Weeknd (8 plays)
  Favorite Time: Evening (17:00-23:00)
  ...
```

### Analyze Listening History

```bash
python scripts/analyze_history.py
```

### Weekly Summary Report

```bash
python scripts/weekly_report.py
```

## Documentation

| Document | Purpose |
|----------|---------|
| [BEHAVIORAL_SYSTEM.md](BEHAVIORAL_SYSTEM.md) | How behavioral classification works without audio features |
| [SAFE_AUDIO_FEATURES.md](SAFE_AUDIO_FEATURES.md) | Handling Spotify's 403 errors gracefully |
| [BEHAVIORAL_ENGINE_README.md](BEHAVIORAL_ENGINE_README.md) | Roast mode and event-driven commentary |
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup guide |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Technical implementation details |

## Troubleshooting

### 403 Error on Audio Features

**What**: `spotipy.exceptions.SpotifyException: http status: 403`

**Why**: Spotify's audio-features endpoint is restricted for new/development apps

**Solution**: Use behavioral analysis instead (no API dependency)
- Set `enrich_features=False` in collector
- Or just run `behavioral_report.py` - it works independently

See [SAFE_AUDIO_FEATURES.md](SAFE_AUDIO_FEATURES.md#resolving-403-errors-long-term) for long-term fix.

### Spotify Not Detected

1. Launch Spotify first (desktop app required)
2. Check if Spotify is running (look for `Spotify.exe` in Task Manager)
3. Script will auto-connect within 5 seconds

### Authorization Error

1. Verify `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in `.env`
2. Confirm Redirect URI matches exactly: `http://127.0.0.1:8888/callback`
3. Delete `.cache` file and try again (forces re-authorization)

### No Output Files

- Check that `enriched_history.json` is being created in the project directory
- Verify Spotify is actually playing songs (not just open)
- Check collector logs for errors

## Performance Notes

- **Polling Interval**: 5 seconds (configurable)
- **Cache**: In-memory feature cache reduces API calls
- **Session Detection**: 30-minute gaps between listening sessions
- **Rate Limiting**: Respects Spotify's 429 errors with exponential backoff

## Architecture Highlights

### Modular Design
- **core/**: Handles data collection, isolated from analysis
- **analysis/**: Works with collected data independently
- **personality/**: Generates insights and commentary
- No circular dependencies

### Error Handling
- Graceful degradation on API failures
- Fallback structures for unavailable data
- No hard crashes on 403/429 errors
- Comprehensive logging

### Behavioral > Features
- Doesn't depend on audio-features API
- More personalized (based on YOUR listening)
- Event-driven for contextual insights
- More robust and interview-worthy

## Development

### Running Tests

```bash
# Test safe audio features fetcher
python scripts/test_safe_features.py

# Run with real data
python scripts/behavioral_report.py --roast
```

### Git Branches

- `main`: Stable releases
- `behavioral-mood-system`: Behavioral classification
- `song-analysis-improvements`: Current development

## Requirements

- Python 3.8+
- Spotify Desktop App (required for real-time monitoring)
- Spotify Free/Premium account
- Dependencies: See [requirements.txt](requirements.txt)

## License

Free to use and modify for personal projects.

## Coming Soon

- 🚀 Web dashboard for listening analytics
- 📊 Audio analysis endpoint integration
- 🎯 Playlist generation based on detected mood
- 🤖 LLM-powered personality enhancement

---

**Enjoy your personalized Spotify behavioral insights!** 🎵🧠