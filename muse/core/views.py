import json
import requests

from django.shortcuts import render
from django.conf import settings

CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET = settings.CLIENT_SECRET


def login(request):
    """login view
    """
    content = {'client_id': CLIENT_ID}
    return render(request, 'core/login.html', content)


def index(request):
    """index view
    """
    return render(request, 'core/index.html')


def oauth_callback(request):
    """oauth callback
    """
    # get temporary GitHub code...
    session_code = request.GET['code']

    # ... and POST it back to GitHub
    data = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'code': session_code}
    headers = {'Accept': 'application/json'}
    r = requests.post('https://github.com/login/oauth/access_token', data=data, headers=headers)
    # extract the token and granted scopes
    # if error:
    access_token = r.json()['access_token']

    params = {'access_token': access_token, 'type': 'owner', 'sort': 'updated'}
    r = requests.get('https://api.github.com/user/repos', params=params, headers=headers)
    content = {'repolist': r.json()}
    return render(request, 'core/index.html', content)
