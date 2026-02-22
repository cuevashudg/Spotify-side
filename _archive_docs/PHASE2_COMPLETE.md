# 🎵 SpotiMood - Phase 2 Complete!

## ✅ What's New in Phase 2

### Analysis Modules

1. **[analysis/mood.py](analysis/mood.py)** - Mood Trend Analysis
   - Overall mood statistics
   - Mood by hour/day
   - Mood shift detection
   - Emotional extremes

2. **[analysis/habits.py](analysis/habits.py)** - Listening Habits
   - Most active times
   - Day of week patterns
   - Top artists
   - Listening streaks
   - Session patterns
   - Repeat behavior

### 🚀 Try It Now

Run the analysis on your current data:

```powershell
python scripts/analyze_history.py
```

This generates a full behavioral report including:
- 📊 Listening habits (peak hours, top artists, streaks)
- 😊 Mood analysis (if audio features work)
- 🔥 Session statistics

---

## Sample Output

```
🎵 Spotify Behavioral Analysis Report
================================================================

📊 LISTENING HABITS
================================================================

🕐 Most Active Hour: 18:00
   Top 3 hours:
     18:00 - 45 tracks
     15:00 - 32 tracks
     20:00 - 28 tracks

📅 Most Active Day: Saturday
   Weekend Listener: Yes

🎧 Listening Sessions:
   Total sessions: 12
   Avg tracks/session: 8.5
   Avg session duration: 34.2 min
   Total listening time: 6.8 hours

⭐ Top Artists:
   1. Post Malone - 23 plays (11.5%)
   2. Billie Eilish - 18 plays (9.0%)
   3. The Weeknd - 15 plays (7.5%)

🔁 Repeat Behavior:
   Unique tracks: 156
   Repeated tracks: 42 (26.9%)
   Diversity score: 0.78

🔥 Listening Streaks:
   Longest streak: 7 days
   Current streak: 3 days
```

---

## ⚠️ Known Issue: Audio Features 403 Error

Your collector is working but audio features aren't loading (HTTP 403).

### Fix:

1. Go to https://developer.spotify.com/dashboard
2. Click your app
3. **Settings** → Check **Redirect URI**: `http://127.0.0.1:8888/callback`
4. Delete cache: `Remove-Item .cache* -Force`
5. Restart: `python -m core.collector`
6. Re-authenticate when browser opens

Once fixed, you'll see mood emojis:
```
🔥😄 Mood: Energetic & Happy
   Energy: 0.78, Valence: 0.65, Tempo: 128.0 BPM
✅ Logged: Song Name by Artist
```

---

## 📁 Current Structure

```
spotimood/
├── core/                       ✅ Phase 1
│   ├── collector.py           # Enhanced logger  
│   ├── features.py            # Audio features
│   ├── sessions.py            # Session detection
│   └── models.py              # Data models
│
├── analysis/                   ✅ Phase 2
│   ├── mood.py                # Mood trends
│   └── habits.py              # Listening patterns
│
├── scripts/
│   ├── enrich_history.py      # Migrate old data
│   └── analyze_history.py     # Generate report ⭐NEW
│
├── personality/                🔜 Phase 3
│   ├── narrator.py            # Natural language insights
│   └── tone.py                # Voice control
│
└── api/                        🔜 Phase 4
    └── main.py                # FastAPI endpoints
```

---

## 🔮 What's Next

### Phase 3: Personality Engine (Coming Soon)
- Natural language narrator
- Weekly/monthly reports
- Configurable tone (friend mode / therapist mode / roast mode 😈)

### Phase 4: API & Dashboard
- FastAPI endpoints
- Real-time mood visualization
- Web dashboard

---

## 📝 Quick Commands

```powershell
# Start collector (tracks songs + mood)
python -m core.collector

# Analyze your history
python scripts/analyze_history.py

# Enrich old CSV data (after fixing 403)
python scripts/enrich_history.py
```

---

**Phase 2 Status: ✅ Complete**

Test it out and let me know when you're ready for Phase 3! 🚀
