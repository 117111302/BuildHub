import json
import requests
import urlparse

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from django.template import loader, Context, Template
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from github import Github
from lib import jenkins
from furl import furl

from .models import Payload
from .models import Badge
from .models import Repo

CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET = settings.CLIENT_SECRET
API_ROOT = settings.GITHUB_API
SERVER = settings.BACKEND_SERVER
OAUTH_URL = settings.OAUTH_URL
REDIRECT_URI = settings.REDIRECT_URI
BADGE_URL = settings.BADGE_URL


def login(request):
    """login view
    """
    content = {'client_id': CLIENT_ID, 'scopes': 'user:email,admin:repo_hook'}
    # if user login or not?
    return render(request, 'core/login.html', content)


def signin(request):
    """signin with Github
    """
    params = {'client_id': CLIENT_ID, 'scope': 'user:email,admin:repo_hook', 'redirect_uri': REDIRECT_URI}
    f = furl(OAUTH_URL)
    f.add(params)
    return HttpResponseRedirect(f.url)


#@login_required
def profile(request):
    """oauth callback
    """
    # get user info, set cookie, save user into db
    # if repo has hook?
    access_token = request.session.get('access_token')
    if not access_token:
        # get temporary GitHub code...
        session_code = request.GET['code']
        # POST it back to GitHub
        data = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'code': session_code}
        headers = {'Accept': 'application/json'}
        r = requests.post('https://github.com/login/oauth/access_token', data=data, headers=headers)
        print access_token
        access_token = r.json()['access_token']
        request.session['access_token'] = access_token


    headers = {'Accept': 'application/json'}

    params = {'access_token': access_token, 'type': 'owner', 'sort': 'updated'}
    # List repositories for the authenticated user.
    repos = requests.get('https://api.github.com/user/repos', params=params, headers=headers)
    repos = repos.json()

    # List public and private organizations for the authenticated user.
    orgs = requests.get('https://api.github.com/user/orgs', params=params, headers=headers)

#    client = Github(access_token)
#    user = client.get_user()
    # List repositories for the authenticated user.
#    repos = client.get_user().get_repos()
    for repo in repos:
        try:
            repo_id = repo['id']
            r = Repo.objects.get(repo_id=repo_id)
            if r.repo_id == repo_id:
#                setattr(repo, 'enable', r.enable)
                repo['enable'] = r.enable
        except ObjectDoesNotExist:
            continue
    # List public and private organizations for the authenticated user.
#    orgs = user.get_orgs()

    content = {'repos': repos, 'orgs': orgs, 'user': 'gao'}
    return render(request, 'core/profile.html', content)


#@login_required
def index(request, user=None):
    """oauth callback
    """
    # get user info, set cookie, save user into db
    # if repo has hook?

    access_token = request.session.get('access_token')
    print access_token

    repos = get_repos(access_token)
    # List public and private organizations for the authenticated user.
    #orgs = user.get_orgs()

    #content = {'repos': repos, 'orgs': orgs}
    content = {'repos': repos}
    return render(request, 'core/index.html', content)


#@login_required
@csrf_exempt
def payload(request):
    """github payloads
    """
    # add enable button, if disable, do not recive event, or not send, or not build
    # try to change Active status

    clone_url = ''
    event = request.META.get('HTTP_X_GITHUB_EVENT')
    print request.META.get('HTTP_X_GITHUB_EVENT')
    payload = request.body
    if not payload:
        return HttpResponse('OK')
    data = json.loads(payload)
    #print '-'*80
    #print json.dumps(data, indent=2)
    #print '-'*80
    if not data.get('repository'):
        return HttpResponse('OK')
    print 'Jenkins job' + '-'*80

    from multiprocessing import Process
    p = Process(target=process_JJ, args=(data, payload))
    p.start()
    p.join()

    return HttpResponse('OK')


def process_JJ(data, payload):
    repo = data['repository']['name']
    branch = data['repository']['default_branch']
    J = jenkins.get_server_instance()
#    if event == 'push':
#        clone_url = data['repository']['clone_url']
#    if event == 'pull_request':
#        clone_url = data['head']['repo']['clone_url']
    r = J[settings.JENKINS_JOB].invoke(build_params={'data': payload})
    while True:
        status = r.is_queued_or_running()
        print 'is running', status
        build_id = r.get_build_number()
        if not status:
            build_id = r.get_build_number()
            break
    print 'build_id: ', build_id
    Payload.objects.create(repo=repo, payload=payload, build_id=build_id, branch=branch)
    print '-'*80
    # FIXME GitHub will time out, can we use subprocess to get build status, and set status to badge?
    #while r.get_build().is_running():
    #    print 'job status: ', r.get_build().is_running()
    #    status = r.get_build().get_status()
    Badge.objects.get_or_create(repo=repo, branch=branch)

#@login_required
def create_hook(request):
    """create webhook
    """
    # add enable button, if disable, do not recive event

    access_token = request.session['access_token']

    uri = '/user'
    user_info = requests.get(urlparse.urljoin(API_ROOT, uri), params={'access_token': access_token})
    print user_info.json()
    user_name = user_info.json()['login']

    uri = '/repos/%s/%s' % (user_name, request.GET['repo'])

    repo = requests.get(urlparse.urljoin(API_ROOT, uri))
    repo = repo.json()

    data = dict(name='web',
                events=['push', 'pull_request'],
                active=True,
                config=dict(url=urlparse.urljoin(SERVER, '/payload/'),
                    content_type='json')
                )
    uri = '/repos/%s/%s/hooks' % (user_name, request.GET['repo'])
    hook = requests.post(urlparse.urljoin(API_ROOT, uri), data=json.dumps(data), params={'access_token': access_token})

#    client = Github(access_token)
#    repo = client.get_user().get_repo(request.GET['repo'])
#    try:
#        repo.create_hook(name='web', config=dict(url=urlparse.urljoin(SERVER, '/payload/'), content_type='json'), events=['push', 'pull_request'], active=True)
#    except Exception as e:
#        print e
    obj, _ = Repo.objects.get_or_create(repo_id=repo['id'], name=repo['name'])
    obj.enable = not obj.enable
    obj.save()
    return HttpResponseRedirect('/profile')


#@login_required
def repo(request, repo):
    """repo page
    """
    # show last build console, build history

    hooks = Payload.objects.filter(repo=repo)
    hooks.reverse()
    for h in hooks:
        h.pretty = json.dumps(json.loads(h.payload), indent=2)

    J = jenkins.get_server_instance()
    r = J[settings.JENKINS_JOB].get_last_build().get_console()
 
    return render(request, 'core/repo.html', locals())


def badge(request, repo, branch):
    """get status from db by repo, branch
    """
    try:
        badge = Badge.objects.get(repo=repo, branch=branch)
    except ObjectDoesNotExist:
        status = 'UNKNOW'
    else:
        status = badge.status
    ref = {'FAILURE': ('failing', 'red'), 'SUCCESS': ('success', 'brightgreen'), 'UNKNOW': ('unkonw', 'lightgrey')}
    return HttpResponseRedirect(BADGE_URL % ref[status])


def builds(request, repo, build_id):
    """get build console
    """
    status = {}

    def realtime_console(t, build):
        s = ''

        building = build.is_running()
        # get build console when job is finished
        if not building:
            status['status'] = build.get_status()
            print 'res====:', status
            yield t.render(Context({'console': build.get_console()}))

        else:
            # get build console when job is running
            while building:
                building = build.is_running()
                console = build.get_console()
                result = build.get_status()
                print '-'*80
                print console
                news = console.strip(s)
                print 'news'+'-'*80
                print news
                s = console
                if news:
                    yield t.render(Context({'console': news}))
                print '-'*80

            status['status'] = result


    J = jenkins.get_server_instance()
    build = J[settings.JENKINS_JOB].get_build(int(build_id))

    print 'running :', build.is_running()
    t = loader.get_template('core/build.html')

    console = realtime_console(t, build)

    payload = Payload.objects.get(repo=repo, build_id=build_id)
    badge = Badge.objects.get_or_create(repo=repo, branch=payload.branch)

    print 'status, ', status
    if status.get('status'):
        badge.status = status['status']
        badge.save()
   
    return StreamingHttpResponse(console)


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


def get_repos(access_token):
    headers = {'Accept': 'application/json'}

    params = {'access_token': access_token, 'type': 'owner', 'sort': 'updated'}
    # List repositories for the authenticated user.
    repos = requests.get('https://api.github.com/user/repos', params=params, headers=headers)

    # List repositories for the authenticated user.
    repos = repos.json()
    for repo in repos:
        try:
            repo_id = repo['id']
            r = Repo.objects.get(repo_id=repo_id)
            if r.repo_id == repo_id:
                repo['enable'] = r.enable
        except ObjectDoesNotExist:
            continue
    return repos
