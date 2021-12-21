from django.shortcuts import render

# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (LoginView, LogoutView)
from django.contrib.auth import authenticate
from django.shortcuts import HttpResponse
import json
from .forms import LoginForm


class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'accounts/login.html'


class Logout(LoginRequiredMixin, LogoutView):
    """ログアウトページ"""
    template_name = 'accounts/login.html'


def check_log_in_view(request):
    if 'username' in request.GET and 'password' in request.GET:
        user_name = request.GET['username']
        password = request.GET['password']

        auth = authenticate(request, username=user_name, password=password)

        json_str = json.dumps(
            {'username': user_name, 'password': password, 'auth': auth is not None},
            ensure_ascii=False,
            indent=2
        )
    else:
        json_str = json.dumps(
            {'username': '', 'password': '', 'auth': False},
        )
    return HttpResponse(json_str)
