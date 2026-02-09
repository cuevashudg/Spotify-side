"""
Diagnostic script to identify the Spotify API 403 error.

Run: python scripts/diagnose_api.py
"""

import os
import sys
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def diagnose():
    """Diagnose Spotify API connection issues."""
    print("\n🔍 Spotify API Diagnostics")
    print("=" * 60)
    
    # Check environment variables
    load_dotenv()
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    print("\n1. Environment Variables:")
    print(f"   CLIENT_ID: {'✅ Set' if client_id else '❌ Missing'}")
    print(f"   CLIENT_SECRET: {'✅ Set' if client_secret else '❌ Missing'}")
    
    if not client_id or not client_secret:
        print("\n❌ Missing credentials in .env file")
        return
    
    # Test authentication
    print("\n2. Testing Authentication...")
    
    try:
        # Use broader scope
        scope = "user-read-playback-state user-read-currently-playing user-library-read user-top-read"
        
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://127.0.0.1:8888/callback",
            scope=scope,
            cache_path=".cache-diagnostic",
            show_dialog=True,
            open_browser=True
        )
        
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Test basic API call
        print("   Testing current user endpoint...")
        user = sp.current_user()
        print(f"   ✅ Authenticated as: {user['display_name']} ({user['id']})")
        
        # Test playback
        print("\n3. Testing Playback Access...")
        try:
            current = sp.current_playback()
            if current and current.get("item"):
                track_id = current["item"]["id"]
                track_name = current["item"]["name"]
                print(f"   ✅ Current track: {track_name}")
                
                # Test audio features - THIS IS WHERE IT FAILS
                print("\n4. Testing Audio Features Access...")
                print(f"   Fetching features for track: {track_id}")
                
                features = sp.audio_features([track_id])
                
                if features and features[0]:
                    print(f"   ✅ Audio features retrieved!")
                    print(f"      Energy: {features[0]['energy']:.2f}")
                    print(f"      Valence: {features[0]['valence']:.2f}")
                    print(f"      Tempo: {features[0]['tempo']:.1f}")
                    print("\n🎉 SUCCESS! Audio features are working!")
                else:
                    print(f"   ⚠️  Features returned None (track might not have features)")
            else:
                print("   ⚠️  No track currently playing")
                print("   Play a song and run this again to test audio features")
        
        except Exception as e:
            print(f"   ❌ Playback test failed: {e}")
            
            # Try audio features anyway with a known track
            print("\n   Trying with a known track ID...")
            test_track_id = "11dFghVXANMlKmJXsNCbNl"  # Cut To The Feeling - Carly Rae Jepsen
            
            try:
                features = sp.audio_features([test_track_id])
                if features and features[0]:
                    print(f"   ✅ Audio features work! The issue is elsewhere.")
                    print(f"      Energy: {features[0]['energy']:.2f}")
                else:
                    print(f"   ❌ Audio features returned None")
            except Exception as feat_error:
                print(f"   ❌ Audio features failed: {feat_error}")
                
                # Parse error
                error_str = str(feat_error)
                if "403" in error_str:
                    print("\n" + "=" * 60)
                    print("🔍 DIAGNOSIS: HTTP 403 - Forbidden")
                    print("=" * 60)
                    print("\nPossible causes:")
                    print("1. App in Development Mode (limited to 25 users)")
                    print("2. Redirect URI mismatch in Dashboard")
                    print("3. App needs Extended Quota Mode")
                    print("\n📋 SOLUTION:")
                    print("Go to: https://developer.spotify.com/dashboard")
                    print("   1. Select your app")
                    print("   2. Settings → Edit Settings")
                    print("   3. Redirect URIs → Add: http://127.0.0.1:8888/callback")
                    print("   4. Save")
                    print("   5. Request Extended Quota Mode if needed")
                    print("\nThen delete .cache* files and try again.")
        
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}")
    
    # Cleanup
    if os.path.exists(".cache-diagnostic"):
        os.remove(".cache-diagnostic")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    diagnose()
