# 🎵 Spotify Behavioral Engine

A psychological mood tracking system for Spotify that analyzes your listening behavior to understand your emotional patterns, preferences, and habits.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Spotify API Credentials

Create a `.env` file in this directory:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

Get your credentials from: https://developer.spotify.com/dashboard

### 3. Start Collecting Data

#### Option A: New Enhanced Collector (Recommended)
```bash
python -m core.collector
```

Features:
- ✅ Real-time playback monitoring
- ✅ Audio features enrichment (energy, valence, tempo)
- ✅ Mood analysis
- ✅ Session tracking
- ✅ Skip detection

#### Option B: Legacy Collector
```bash
python spotiloader.py
```

Basic features only (backward compatible).

### 4. Enrich Existing History

If you have existing `song_history.csv` data:

```bash
python scripts/enrich_history.py
```

This fetches audio features for all your historical tracks.

---

## 📁 Project Structure

```
spotify-behavioral-engine/
├── core/                   # Core collection & enrichment
│   ├── collector.py       # Enhanced playback logger
│   ├── features.py        # Audio features API
│   ├── sessions.py        # Session detection
│   └── models.py          # Typed data models
│
├── analysis/              # Analysis modules (Phase 2)
│   ├── mood.py           # Energy/valence trends
│   ├── skips.py          # Skip psychology
│   ├── habits.py         # Time-of-day patterns
│   └── anomalies.py      # Weird behavior detection
│
├── personality/           # Personality engine (Phase 3)
│   ├── narrator.py       # Metrics → commentary
│   └── tone.py           # Voice control
│
├── api/                   # FastAPI endpoints (Phase 4)
│   └── main.py
│
├── scripts/               # Utilities
│   └── enrich_history.py # Migrate old data
│
├── spotiloader.py         # Legacy collector
├── requirements.txt       # Dependencies
└── README.md             # This file
```

---

## 🎯 Audio Features Explained

Spotify provides psychological dimensions for every track:

| Feature | Range | Meaning |
|---------|-------|---------|
| **Energy** | 0.0-1.0 | Intensity & activity (0=calm, 1=intense) |
| **Valence** | 0.0-1.0 | Musical positivity (0=sad, 1=happy) |
| **Danceability** | 0.0-1.0 | How suitable for dancing |
| **Tempo** | BPM | Beats per minute |
| **Acousticness** | 0.0-1.0 | Confidence track is acoustic |
| **Speechiness** | 0.0-1.0 | Presence of spoken words |
| **Loudness** | dB | Average loudness |

### Mood Classification

Energy + Valence = Mood Quadrants:

- **High Energy + High Valence** → 🔥😄 Energetic & Happy
- **High Energy + Low Valence** → ⚡😤 Intense & Aggressive  
- **Low Energy + High Valence** → 🌙😌 Calm & Peaceful
- **Low Energy + Low Valence** → 🌧️😢 Melancholic & Low

---

## 📊 Output Files

### `current_song.txt`
Current/last played track (overwritten each time).

### `song_history.txt`
Human-readable chronological log.

### `song_history.csv`
Legacy CSV format (timestamp, song, artist, album, track_id, duration).

### `enriched_history.json`
**Full enriched data** with:
- All basic metadata
- Audio features (energy, valence, etc.)
- Playback context (playlist, shuffle state)
- Session IDs

---

## 🔮 Roadmap

### ✅ Phase 1: Foundation (COMPLETE)
- Core data models
- Audio features enrichment
- Refactored collector
- Session detection

### 🚧 Phase 2: Analysis Modules (Next)
- Mood trends over time
- Skip psychology
- Time-of-day habits
- Anomaly detection

### 🔜 Phase 3: Personality Engine
- Natural language narrator
- Configurable tone (friend/therapist/roast)
- Weekly/monthly reports

### 🔜 Phase 4: API & UI
- FastAPI endpoints
- Web dashboard
- Real-time mood visualization

---

## 🤖 Advanced Usage

### Session Detection

Sessions are automatically detected with 30-minute gaps:

```python
from core.sessions import SessionDetector
from core.models import Track

detector = SessionDetector(gap_threshold_minutes=30)

for track in tracks:
    completed_session = detector.process_track(track)
    if completed_session:
        print(f"Session ended: {completed_session.total_tracks} tracks")
```

### Manual Feature Fetching

```python
from core.features import AudioFeaturesEnricher
import spotipy

sp = spotipy.Spotify(auth_manager=...)
enricher = AudioFeaturesEnricher(sp)

# Single track
features = enricher.get_features("track_id_here")
print(f"Energy: {features.energy}, Valence: {features.valence}")

# Batch (up to 50 tracks)
features_map = enricher.get_features_batch(["id1", "id2", ...])
```

---

## 🙋 FAQ

**Q: Why does it ask for authentication?**  
A: Spotify requires OAuth for API access. Your credentials stay local.

**Q: Does this work with Spotify Free?**  
A: Yes! Playback monitoring works on Free and Premium.

**Q: How much API quota does this use?**  
A: Minimal. ~1 request every 5 seconds for playback, plus audio features fetches (100 tracks per request).

**Q: Can I use this with other music apps?**  
A: Not currently. This is Spotify-specific due to their API.

---

## 📝 License

MIT License - do whatever you want with it!

---

## 🤝 Contributing

This is a personal project, but feel free to:
- Fork and extend
- Report bugs
- Suggest features

---

**Made with ☕ and 🎵**
