import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from .models import SpotifyToken
from datetime import datetime, timedelta
from django.utils import timezone


def get_spotify_auth_manager():
    return SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-library-read playlist-modify-public playlist-modify-private",
    )


def get_user_token(user):
    try:
        user_token = SpotifyToken.objects.get(user=user)
        # Use timezone.now() instead of datetime.now() to get a timezone-aware datetime
        if user_token.expires_at <= timezone.now():
            refresh_spotify_token(user_token)
        return user_token.access_token
    except SpotifyToken.DoesNotExist:
        return None


def refresh_spotify_token(token_model):
    auth_manager = get_spotify_auth_manager()
    new_token = auth_manager.refresh_access_token(token_model.refresh_token)

    token_model.access_token = new_token["access_token"]
    # Use timezone.now() for consistent timezone-aware datetimes
    token_model.expires_at = timezone.now() + timedelta(seconds=new_token["expires_in"])
    token_model.save()


def save_spotify_token(user, token_info):
    expires_in = token_info["expires_in"]
    # Use timezone.now() for consistent timezone-aware datetimes
    expires_at = timezone.now() + timedelta(seconds=expires_in)

    try:
        token = SpotifyToken.objects.get(user=user)
        token.access_token = token_info["access_token"]
        token.refresh_token = token_info["refresh_token"]
        token.expires_at = expires_at
        token.save()
    except SpotifyToken.DoesNotExist:
        token = SpotifyToken(
            user=user,
            access_token=token_info["access_token"],
            refresh_token=token_info["refresh_token"],
            expires_at=expires_at,
        )
        token.save()


def get_spotify_client(user):
    token = get_user_token(user)
    if token:
        return spotipy.Spotify(auth=token)
    return None


def get_liked_songs(spotify_client, limit=50):
    """Get user's liked songs from Spotify"""
    results = spotify_client.current_user_saved_tracks(limit=limit)
    tracks = results["items"]

    # Handle pagination if there are more than 50 liked songs
    while results["next"]:
        results = spotify_client.next(results)
        tracks.extend(results["items"])

    return tracks


def create_new_playlist(spotify_client, name, description=""):
    """Create a new playlist on Spotify"""
    user_id = spotify_client.me()["id"]
    playlist = spotify_client.user_playlist_create(
        user=user_id, name=name, public=True, description=description
    )
    return playlist


def add_tracks_to_playlist(spotify_client, playlist_id, track_uris):
    """Add tracks to a Spotify playlist"""
    # Spotify API has a limit of 100 tracks per request
    chunk_size = 100
    for i in range(0, len(track_uris), chunk_size):
        chunk = track_uris[i : i + chunk_size]
        spotify_client.playlist_add_items(playlist_id, chunk)
