# Spotiloader - Spotify Song Tracker

A Python application that monitors your Spotify playback and logs song metadata to files in real-time. I tried to include a BPM feature, however, Spotify API metadata doesn't include such information. Will plan on removing in the future.

## Features

- **Real-time Monitoring**: Tracks currently playing songs from Spotify
- **Current Song Display**: Maintains `current_song.txt` with the song currently playing
- **Song History**: Logs all played songs with timestamps to `song_history.txt`
- **Automatic Process Detection**: Waits for Spotify to launch before connecting
- **Error Handling**: Gracefully handles API errors and continues monitoring
- **OAuth Authentication**: Secure authentication via Spotify Developer API

## Requirements

- Python 3.7+
- Spotify Account (Free or Premium)
- Spotify Desktop Application

## Installation

1. **Clone or download this project**

2. **Install required packages**:
   ```powershell
   pip install psutil spotipy python-dotenv
   ```

3. **Create a Spotify Developer Application**:
   - Go to https://developer.spotify.com/dashboard
   - Log in or create an account
   - Create a new app
   - Accept the terms and create
   - You'll get a CLIENT_ID and CLIENT_SECRET

4. **Configure the `.env` file**:
   ```
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
   ```

5. **Update Spotify App Settings**:
   - Go back to your Spotify app on the dashboard
   - Click "Edit Settings"
   - Set Redirect URI to: `http://127.0.0.1:8888/callback`
   - Save changes

## Usage

1. **Start Spotify** on your system

2. **Run the script**:
   ```powershell
   python.exe spotiloader.py
   ```

3. **Authorize the app**:
   - A browser window will open to Spotify's authorization page
   - Click "AGREE" to grant the app permission to read your playback
   - The browser will redirect (and may show an error - this is normal)

4. **Monitor playback**:
   - The script will begin tracking songs as you play them
   - Check `current_song.txt` for the currently playing song
   - Check `song_history.txt` for a complete history with timestamps

5. **Stop the script**:
   - Press `Ctrl+C` in the terminal to stop monitoring

## Output Files

### `current_song.txt`
Shows the currently playing song (updates every time the track changes):
```
Song: Song Name
Artist: Artist Name
Duration: 3:45
BPM: N/A
```

### `song_history.txt`
Complete history of all songs played with timestamps (never overwrites):
```
[2025-12-02 14:30:15] Song: Song 1 | Artist: Artist 1 | Duration: 3:45 | BPM: N/A
[2025-12-02 14:34:10] Song: Song 2 | Artist: Artist 2 | Duration: 4:12 | BPM: N/A
```

## Notes

- **BPM Data**: Shows "N/A" due to Spotify API limitations. Premium accounts may have better access.
- **Process Detection**: The script checks for `Spotify.exe` process on Windows
- **Check Interval**: Updates every 5 seconds
- **Cache Files**: The script auto-manages authentication cache (`.cache` file)

## Troubleshooting

**Script says "Waiting for Spotify to open"**:
- Launch Spotify Desktop application
- The script will automatically detect it and connect

**403 Error on audio-features**:
- This is expected for free Spotify accounts
- The script handles this gracefully and logs songs without BPM data
- Expect an HTTP error when transitioning between songs. It's a normal feature.

**Browser doesn't open for authorization**:
- Manually open https://accounts.spotify.com/en/authorize and follow the OAuth flow
- Or check if your browser is opening in the background

**Invalid credentials error**:
- Verify your CLIENT_ID and CLIENT_SECRET match your Spotify app dashboard
- Make sure your `.env` file is in the same directory as `spotiloader.py`

## Code Structure

- **Configuration Section**: Loads credentials and sets up API parameters
- **Utility Functions**: 
  - `spotify_is_running()`: Checks if Spotify is running
  - `get_spotify_client()`: Initializes OAuth authentication
  - `write_metadata()`: Writes song data to files
- **Main Loop**: Continuously monitors Spotify playback and logs songs

## License

Free to use and modify for personal projects.

## Support

For issues with the Spotify API, visit: https://developer.spotify.com/documentation/web-api


## MOST IMPORTANT

Enjoy