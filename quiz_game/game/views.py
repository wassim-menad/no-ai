import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .forms import CustomUserCreationForm


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Log in the user after registration
            return redirect('index') # Redirect to your homepage
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def index(request):
    """
    Renders the homepage where users input their name and join or create a room.
    """
    return render(request, 'game/index.html')
def room(request):
    """
    Renders the homepage where users input their name and join or create a room.
    """
    return render(request, 'game/room.html')
