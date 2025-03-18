from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import spotipy

from .spotify_client import (
    get_spotify_auth_manager,
    save_spotify_token,
    get_spotify_client,
    get_liked_songs,
    create_new_playlist,
    add_tracks_to_playlist,
)
from .models import SharedPlaylist


def spotify_login(request):
    """Redirect user to Spotify authorization page"""
    auth_manager = get_spotify_auth_manager()
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)


def spotify_callback(request):
    """Handle callback from Spotify OAuth"""
    code = request.GET.get("code")

    if not code:
        return JsonResponse({"error": "Authorization code not provided"}, status=400)

    auth_manager = get_spotify_auth_manager()
    token_info = auth_manager.get_access_token(code)

    # For simplicity, we're creating or getting a user based on Spotify username
    # In a real app, you'd want proper user authentication
    sp = spotipy.Spotify(auth=token_info["access_token"])
    spotify_user = sp.me()

    user, created = User.objects.get_or_create(
        username=spotify_user["id"], defaults={"email": spotify_user.get("email", "")}
    )

    save_spotify_token(user, token_info)

    # Redirect to frontend or return success response
    return JsonResponse(
        {
            "success": True,
            "message": "Successfully authenticated with Spotify",
            "user_id": user.id,
        }
    )


@api_view(["POST"])
def create_playlist_from_liked_songs(request):
    """Create a new playlist from user's liked songs"""
    user_id = request.data.get("user_id")
    playlist_name = request.data.get("playlist_name", "My Liked Songs")
    playlist_description = request.data.get(
        "description", "A playlist of my liked songs on Spotify"
    )

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    spotify = get_spotify_client(user)
    if not spotify:
        return Response(
            {"error": "Spotify authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        # Get user's liked songs
        liked_songs = get_liked_songs(spotify)

        if not liked_songs:
            return Response(
                {"message": "No liked songs found"}, status=status.HTTP_200_OK
            )

        # Create a new playlist
        playlist = create_new_playlist(spotify, playlist_name, playlist_description)

        # Extract track URIs from liked songs
        track_uris = [item["track"]["uri"] for item in liked_songs]

        # Add tracks to the playlist
        add_tracks_to_playlist(spotify, playlist["id"], track_uris)

        # Save the shared playlist to the database
        shared_playlist = SharedPlaylist.objects.create(
            user=user,
            playlist_id=playlist["id"],
            playlist_name=playlist["name"],
            playlist_url=playlist["external_urls"]["spotify"],
        )

        return Response(
            {
                "success": True,
                "message": "Playlist created successfully",
                "playlist": {
                    "id": playlist["id"],
                    "name": playlist["name"],
                    "url": playlist["external_urls"]["spotify"],
                    "tracks_count": len(track_uris),
                },
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def get_user_playlists(request):
    """Get all playlists created by the user"""
    user_id = request.query_params.get("user_id")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    playlists = SharedPlaylist.objects.filter(user=user).order_by("-created_at")

    playlist_data = [
        {
            "id": playlist.id,
            "playlist_id": playlist.playlist_id,
            "name": playlist.playlist_name,
            "url": playlist.playlist_url,
            "created_at": playlist.created_at,
        }
        for playlist in playlists
    ]

    return Response(playlist_data, status=status.HTTP_200_OK)

# Add to playlist_api/views.py
def api_documentation(request):
    """Render the API documentation page"""
    return render(request, 'playlist_api/api_docs.html')
