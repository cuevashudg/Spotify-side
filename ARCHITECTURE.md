# Spotimood Signal-Based Behavioral Inference Architecture

> **Goal**: Personal behavioral classification from listening patterns, not metadata.  
> **Approach**: Weighted scoring system with competing behavioral signals.  
> **Key Benefit**: Explainable, extensible, and API-independent.

---

## System Overview

The behavioral inference engine classifies listening behavior into emotional/contextual states **without relying on Spotify audio features** (energy, valence, etc.). Instead, it observes **how you listen** and infers **why**.

### Core Philosophy

Instead of analyzing track metadata:
- ❌ "This song has high valence, so you're energized"
- ✅ "You're listening at 2am, replaying songs, so you're ruminating"

---

## Architecture Components

### 1. **BehaviorSignal** (Abstract Base Class)

```python
class BehaviorSignal(ABC):
    @abstractmethod
    def evaluate(session, baseline, all_tracks) -> Dict[str, Tuple[float, List[str]]]:
        """Score multiple competing behaviors for a session."""
```

**Key Design**:
- Each signal independently evaluates one session
- Returns **multiple behaviors** (not just one), allowing competition
- Each behavior gets a score (0.0-1.0) and evidence list
- No early returns; all signals contribute equally

**Implementation Pattern**:
```python
class MyNewSignal(BehaviorSignal):
    def evaluate(self, session, baseline, all_tracks):
        return {
            "primary_behavior": (0.75, ["Evidence A", "Evidence B"]),
            "secondary_behavior": (0.45, ["Evidence C"])
        }
```

### 2. **Concrete Signals** (Current Implementation)

#### **LateNightSignal**
- **Triggers**: Listening between 22:00-03:00
- **Scores**: `ruminating` behavior
- **Evidence**: Time of day + replay rate vs baseline
- **Intensity Driver**: Late-night sessions with high replay

#### **ReplaySignal**
- **Triggers**: Replay rate elevated vs baseline
- **Scores**: `comfort_seeking` (primary) + `routine_driven` (competing)
- **Evidence**: Replay percentage deviance from historical average
- **Intensity Driver**: How much above baseline replay

#### **SessionLengthSignal**
- **Triggers**: Session duration patterns
- **Scores**: `focused` (60-90 min), `zoning_out` (90+ min), `routine_driven` (competing)
- **Evidence**: Session duration + context switches + replay rate
- **Intensity Driver**: Duration and context stability

#### **ContextSwitchSignal**
- **Triggers**: High context switching (playlist changes)
- **Scores**: `searching` behavior
- **Evidence**: Number of unique playlists/albums switched
- **Intensity Driver**: Context switch frequency

### 3. **BehaviorBaseline**

Defines statistical norms for a listener across their history:

```python
@dataclass
class BehaviorBaseline:
    avg_session_length_minutes: float      # Average listening duration
    avg_replay_rate: float                 # Typical replay percentage
    avg_listening_hour: float              # Average hour of day (0-24)
    avg_context_switches: float            # Avg playlist changes per session
    typical_session_tracks: float          # Avg tracks per session
```

**Computation**: Extracted once at classifier initialization from all historical sessions. Used by signals for **relative scoring** (deviation detection).

### 4. **ListeningSession** (Data Structure)

```python
class ListeningSession:
    session_id: str
    tracks: List[Track]                    # Track objects directly
    all_tracks_history: List[Track]        # For replay detection
    
    # Computed Properties:
    duration_minutes: float                # Total session length
    avg_hour: float                        # Average listen time
    replay_rate: float                     # % of tracks played before
    context_switches: int                  # Unique playlists/albums
    start_time: datetime
    end_time: datetime
```

**Design Note**: Lightweight dataclass focused on signal evaluation. Stores Track objects for efficient analysis.

### 5. **BehaviorClassifier** (Orchestrator)

```python
class BehaviorClassifier:
    def __init__(self, all_tracks: List[Track]):
        # Group tracks into sessions
        # Compute baseline from historical behavior
        # Initialize all signals
    
    def classify_session(session_tracks) -> BehaviorState:
        # Run all signals
        # Accumulate scores (no early returns)
        # Select dominant behavior + secondary behaviors
        # Compute intensity
        
    def classify_overall() -> BehaviorState:
        # Classify all sessions
        # Aggregate states
        # Return dominant overall state with secondaries
```

**Weighted Scoring Process**:
1. Create `ListeningSession` object from track list
2. For each signal: call `evaluate(session, baseline, all_tracks)`
3. Accumulate scores for each behavior (average if multiple signals score it)
4. Select **top 3 behaviors**:
   - **Primary**: Highest score
   - **Secondary**: #2 and #3 scores (if > 30% confidence)
5. Compute intensity (behavior-specific calculation)
6. Return `BehaviorState` with all results

### 6. **BehaviorState** (Output)

```python
@dataclass
class BehaviorState:
    state: str                             # Primary behavior (e.g., "ruminating")
    confidence: float                      # 0.0-1.0 for primary (max signal score)
    evidence: List[str]                    # Why this classification
    intensity: float                       # 0.0-1.0 how intense
    secondary_behaviors: List[Tuple[str, float]]  # [(behavior, score), ...]
```

**Example Output**:
```
state: "comfort_seeking"
confidence: 0.68
intensity: 0.50
secondary_behaviors: [("routine_driven", 0.52)]
evidence: [
    "Elevated replay rate: 50% (baseline: 31%)",
    "Secondary: routine_driven (52%)"
]
```

---

## Backward Compatibility Methods

For integration with existing roast engine and report generation:

- `detect_behavioral_events()` → Returns event dicts for roast mode
- `get_intensity_score()` → Overall listening intensity (0.0-1.0)
- `get_deviation_score(recent_tracks)` → Behavioral change detection

These methods delegate to the new signal-based system internally.

---

## How to Extend the System

### Adding a New Signal

1. **Create signal class**:
```python
class MySignal(BehaviorSignal):
    def evaluate(self, session, baseline, all_tracks):
        # Compute scores
        score = ...  # 0.0-1.0
        evidence = [...]
        
        return {
            "behavior_name": (score, evidence),
            # optionally add competing behaviors:
            "other_behavior": (lower_score, ["evidence"])
        }
```

2. **Register in BehaviorClassifier**:
```python
# In __init__:
self.signals: List[BehaviorSignal] = [
    LateNightSignal(),
    ReplaySignal(),
    SessionLengthSignal(),
    ContextSwitchSignal(),
    MySignal(),  # ← Add here
]
```

3. **Test**:
```python
bc = BehaviorClassifier(tracks)
state = bc.classify_session(some_tracks)
print(state.secondary_behaviors)  # Should include your behavior
```

### Signal Design Best Practices

- **Avoid early returns**: Score all behaviors, let them compete
- **Relative scoring**: Compare to `baseline`, not fixed thresholds
- **Clear evidence**: 1-2 human-readable strings explaining the score
- **Handle edge cases**: Empty sessions, no history, single track
- **Score range**: Keep between 0.0-1.0 for normalization

---

## Session Grouping

Sessions are detected via time gaps:

```python
def _group_into_sessions(self, tracks, gap_minutes=30):
    """Group tracks into sessions based on 30-min gaps."""
    # If 30+ minutes between plays → new session
```

This is automatic; users don't need to manage it.

---

## Behavioral States

Current implemented behaviors:

| State | Triggered By | Meaning |
|-------|--------------|---------|
| `ruminating` | Late night + replay | Obsessive looping, insomnia |
| `comfort_seeking` | High replay | Familiar music, security blanket |
| `searching` | High context switches | Indecisive, looking for something |
| `focused` | 60-90 min, low switches | Deep listening, immersion |
| `zoning_out` | 90+ minute session | Passive background listening |
| `casual` | Standard patterns | Normal, routine consumption |
| `routine_driven` | Consistent behavior | Habitual, predictable |

**Overall States** (aggregated from sessions):
- `chronic_ruminator`, `comfort_oriented`, `restless_searcher`, `focused_listener`, `passive_listener`, `routine_driven`, `eclectic`

---

## Integration Points

### With Roast Engine
- `BehaviorClassifier.detect_behavioral_events()` → Event dicts
- Each event has `type`, `timestamp`, and contextual data
- RoastEngine selects roasts based on event types

### With Narrator
- `BehaviorState.state` and `intensity` → Tone selection
- `evidence` list → Story generation
- `secondary_behaviors` → Nuanced personality details

### With Analysis Modules
- `HabitsAnalyzer` for top artists, listening patterns
- `MoodAnalyzer` for energy/valence (when features available)
- Behavioral signals for emotional/contextual classification

---

## Performance Considerations

- **Baseline computation**: O(n) once per initialization
- **Session grouping**: O(n log n) for sorting
- **Signal evaluation**: O(m × s) where m=sessions, s=signals
- **Overall**: Linear in track history, very efficient

---

## Data Flow Diagram

```
Track History (enriched_history.json)
         ↓
[BehaviorClassifier.__init__]
         ↓
    ┌────┴────┐
    ↓         ↓
Sessions  Baseline (avg_*, typical_*)
    ↓         ↓
    └────┬────┘
         ↓
   [classify_session]
         ↓
    ┌────┴────────────────┬────────────┐
    ↓                     ↓            ↓
LateNightSignal    ReplaySignal  SessionLengthSignal  ContextSwitchSignal
    ↓                     ↓            ↓                     ↓
[evaluate(session, baseline)]  ← all compete for scores
    ↓                     ↓            ↓                     ↓
behavior_scores (accumulated from all signals)
         ↓
  [sort by score]
         ↓
    Top 3 behaviors (primary + secondaries)
         ↓
   [BehaviorState]
         ↓
    ┌────┴────┬──────────┐
    ↓         ↓          ↓
  state   confidence  secondary_behaviors
```

---

## Examples

### Session Classification
```python
from analysis import BehaviorClassifier, load_tracks_from_json

tracks = load_tracks_from_json("enriched_history.json")
classifier = BehaviorClassifier(tracks)

# Classify a single session
session_tracks = tracks[10:25]
state = classifier.classify_session(session_tracks)

print(f"Primary: {state.state} ({state.confidence:.0%})")
print(f"Secondary: {state.secondary_behaviors}")
print(f"Intensity: {state.intensity:.2f}/1.0")
print(f"Why: {state.evidence}")
```

### Overall Classification
```python
overall = classifier.classify_overall()
print(f"You're a {overall.state}")
print(f"Supporting behaviors: {overall.secondary_behaviors}")
```

### Roast Integration
```python
events = classifier.detect_behavioral_events()
from personality import RoastEngine

for event in events:
    roast = RoastEngine.roast_event(event)
    print(roast)
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| All sessions return `casual` | No signals firing | Check baseline computation; signals may have too-high thresholds |
| Secondary behaviors empty | Single signal per session | Add signals that return multiple behaviors; encourage competition |
| Confidence always low | Too many competing scores | Adjust signal weighting; increase primary behavior scores |
| Intensity always 0.5 | `_compute_intensity()` not differentiating | Customize intensity calculation per behavior |

---

## Future Enhancements

Proposed signals to implement:

- **ShuffleStateSignal**: Detects comfort vs exploration (shuffle on/off)
- **SkipRateSignal**: High skips → "searching" behavior
- **ArtistDiversitySignal**: Musical taste breadth
- **ConcernSignal**: Deviation spikes → anomaly detection
- **TimeOfDayPatternsSignal**: Multi-day listening cycles
- **BingeVsGrazeSignal**: Long vs short sessions

---

## References

- **Code**: `analysis/behavior_signals.py`
- **Usage**: `scripts/analyze.py`
- **Tests**: See `test_secondary.py` for examples
- **Related**: `personality/roast_engine.py`, `personality/narrator.py`

