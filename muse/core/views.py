import json
import requests
import urlparse

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from django.template import loader, Context, Template
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from github import Github
from lib import jenkins
from furl import furl

from core.models import Payload
from core.models import Badge

CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET = settings.CLIENT_SECRET
API_ROOT = settings.GITHUB_API
SERVER = settings.BACKEND_SERVER
OAUTH_URL = settings.OAUTH_URL
REDIRECT_URI = settings.REDIRECT_URI


def login(request):
    """login view
    """
    content = {'client_id': CLIENT_ID, 'scopes':'user:email,admin:repo_hook'}
    return render(request, 'core/login.html', content)


def auth(request):
    """auth with Github
    """
    auth_uri = urlparse.urljoin
    params = {'client_id': CLIENT_ID, 'scope':'user:email,admin:repo_hook', 'redirect_uri': REDIRECT_URI}
    f = furl(OAUTH_URL)
    f.add(params)
    return HttpResponseRedirect(f.url)


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
    access_token = request.session.get('access_token')
    print access_token

    # extract the token and granted scopes
    # if error:
    if not access_token:
        access_token = r.json()['access_token']
        request.session['access_token'] = access_token
    client = Github(access_token)
    user = client.get_user()
    # List repositories for the authenticated user.
    repos = client.get_user().get_repos()
    # List public and private organizations for the authenticated user.
    orgs = user.get_orgs()

    content = {'repos': repos, 'orgs': orgs}
    return render(request, 'core/index.html', content)


@csrf_exempt
def payload(request):
    """github payloads
    """
    clone_url = ''
    event = request.META.get('HTTP_X_GITHUB_EVENT')
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
    print 'Jenkins job' + '-'*80
    J = jenkins.get_server_instance()
#    if event == 'push':
#        clone_url = data['repository']['clone_url']
#    if event == 'pull_request':
#        clone_url = data['head']['repo']['clone_url']
    r = J[settings.JENKINS_JOB].invoke(build_params={'data': payload})
    build_id = r.get_build_number()
    print 'build_id: ', build_id
    branch = data['repository']['default_branch']
    Payload.objects.create(repo=repo, payload=payload, build_id=build_id, branch=branch)
    print '-'*80
    # FIXME GitHub will time out, can we use subprocess to get build status, and set status to badge?
    #while r.get_build().is_running():
    #    print 'job status: ', r.get_build().is_running()
    #    status = r.get_build().get_status()
    Badge.objects.get_or_create(repo=repo, branch=branch)
    return HttpResponse('OK')


def create_hook(request):
    """create webhook
    """
    access_token=request.session['access_token']
    client = Github(access_token)
    repo = client.get_user().get_repo(request.GET['repo'])
    try:
	repo.create_hook(name='web', config=dict(url=urlparse.urljoin(SERVER, '/payload/'), content_type='json'), events=['push', 'pull_request'], active=True)
	return HttpResponse('Create success!')
    except Exception as e:
	return HttpResponse(e)
    return HttpResponse(hook.text)


def repo(request, repo):
    """webhook page
    """
    hooks = Payload.objects.filter(repo=repo)
    for h in hooks:
        h.pretty = json.dumps(json.loads(h.payload), indent=2)

    J = jenkins.get_server_instance()
#    if event == 'push':
#        clone_url = data['repository']['clone_url']
#    if event == 'pull_request':
#        clone_url = data['head']['repo']['clone_url']
    r = J[settings.JENKINS_JOB].get_last_build().get_console()
    print r
 
    return render(request, 'core/repo.html', locals())


def badge(request, branch, repo):
    #get status from db by project, branch
    badge = Badge.objects.get(repo=repo, branch=branch)
    if not badge:
        status = 'UNKNOW'
    else:
        status = badge.status
    status = {'FAILURE': ('failing', 'red'), 'SUCCESS': ('success', 'brightgreen'), 'UNKNOW': ('unkonw', 'lightgrey')}
    url = 'http://img.shields.io/badge/build-%s-%s.svg' % status[status]
    return HttpResponseRedirect(url)


def builds(request, repo, build_id):
    """get build console
    """
    status = {}
    J = jenkins.get_server_instance()
    build = J[settings.JENKINS_JOB].get_build(int(build_id))

    print 'running :', build.is_running()
    t = loader.get_template('core/build.html')

    console = realtime_console(t, build, status)

    payload = Payload.objects.get(repo=repo, build_id=build_id)
    badge = Badge.objects.get_or_create(repo=repo, branch=payload.branch)

    badge.status = status['status']
    badge.save()
   
    return StreamingHttpResponse(console)


def realtime_console(t, build, res):
    s = ''

    # get build console when job is finished
    if not build.is_running():
        status = build.get_status()
        yield t.render(Context({'console': build.get_console()}))

    building = build.is_running()
    # get build console when job is running
    while building:
        building = build.is_running()
        console = build.get_console()
        status = build.get_status()
        print '-'*80
        print console
        news = console.strip(s)
        print 'news'+'-'*80
        print news
        s = console
        if news:
            yield t.render(Context({'console': news}))
        print '-'*80

    res['status'] = status


t = loader.get_template('core/build.html')

def gen_rendered():
    yield t.render(Context({'console': "console********************************"}))
    j = 0
    for x in range(1,11):
        yield t.render(Context({'console': (x-j)}))
        j = x

def stream_view(request):

    response = StreamingHttpResponse(gen_rendered())
    return response
