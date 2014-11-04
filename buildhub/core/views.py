# -*- coding: utf-8 -*-

import json
import requests
import urlparse
from multiprocessing import Process

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm as authentication_form
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from furl import furl
from lib import jenkins
from lib import keygen as ssh_keygen

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


@csrf_exempt
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect("/")
    else:
        form = UserCreationForm()
    return render(request, "core/register.html", {
        'form': form,
    })


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')


@csrf_exempt
def login_view(request):
    """login view
    """
    redirect_to = request.POST.get('next', '/')

    if request.method == "POST":
        form = authentication_form(request, data=request.POST)
        if form.is_valid():

            # Okay, security check complete. Log the user in.
            login(request, form.get_user())

            return HttpResponseRedirect(redirect_to)
    else:
        form = authentication_form(request)

    return render(request, 'core/login.html', {
        'form': form,
    })


@csrf_exempt
def keygen(request):
    """generate SSH key
    """
    SSH_addr = request.POST.get('addr')
    print SSH_addr
    key = ssh_keygen.generate()
    return render(request, 'core/generate.html', {
	'key': key,
    })


def auth(request):
    # get temporary GitHub code...
    session_code = request.GET['code']
    # POST it back to GitHub
    data = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'code': session_code}
    headers = {'Accept': 'application/json'}
    r = requests.post('https://github.com/login/oauth/access_token', data=data, headers=headers)
    print r.json()
    access_token = r.json().get('access_token')
    if not access_token:
	return HttpResponseRedirect('/')
    request.session['access_token'] = access_token
    uri = '/user'
    user_info = requests.get(urlparse.urljoin(API_ROOT, uri), params={'access_token': access_token})
    user_id = user_info.json()['id']
    user_name = user_info.json()['login']
    user, created = User.objects.get_or_create(username=user_name)
    user.set_password('password')
    user.save()
    user = authenticate(username=user_name, password='password')
    login(request, user)

    print request.session.get('access_token')
    return HttpResponseRedirect('/repos/')


def signin(request):
    """signin with Github
    """
    params = {'client_id': CLIENT_ID, 'scope': 'user:email,admin:repo_hook', 'redirect_uri': REDIRECT_URI}
    f = furl(OAUTH_URL)
    f.add(params)
    response = HttpResponseRedirect(f.url)
    return response


@login_required
def repos(request):
    """oauth callback
    """
    # get user info, set cookie, save user into db
    # if repo has hook?
    access_token = request.session.get('access_token')
    print 'access_token:', access_token

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
                repo['hook_id'] = r.hook_id
        except ObjectDoesNotExist:
            continue
    # List public and private organizations for the authenticated user.
#    orgs = user.get_orgs()

    content = {'repos': repos, 'orgs': orgs}
    return render(request, 'core/repos.html', content)


@login_required
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
    if not data.get('repository'):
        return HttpResponse('OK')
    print 'Jenkins job' + '-'*80

    p = Process(target=process_JJ, args=(data, payload))
    p.start()
    p.join()

    return HttpResponse('OK')


def process_JJ(data, payload):
#    if event == 'push':
#        clone_url = data['repository']['clone_url']
#    if event == 'pull_request':
#        clone_url = data['head']['repo']['clone_url']

    # FIXME build id is not sync
    J = jenkins.get_server_instance()
    r = J[settings.JENKINS_JOB].invoke(build_params={'data': payload})
    start = timezone.now()
    while True:
        status = r.is_queued_or_running()
        print 'is running', status
        build_id = r.get_build_number()
        if not status:
            build_id = r.get_build_number()
            break
    print 'build_id: ', build_id

    branch = data['ref']
    repo_name = data['repository']['full_name']
    repo_id = data['repository']['id']
    message = data['head_commit']['message']
    commit = data['head_commit']['id']
    committer = data['head_commit']['committer']['name']
    timestamp = data['head_commit']['timestamp']

    payload, created = Payload.objects.get_or_create(repo_id=repo_id, commit=commit)
    payload.name = repo_name
    payload.committer = committer
    payload.message = message
    payload.build_id = build_id
    payload.build_job = settings.JENKINS_JOB
    payload.branch = branch
    payload.start = start
    payload.end = timezone.now()
    payload.save()

    print '-'*80
    # FIXME GitHub will time out, can we use subprocess to get build status, and set status to badge?
    #while r.get_build().is_running():
    #    print 'job status: ', r.get_build().is_running()
    #    status = r.get_build().get_status()
    Badge.objects.get_or_create(repo=repo_name, branch=branch)

@login_required
def create_hook(request):
    """create webhook
    """
    # add enable button, if disable, do not recive event

    access_token = request.session['access_token']

    repo_id = request.GET['repo_id']
    repo_name = request.GET['repo']

    data = dict(name='web',
                events=['push'],
                active=True,
                config=dict(url=urlparse.urljoin(SERVER, '/payload/'),
                    content_type='json')
                )
    uri = '/repos/%s/hooks' % (repo_name)
    hook = requests.post(urlparse.urljoin(API_ROOT, uri), data=json.dumps(data), params={'access_token': access_token})
    # FIXME Hook is already existed.
    print hook.status_code
    hook = hook.json()
    print hook
#    client = Github(access_token)
#    repo = client.get_user().get_repo(request.GET['repo'])
#    try:
#        repo.create_hook(name='web', config=dict(url=urlparse.urljoin(SERVER, '/payload/'), content_type='json'), events=['push', 'pull_request'], active=True)
#    except Exception as e:
#        print e
    obj, _ = Repo.objects.get_or_create(repo_id=repo_id)
    obj.name = repo_name
    obj.hook_id = hook['id']
    obj.enable = hook['active']
    obj.save()
    return HttpResponseRedirect('/repos/')


@login_required
def edit_hook(request):
    """edit webhook
    """

    access_token = request.session['access_token']

    repo_id = request.GET['repo_id']
    repo_name = request.GET['repo']

    obj = Repo.objects.get(repo_id=repo_id)

    data = dict(active=not obj.enable,)
    uri = '/repos/%s/hooks/%s' % (repo_name, request.GET['hook_id'])
    hook = requests.patch(urlparse.urljoin(API_ROOT, uri), data=json.dumps(data), params={'access_token': access_token})
    hook = hook.json()
    print hook
    obj.enable = hook['active']

#    client = Github(access_token)
#    repo = client.get_user().get_repo(request.GET['repo'])
#    try:
#        repo.create_hook(name='web', config=dict(url=urlparse.urljoin(SERVER, '/payload/'), content_type='json'), events=['push', 'pull_request'], active=True)
#    except Exception as e:
#        print e

    obj.save()
    return HttpResponseRedirect('/repos/')


@login_required
def repo(request, repo):
    """show last build console and build history
    """
    payloads = Payload.objects.filter(name=repo).order_by('-id')
    current = payloads[0] if payloads else {}
    if current:
        J = jenkins.get_server_instance()
        console = J[current.build_job].get_build(int(current.build_id)).get_console()

    return render(request, 'core/repo.html', locals())


@login_required
def builds(request, repo):
    """show build history
    """
    builds = Payload.objects.filter(name=repo).order_by('-id')
    for build in builds:
        build.message = build.message.strip().splitlines()[0]
    return render(request, 'core/repo.html', locals())


@login_required
def get_build(request, repo, build_id):
    """get specific build information
    """
    J = jenkins.get_server_instance()
    try:
        current = Payload.objects.get(name=repo, build_id=build_id)
    except Payload.DoesNotExist:
        current = {}
    console = J[current.build_job].get_build(int(build_id)).get_console()
    return render(request, 'core/repo.html', locals())


def badge(request, repo, branch):
    """get status from db by repo, branch
    """
    try:
        badge = Badge.objects.get(repo=repo, branch=branch)
    except Badge.DoesNotExist:
        status = 'UNKNOW'
    else:
        status = badge.status
    ref = {'FAILURE': ('failing', 'red'), 'SUCCESS': ('success', 'brightgreen'), 'UNKNOW': ('unkonw', 'lightgrey')}
    return HttpResponseRedirect(BADGE_URL % ref[status])


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

