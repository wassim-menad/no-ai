from django.db import models

class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_game_started = models.BooleanField(default=False)  # Tracks if the game has started
    game_start_time = models.DateTimeField(null=True, blank=True)  # Tracks the start time of the game

    def __str__(self):
        return self.name




class Player(models.Model):
    username = models.CharField(max_length=100)
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='players')
    is_ready = models.BooleanField(default=False)
    is_leader = models.BooleanField(default=False)  # Add this line

    def __str__(self):
        return self.username
