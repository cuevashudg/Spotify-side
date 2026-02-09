# 🎵 Quick Start Guide - Spotify Behavioral Engine

## Installation (5 minutes)

### Step 1: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Test the new collector
```bash
python -m core.collector
```

This will:
1. Launch Spotify authentication in browser
2. Start monitoring your playback
3. Fetch audio features for each track
4. Save enriched data to `enriched_history.json`

### Step 3: (Optional) Enrich existing history
If you have old data in `song_history.csv`:
```bash
python scripts/enrich_history.py
```

---

## What You Get

### Before (spotiloader.py):
```csv
timestamp,song_name,artist,album,track_id,duration_ms
2026-01-20 15:01:07,Be Right There,Diplo,Be Right There,5wZZR...,232116
```

### After (core.collector):
```json
{
  "timestamp": "2026-01-20T15:01:07",
  "song_name": "Be Right There - Sleepy Tom's Decade Mix",
  "artist": "Diplo",
  "audio_features": {
    "energy": 0.78,
    "valence": 0.65,
    "danceability": 0.72,
    "tempo": 128.0
  },
  "context_type": "playlist",
  "session_id": "2026-01-20_15-01"
}
```

**Plus mood analysis in console:**
```
🔥😄 Mood: Energetic & Happy
✅ Logged: Be Right There by Diplo
```

---

## Next Steps

### Phase 2: Add Analysis Modules
Create `analysis/mood.py` to track:
- Daily energy patterns
- Mood shifts during sessions
- Correlation between valence and skips

### Phase 3: Build Personality Narrator
Create `personality/narrator.py` to generate:
- Weekly listening reports
- Commentary on your music taste
- Personalized insights

### Phase 4: Deploy API
Launch FastAPI endpoints for:
- Real-time mood dashboard
- Historical trend visualization
- Webhook notifications

---

## Troubleshooting

**"Module not found" error:**
```bash
# Make sure you're in the Spotify-side directory
cd "c:\Users\losve\OneDrive\Documents\programming stuff\SpotifyMood\Spotify-side"
pip install -r requirements.txt
```

**Authentication issues:**
- Check your `.env` file has correct credentials
- Delete `.cache` files and try again
- Make sure redirect URI is: `http://127.0.0.1:8888/callback`

**No audio features:**
- Some tracks don't have features (podcasts, local files)
- This is normal - features are fetched when available

---

## File Structure After Phase 1

```
Spotify-side/
├── core/                        ← NEW
│   ├── __init__.py
│   ├── collector.py            # Enhanced logger
│   ├── features.py             # Audio features API
│   ├── sessions.py             # Session detection
│   └── models.py               # Data models
│
├── scripts/                     ← NEW
│   ├── __init__.py
│   └── enrich_history.py       # Migration tool
│
├── analysis/                    ← NEW (empty, for Phase 2)
├── personality/                 ← NEW (empty, for Phase 3)
├── api/                         ← NEW (empty, for Phase 4)
│
├── spotiloader.py              # Original logger (still works)
├── requirements.txt            # Updated with new deps
├── song_history.csv            # Legacy format
├── enriched_history.json       ← NEW (enriched data)
└── BEHAVIORAL_ENGINE_README.md ← NEW (full docs)
```

---

**You're ready to go! 🚀**

Run: `python -m core.collector` and start collecting mood data.
