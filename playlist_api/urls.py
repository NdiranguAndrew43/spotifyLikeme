from django.urls import path
from . import views

urlpatterns = [
    path('spotify/login/', views.spotify_login, name='spotify_login'),
    path('spotify/callback/', views.spotify_callback, name='spotify_callback'),
    path('spotify/create-playlist/', views.create_playlist_from_liked_songs, name='create_playlist'),
    path('spotify/playlists/', views.get_user_playlists, name='get_playlists'),
]

