from django.contrib import admin
from .models import SpotifyToken, SharedPlaylist

@admin.register(SpotifyToken)
class SpotifyTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'expires_at', 'created_at')
    search_fields = ('user__username',)

@admin.register(SharedPlaylist)
class SharedPlaylistAdmin(admin.ModelAdmin):
    list_display = ('playlist_name', 'user', 'created_at')
    search_fields = ('playlist_name', 'user__username')
    list_filter = ('created_at',)

