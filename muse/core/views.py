import json
import requests
import urlparse

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from github import Github

from core.models import Payload

CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET = settings.CLIENT_SECRET
API_ROOT = 'https://api.github.com/'


def login(request):
    """login view
    """
    content = {'client_id': CLIENT_ID, 'scopes':'user:email,admin:repo_hook'}
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

    # POST it back to GitHub
    data = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'code': session_code}
    headers = {'Accept': 'application/json'}
    r = requests.post('https://github.com/login/oauth/access_token', data=data, headers=headers)
    # extract the token and granted scopes
    # if error:
    access_token = request.session.get('access_token')
    if not access_token:
        access_token = r.json()['access_token']
        request.session['access_token'] = access_token
    params = {'access_token': access_token, 'type': 'owner', 'sort': 'updated'}
    # List repositories for the authenticated user.
    repos = requests.get('https://api.github.com/user/repos', params=params, headers=headers)

    # List public and private organizations for the authenticated user.
    orgs = requests.get('https://api.github.com/user/orgs', params=params, headers=headers)

    orgs = requests.get('https://api.github.com/repos/117111302/iris/hooks', params={'access_token': access_token})
    content = {'repos': repos.json(), 'orgs': orgs.json()}
    return render(request, 'core/index.html', content)


@csrf_exempt
def payload(request):
    """github payloads
    """
    payload = request.body
    data = json.loads(payload)
    print '-'*80
    print json.dumps(data, indent=2)
    print '-'*80
    repo = data['repository']['name']
    webhook = Payload.objects.create(repo=repo, payload=payload)
    return HttpResponse(unicode(webhook))


def create_hook(request):
    """create webhook
    """
    access_token=request.session['access_token']
    data = dict(name='web',
		events=['push', 'pull_request'],
		active=True,
		config=dict(url='http://522bbc09.ngrok.com/payload',
		    content_type='json')
		)
    uri = '/repos/117111302/%s/hooks' % (request.GET['repo'])
    hook = requests.post(urlparse.urljoin(API_ROOT, uri), data=json.dumps(data), params={'access_token': access_token})
    #client = Github(access_token)
    #repo = client.get_user().get_repo(request.GET['repo'])
    #repo.create_hook(name='web', config=data, events=["push"], active=True)
    return HttpResponse(hook.text)


def repo(request):
    """webhook page
    """
    repo = request.GET['repo']
    hooks = Payload.objects.filter(repo=repo)
    print 'hooks====================>', hooks
    for h in hooks:
        h.pretty = json.dumps(json.loads(h.payload), indent=2)
    return render(request, 'core/repo.html', locals())
