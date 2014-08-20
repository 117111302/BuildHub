import json
import requests
import urlparse

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt

from core.models import Webhook

CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET = settings.CLIENT_SECRET
API_ROOT = 'https://api.github.com/'


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

    request.session['access_token'] = access_token
    params = {'access_token': access_token, 'type': 'owner', 'sort': 'updated'}
    # List repositories for the authenticated user.
    repos = requests.get('https://api.github.com/user/repos', params=params, headers=headers)

    # List public and private organizations for the authenticated user.
    orgs = requests.get('https://api.github.com/user/orgs', params=params, headers=headers)

    content = {'repos': repos.json(), 'orgs': orgs.json()}
    return render(request, 'core/index.html', content)

@csrf_exempt
def payload(request):
    """github payloads
    """
    content = {}
    return render(request, 'core/index.html', content)


def create_hook(request):
    """create webhook
    """
    params = dict(name=request.GET['repo'],
		event=['push', 'pull_request'],
		active=True,
		config=dict(url='http://4fea4883.ngrok.com/payload/',
		    content_type='json',
		    insecure_ssl='1')
		)
    uri = '/repos/:owner/:repo/hooks'
    hook = requests.post(urlparse.urljoin(API_ROOT, uri), params=params, headers={'Accept': 'application/json'})
    return HttpResponse('Success!')
