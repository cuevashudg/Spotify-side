import time
import os
import psutil
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import webbrowser
import csv

# ==============================================================================
# CONFIGURATION AND INITIALIZATION SECTION
# ==============================================================================

# Load environment variables from .env file (contains API credentials)
load_dotenv()

# Retrieve Spotify API credentials from environment variables
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# OAuth redirect URI - where Spotify redirects after user authorization
# Uses loopback address (127.0.0.1) which is allowed by Spotify with HTTP
REDIRECT_URI = "http://127.0.0.1:8888/callback"

# API scopes - permissions requested from the user
# user-read-currently-playing streaming : Access to streaming features read currently playing track and control playback
SCOPE = "user-read-playback-state user-read-currently-playing streaming"

# Validate that credentials are set before proceeding
if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env file")

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def spotify_is_running():
    """
    Check if Spotify application is currently running on the system.
    
    Returns:
        bool: True if Spotify.exe process is found, False otherwise
    """
    return any("Spotify.exe" in p.name() for p in psutil.process_iter())

def get_spotify_client():
    """
    Initialize and return a Spotify API client with OAuth authentication.
    
    Returns:
        spotipy.Spotify: Authenticated Spotify client object
    """
    # Remove cached token to force fresh authorization
    cache_path = ".cache"
    if os.path.exists(cache_path):
        os.remove(cache_path)
    
    # Create and return authenticated Spotify client
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=cache_path,
        show_dialog=True
    )
    return spotipy.Spotify(auth_manager=auth_manager)

def write_metadata(track, features=None):
    """
    Write current song metadata to files for tracking.
    
    Args:
        track (dict): Current playback object from Spotify API
    """
    # Extract song information
    name = track["item"]["name"]
    artist = track["item"]["artists"][0]["name"]
    album = track["item"]["album"]["name"]
    track_id = track["item"]["id"]
    duration_ms = track["item"]["duration_ms"]
    duration_sec = duration_ms // 1000
    duration_formatted = f"{duration_sec // 60}:{duration_sec % 60:02d}"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # Write current song (overwrites previous)
    with open("current_song.txt", "w", encoding="utf-8") as f:
        f.write(f"Song: {name}\nArtist: {artist}\nDuration: {duration_formatted}\n")

    # Append to song history (text format)
    with open("song_history.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Song: {name} | Artist: {artist} | Duration: {duration_formatted}\n")
    
    # Append to CSV file for MongoDB import
    csv_file = "song_history.csv"
    file_exists = os.path.exists(csv_file)
    
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write header if file doesn't exist
        if not file_exists:
            writer.writerow(["timestamp", "song_name", "artist", "album", "track_id", "duration_ms", "duration_formatted"])
        # Write song data
        writer.writerow([timestamp, name, artist, album, track_id, duration_ms, duration_formatted])

# ==============================================================================
# MAIN MONITORING LOOP
# ==============================================================================

def main():
    """
    Monitor Spotify playback and log song metadata.
    
    Process:
    1. Waits for Spotify to launch
    2. Authenticates with Spotify API
    3. Logs song info every 5 seconds when playing
    4. Handles errors gracefully
    """
    print("Waiting for Spotify to open...")
    while not spotify_is_running():
        time.sleep(2)

    print("Spotify detected. Connecting to API...")
    sp = get_spotify_client()
    last_track_id = None

    while True:
        try:
            if spotify_is_running():
                current = sp.current_playback()
                if current and current["is_playing"] and current["item"]:
                    track_id = current["item"]["id"]
                    if track_id != last_track_id:
                        write_metadata(current)
                        last_track_id = track_id
                        print(f"Updated: {current['item']['name']} by {current['item']['artists'][0]['name']}")
            else:
                print("Spotify closed. Waiting...")
                last_track_id = None
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
        
        time.sleep(5)

# ==============================================================================
# SCRIPT ENTRY POINT
# ==============================================================================

# Only run main() if this file is executed directly (not imported as a module)
if __name__ == "__main__":
    main()

