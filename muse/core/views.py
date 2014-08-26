import json
import requests
import urlparse

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from github import Github

from core.models import Payload

CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET = settings.CLIENT_SECRET
API_ROOT = settings.GITHUB_API
SERVER = settings.BACKEND_SERVER


def login(request):
    """login view
    """
    content = {'client_id': CLIENT_ID, 'scopes':'user:email,admin:repo_hook'}
    return render(request, 'core/login.html', content)


def index(request, user):
    """index view
    """
    print "index==================>", user
    return render(request, 'core/index.html')


def oauth_callback(request, user=None):
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
    print request.META.get('HTTP_X_GITHUB_EVENT')
    payload = request.body
    if not payload:
	return HttpResponse('OK')
    data = json.loads(payload)
    print '-'*80
    print json.dumps(data, indent=2)
    print '-'*80
    if not data.get('repository'):
	return HttpResponse('OK')
    repo = data['repository']['name']
    webhook = Payload.objects.create(repo=repo, payload=payload)
    return HttpResponse(unicode(webhook))


def create_hook(request):
    """create webhook
    """
    access_token=request.session['access_token']
    uri = '/user'
    user_info = requests.get(urlparse.urljoin(API_ROOT, uri), params={'access_token': access_token})
    print user_info.json()
    user_name = user_info.json()['login']
    data = dict(name='web',
		events=['push', 'pull_request'],
		active=True,
		config=dict(url=urlparse.urljoin(SERVER, '/payload/'),
		    content_type='json')
		)
    uri = '/repos/%s/%s/hooks' % (user_name, request.GET['repo'])
    hook = requests.post(urlparse.urljoin(API_ROOT, uri), data=json.dumps(data), params={'access_token': access_token})
    #client = Github(access_token)
    #repo = client.get_user().get_repo(request.GET['repo'])
    #try:
#	repo.create_hook(name='web', config=dict(url='http://1223446e.ngrok.com/payload/', content_type='json'), events=["push"], active=True)
    #except Exception as e:
#	return HttpResponse(e)
    return HttpResponse(hook.text)


def repo(request, repo):
    """webhook page
    """
    hooks = Payload.objects.filter(repo=repo)
    print 'hooks====================>', hooks
    for h in hooks:
        h.pretty = json.dumps(json.loads(h.payload), indent=2)
    return render(request, 'core/repo.html', locals())
