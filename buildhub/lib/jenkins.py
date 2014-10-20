from django.conf import settings
from jenkinsapi.jenkins import Jenkins

def get_server_instance():
    server = Jenkins(settings.JENKINS_URL, settings.JENKINS_USER, settings.JENKINS_PASS)
    return server
