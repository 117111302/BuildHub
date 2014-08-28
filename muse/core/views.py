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
from lib import jenkins

from core.models import Payload
from core.models import Badge

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
    print '-'*80
    J = jenkins.get_server_instance()
#    if event == 'push':
#        clone_url = data['repository']['clone_url']
#    if event == 'pull_request':
#        clone_url = data['head']['repo']['clone_url']
    r = J[settings.JENKINS_JOB].invoke(build_params={'data': payload})
    build_id = r.get_build_number()
    webhook = Payload.objects.create(repo=repo, payload=payload, build_id=build_id)
    print r.get_build().get_console()
    print '-'*80
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
    status = {'FAILURE': ('failing', 'red'), 'SUCCESS': ('success', 'brightgreen')}
    url = 'http://img.shields.io/badge/build-%s-%s.svg' % status[badge.status]
    return HttpResponseRedirect(url)


def builds(request, repo, build_id):
    """get build console
    """
    J = jenkins.get_server_instance()
    build = J[settings.JENKINS_JOB].get_build(int(build_id))

    print 'running :', build.is_running()
    from django.http import StreamingHttpResponse
    from django.template import loader, Context
    t = loader.get_template('core/build.html')
    console = realtime_console(t,build)
    print console
    
    t.render(Context({'console': console}))

    return StreamingHttpResponse(console)
    return render(request, 'core/build.html', locals())


def realtime_console(t,build):
    from django.template import loader, Context
    buffer = '*' * 1024

#    yield t.render(Context({'console': buffer}))

    while build.is_running():
        console = build.get_console()
#        yield '<p>x = {}</p>\n'.format(console)
        yield console


from django.http import StreamingHttpResponse
from django.template import Context, Template
t = Template('{{ mydata }} <br />\n')

def gen_rendered():
    for x in range(1,11):
        c = Context({'mydata': x})
        yield t.render(c)

def stream_view(request):
    response = StreamingHttpResponse(gen_rendered())
    return response
