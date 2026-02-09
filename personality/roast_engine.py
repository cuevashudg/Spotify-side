"""
Event-driven roast engine - Multiple triggers, randomized savage commentary.

Triggered by behavioral events, not just statistics.
Makes roasts feel observed, not generated.
"""

import random
from typing import Dict, List


class RoastEngine:
    """
    Generate contextual roasts based on behavioral events.
    
    Each event type has multiple possible roasts for variety.
    """
    
    # Roast templates by event type
    ROASTS = {
        "late_night_replay": [
            lambda e: f"You played '{e['track']}' {e['count']} times at {e['hour']}am. That's a choice.",
            lambda e: f"{e['hour']}am and you're on replay #{e['count']}. Who hurt you?",
            lambda e: f"'{e['track']}' hit different at {e['hour']}am, huh? {e['count']} times tho?",
            lambda e: f"Bro it's {e['hour']} in the morning. {e['count']} replays. We've all been there but DAMN.",
            lambda e: f"The sun ain't even up and you've played this {e['count']} times. Therapy might be cheaper than Spotify Premium.",
        ],
        
        "skip_spree": [
            lambda e: f"You skipped {e['switches']} times in one session. The problem isn't the music, bestie.",
            lambda e: f"{e['switches']} skips. You good? Nothing's gonna hit when you're THIS indecisive.",
            lambda e: f"Changed context {e['switches']} times. Pick a vibe and commit. Damn.",
            lambda e: f"Skipped {e['switches']} tracks. Maybe the issue is... you? Just saying.",
            lambda e: f"{e['switches']} context switches. You have the attention span of a TikTok comment section.",
        ],
        
        "comfort_loop": [
            lambda e: f"Shuffle off. Repeat on. {e['duration_min']:.0f} minutes. We've seen this movie.",
            lambda e: f"Repeat mode for {e['duration_min']:.0f} minutes straight. Creature of habit confirmed.",
            lambda e: f"You disabled shuffle to replay the same songs. That's not a playlist, that's a security blanket.",
            lambda e: f"{e['duration_min']:.0f}-minute comfort loop. Growth happens outside your comfort zone, just FYI.",
            lambda e: f"Repeat on, shuffle off. You're basically that person who orders the same thing at restaurants.",
        ],
        
        "binge_session": [
            lambda e: f"{e['duration_hours']:.1f} hours straight. {e['tracks']} tracks. Go outside. Touch grass.",
            lambda e: f"{e['duration_hours']:.1f}-hour session? That's not listening, that's dissociating.",
            lambda e: f"You listened for {e['duration_hours']:.1f} hours without stopping. Bro. Take a break. Please.",
            lambda e: f"{e['tracks']} tracks in {e['duration_hours']:.1f} hours. This is giving 'avoiding responsibilities' energy.",
            lambda e: f"{e['duration_hours']:.1f} hours? At this point the algorithm is worried about YOU.",
        ],
        
        "high_replay_rate": [
            lambda e: f"{e['replay_pct']}% of your tracks are repeats. Found 5 songs in 2010 and never looked back, huh?",
            lambda e: f"You replay {e['replay_pct']}% of tracks. There are literally millions of other songs. Explore.",
            lambda e: f"{e['replay_pct']}% replay rate. Commitment issues everywhere except your playlist apparently.",
            lambda e: f"Same. Songs. Every. Time. {e['replay_pct']}% repeats. The algorithm has given up on you.",
        ],
        
        "artist_obsessed": [
            lambda e: f"{e['artist']} is {e['percentage']}% of your listening. They're not gonna date you, bestie.",
            lambda e: f"{e['artist']}: {e['percentage']}%. That's not a fan, that's a fixation.",
            lambda e: f"{e['percentage']}% {e['artist']}. Bro there are OTHER artists. Please.",
            lambda e: f"You've played {e['artist']} so much their royalty check has your name on it.",
        ],
        
        "song_addiction": [
            lambda e: f"Played '{e['song']}' {e['count']} times. Are you okay? Do you need someone to talk to?",
            lambda e: f"'{e['song']}' × {e['count']}. That's not a favorite, that's a coping mechanism.",
            lambda e: f"{e['count']} plays of '{e['song']}'. You know other songs exist, right?",
            lambda e: f"'{e['song']}': {e['count']} plays. At this point it's less about the song and more about what you're avoiding.",
        ],
        
        "weekend_only": [
            lambda e: "Only listen on weekends? What, weekdays too busy being productive? Doubt it.",
            lambda e: "Weekend warrior energy. Monday hits and you ghost Spotify until Friday.",
            lambda e: "You're a weekend listener. The algorithm doesn't know what to do with you.",
        ],
        
        "late_night_listener": [
            lambda e: "Up at 2am listening to sad songs? We've all been there... but not THIS much.",
            lambda e: "Late night listening: certified. Sleep schedule: destroyed.",
            lambda e: "Your peak hours are when most people are asleep. That's either dedication or depression.",
        ],
        
        "low_diversity": [
            lambda e: f"Diversity score: {e['score']:.2f}. You discovered 10 songs and decided that was enough.",
            lambda e: f"{e['score']:.2f} diversity. Algorithms are BEGGING you to branch out.",
            lambda e: f"Musical diversity: {e['score']:.2f}. That's... not great bestie.",
        ],
        
        "chronic_skipper": [
            lambda e: f"Average skip rate: {e['skip_pct']}%. Nothing's ever good enough, huh?",
            lambda e: f"{e['skip_pct']}% skip rate. The commitment issues are showing.",
            lambda e: f"You skip {e['skip_pct']}% of tracks. Maybe you're the problem?",
        ],
        
        "perfectly_average": [
            lambda e: "Your listening habits are so average the algorithm uses you as a baseline. Congrats?",
            lambda e: "You're peak mid. Not bad, not interesting. Just... there.",
            lambda e: "Perfectly average behavior. The algorithm treats you like a control group.",
        ],
        
        "deviation_high": [
            lambda e: f"Your behavior changed {e['deviation']:.0%} recently. Everything okay? Serious question.",
            lambda e: f"Deviation score: {e['deviation']:.0%}. Something happened. The data knows.",
            lambda e: f"You're listening VERY differently than usual ({e['deviation']:.0%} change). We're concerned.",
        ],
    }
    
    # General roasts (not event-specific)
    GENERAL_ROASTS = [
        "Your taste is... unique. And by unique I mean questionable.",
        "The algorithm  tried to recommend you new music but gave up.",
        "Spotify Wrapped was too embarrassed to show some of this.",
        "You listen like someone who discovered music last year and stopped exploring.",
        "Your playlist has the energy of 'I peaked in high school'.",
    ]
    
    @staticmethod
    def roast_event(event: Dict) -> str:
        """
        Generate roast for a specific behavioral event.
        
        Args:
            event: Event dictionary with 'type' and event-specific data
            
        Returns:
            Contextual roast string
        """
        event_type = event.get("type")
        
        if event_type in RoastEngine.ROASTS:
            roast_options = RoastEngine.ROASTS[event_type]
            chosen_roast = random.choice(roast_options)
            return chosen_roast(event)
        
        return random.choice(RoastEngine.GENERAL_ROASTS)
    
    @staticmethod
    def roast_multiple_events(events: List[Dict], max_roasts: int = 3) -> List[str]:
        """
        Generate multiple roasts from event list.
        
        Args:
            events: List of behavioral events
            max_roasts: Maximum number of roasts to return
            
        Returns:
            List of roast strings
        """
        if not events:
            return [random.choice(RoastEngine.GENERAL_ROASTS)]
        
        # Sample events to roast (avoid duplicate types)
        event_types_seen = set()
        selected_events = []
        
        for event in events:
            event_type = event.get("type")
            if event_type not in event_types_seen:
                selected_events.append(event)
                event_types_seen.add(event_type)
            
            if len(selected_events) >= max_roasts:
                break
        
        return [RoastEngine.roast_event(e) for e in selected_events]
    
    @staticmethod
    def roast_stats(stats: Dict) -> List[str]:
        """
        Generate roasts from statistical data.
        
        Args:
            stats: Dictionary with stat_type -> value
            
        Returns:
            List of roast strings
        """
        roasts = []
        
        # Convert stats to pseudo-events for roasting
        if stats.get("replay_pct", 0) > 30:
            roasts.append(RoastEngine.roast_event({
                "type": "high_replay_rate",
                "replay_pct": stats["replay_pct"]
            }))
        
        if stats.get("top_artist_pct", 0) > 20:
            roasts.append(RoastEngine.roast_event({
                "type": "artist_obsessed",
                "artist": stats.get("top_artist", "someone"),
                "percentage": stats["top_artist_pct"]
            }))
        
        if stats.get("diversity_score", 1.0) < 0.3:
            roasts.append(RoastEngine.roast_event({
                "type": "low_diversity",
                "score": stats["diversity_score"]
            }))
        
        if not roasts:
            roasts.append(random.choice(RoastEngine.GENERAL_ROASTS))
        
        return roasts
    
    @staticmethod
    def closing_roast() -> str:
        """Get a random closing roast."""
        closings = [
            "Well, that was... something. Got any worse taste you wanna share?",
            "In conclusion: yikes.",
            "Your listening history is a cry for help disguised as a playlist.",
            "Anyway, keep vibing (or whatever you call this).",
            "The data has spoken. And it's not impressed.",
            "Thanks for coming to my TED Talk about your questionable choices.",
            "You can't fix this but at least you're self-aware now.",
            "This concludes today's roast. You're welcome.",
        ]
        return random.choice(closings)
