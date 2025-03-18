from django.db import models
from django.contrib.auth.models import User

class SpotifyToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Spotify Token"

class SharedPlaylist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    playlist_id = models.CharField(max_length=255)
    playlist_name = models.CharField(max_length=255)
    playlist_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.playlist_name} by {self.user.username}"

