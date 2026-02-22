import json

with open('final_analysis.json') as f:
    data = json.load(f)

print("SECONDARY BEHAVIOR ANALYSIS (final_analysis.json)\n")
for a in data['analyses']:
    print(f"Session: {a['track_count']} tracks, {a['duration_minutes']:.0f}min")
    print(f"  Primary: {a['predicted_state']} ({a['predicted_confidence']:.0%})")
    print(f"  Secondary: {a['predicted_secondary']}")
    print()

print("SUMMARY:")
total_sessions = len(data['analyses'])
with_secondary = sum(1 for a in data['analyses'] if a['predicted_secondary'])
secondary_freq = with_secondary / total_sessions if total_sessions > 0 else 0
print(f"  Sessions with ANY secondary: {with_secondary}/{total_sessions} ({secondary_freq:.0%})")
print(f"  Current threshold in code: 0.15")
print(f"  Secondary scores range: {[s[1] for a in data['analyses'] for s in a['predicted_secondary']]}")

