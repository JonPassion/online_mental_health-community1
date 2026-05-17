from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def mini_chats(request):
    return render(request, "chat_dash/chadashboard.html")

def miniposts(request):
    return render(request, "chat_dash/podash.html")