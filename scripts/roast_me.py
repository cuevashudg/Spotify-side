"""
Generate a personality-driven report with different tones.

Run: python scripts/roast_me.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.mood import MoodAnalyzer, load_tracks_from_json
from analysis.habits import HabitsAnalyzer
from personality import Narrator, ToneType


def generate_report(tone: ToneType):
    """Generate report with specified tone."""
    
    json_file = "enriched_history.json"
    
    if not os.path.exists(json_file):
        print(f"\n❌ Error: {json_file} not found")
        print("   Run the collector first: python -m core.collector")
        return
    
    # Load data
    print(f"\n📖 Loading listening history...")
    tracks = load_tracks_from_json(json_file)
    
    if not tracks:
        print("\n⚠️  No tracks found. Play some music first!")
        return
    
    print(f"✅ Loaded {len(tracks)} tracks\n")
    
    # Initialize analyzers
    mood = MoodAnalyzer(tracks)
    habits = HabitsAnalyzer(tracks)
    
    # Create narrator with chosen tone
    narrator = Narrator(mood, habits, tone=tone)
    
    # Generate report
    report = narrator.generate_full_report()
    print(report)
    
    # Quick summary
    print("\n📝 Quick Summary:")
    print(narrator.generate_quick_summary())
    print()


def main():
    """Run report with all tones for comparison."""
    
    print("\n🎵 SpotiMood Personality Reports")
    print("=" * 60)
    
    # User can choose tone or see all
    print("\nChoose your narrator:")
    print("  1. 💙 Friend Mode (supportive)")
    print("  2. 📊 Analyst Mode (objective)")
    print("  3. 🔥 Roast Mode (savage) 😈")
    print("  4. Show all three")
    
    choice = input("\nEnter 1-4 (or just press Enter for roast mode): ").strip()
    
    if choice == "1":
        generate_report(ToneType.FRIEND)
    elif choice == "2":
        generate_report(ToneType.ANALYST)
    elif choice == "4":
        print("\n" + "🔥" * 30)
        print("SHOWING ALL TONES FOR COMPARISON")
        print("🔥" * 30)
        
        for tone in [ToneType.FRIEND, ToneType.ANALYST, ToneType.ROAST]:
            generate_report(tone)
            input("\nPress Enter for next tone...")
    else:  # Default to roast mode 😈
        generate_report(ToneType.ROAST)


if __name__ == "__main__":
    main()
