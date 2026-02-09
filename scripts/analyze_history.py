"""
Demo script to test analysis modules on your listening history.

Run: python scripts/analyze_history.py
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.mood import MoodAnalyzer, load_tracks_from_json
from analysis.habits import HabitsAnalyzer


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def analyze_history(json_file: str = "enriched_history.json"):
    """
    Run full analysis on listening history.
    
    Args:
        json_file: Path to enriched history JSON
    """
    print("\n🎵 Spotify Behavioral Analysis Report")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(json_file):
        print(f"\n❌ Error: {json_file} not found")
        print("   Run the collector first: python -m core.collector")
        return
    
    # Load tracks
    print(f"\n📖 Loading tracks from {json_file}...")
    tracks = load_tracks_from_json(json_file)
    
    print(f"✅ Loaded {len(tracks)} tracks")
    
    if not tracks:
        print("\n⚠️  No tracks found. Play some music and try again!")
        return
    
    # === HABITS ANALYSIS ===
    print_section("📊 LISTENING HABITS")
    
    habits = HabitsAnalyzer(tracks)
    
    # Time of day
    hours = habits.get_listening_hours()
    if "error" not in hours:
        print(f"\n🕐 Most Active Hour: {hours['most_active_hour']}:00")
        print(f"   Top 3 hours:")
        for peak in hours['peak_hours']:
            print(f"     {peak['hour']:02d}:00 - {peak['count']} tracks")
    
    # Day of week
    days = habits.get_day_of_week_pattern()
    if "error" not in days:
        print(f"\n📅 Most Active Day: {days['most_active_day']}")
        print(f"   Weekend Listener: {'Yes' if days['is_weekend_listener'] else 'No'}")
    
    # Session patterns
    sessions = habits.get_session_patterns()
    if "error" not in sessions:
        print(f"\n🎧 Listening Sessions:")
        print(f"   Total sessions: {sessions['total_sessions']}")
        print(f"   Avg tracks/session: {sessions['avg_tracks_per_session']}")
        print(f"   Avg session duration: {sessions['avg_session_duration_min']} min")
        print(f"   Total listening time: {sessions['total_listening_time_hours']} hours")
    
    # Top artists
    print(f"\n⭐ Top Artists:")
    top_artists = habits.get_top_artists(limit=5)
    for i, artist in enumerate(top_artists, 1):
        print(f"   {i}. {artist['artist']} - {artist['play_count']} plays ({artist['percentage']}%)")
    
    # Repeat behavior
    repeats = habits.get_repeat_behavior()
    print(f"\n🔁 Repeat Behavior:")
    print(f"   Unique tracks: {repeats['total_unique_tracks']}")
    print(f"   Repeated tracks: {repeats['repeated_tracks']} ({repeats['repeat_percentage']}%)")
    print(f"   Diversity score: {repeats['diversity_score']}")
    
    if repeats.get('most_repeated'):
        print(f"\n   Most repeated:")
        for track in repeats['most_repeated'][:3]:
            print(f"     • {track['song']} by {track['artist']} - {track['play_count']}x")
    
    # Streaks
    streaks = habits.get_listening_streaks()
    if "error" not in streaks:
        print(f"\n🔥 Listening Streaks:")
        print(f"   Longest streak: {streaks['longest_streak']} days")
        print(f"   Current streak: {streaks['current_streak']} days")
        print(f"   Total listening days: {streaks['total_listening_days']}")
    
    # === MOOD ANALYSIS ===
    print_section("😊 MOOD ANALYSIS")
    
    mood_analyzer = MoodAnalyzer(tracks)
    
    overall = mood_analyzer.get_overall_mood()
    
    if "error" in overall:
        print(f"\n⚠️  {overall['error']}")
        print("   Audio features are needed for mood analysis.")
        print("   Fix the 403 error and re-run the collector.")
    else:
        print(f"\n{overall['emoji']} Overall Mood: {overall['mood_label']}")
        print(f"   Energy: {overall['avg_energy']:.2f} (σ={overall['energy_std']:.2f})")
        print(f"   Valence: {overall['avg_valence']:.2f} (σ={overall['valence_std']:.2f})")
        print(f"   Tempo: {overall['avg_tempo']:.1f} BPM")
        print(f"   Tracks analyzed: {overall['tracks_analyzed']}/{overall['total_tracks']}")
        
        # Mood extremes
        extremes = mood_analyzer.get_mood_extremes()
        if extremes:
            print(f"\n🎯 Mood Extremes:")
            print(f"   🔥 Highest Energy: {extremes['highest_energy']['song']} ({extremes['highest_energy']['energy']})")
            print(f"   😴 Lowest Energy: {extremes['lowest_energy']['song']} ({extremes['lowest_energy']['energy']})")
            print(f"   😄 Happiest: {extremes['happiest']['song']} ({extremes['happiest']['valence']})")
            print(f"   😢 Saddest: {extremes['saddest']['song']} ({extremes['saddest']['valence']})")
        
        # Mood shifts
        shifts = mood_analyzer.detect_mood_shifts()
        if shifts:
            print(f"\n🌀 Detected {len(shifts)} mood shifts")
            print(f"   Most recent shifts:")
            for shift in shifts[-3:]:
                print(f"     • {shift['before_mood']} → {shift['after_mood']}")
                print(f"       {shift['track']} ({shift['shift_type']})")
    
    # === SUMMARY ===
    print_section("✨ SUMMARY")
    
    print(f"\n   Total tracks analyzed: {len(tracks)}")
    print(f"   Time period: {tracks[0].timestamp.date()} to {tracks[-1].timestamp.date()}")
    
    if overall.get('tracks_analyzed', 0) == 0:
        print(f"\n   ⚠️  Audio features missing - Fix Spotify API permissions!")
        print(f"   Run: python scripts/enrich_history.py (after fixing 403 error)")
    
    print("\n" + "=" * 60)
    print("🎵 Analysis complete! Keep tracking to see more patterns.\n")


if __name__ == "__main__":
    analyze_history()
