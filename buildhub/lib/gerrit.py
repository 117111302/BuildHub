from pygerrit.ssh import GerritSSHClient
from pygerrit.client import GerritClient


client = GerritSSHClient("tools")


def gerrit_version(**kwargs):
    """Test Gerrit server connection
    """
    client = GerritSSHClient(kwargs['addr'], username=kwargs['user'], port=int(kwargs['port']))
    client.load_host_keys("/home/nemo/.ssh/%s.id_rsa" % kwargs['key'])
    result = client.run_gerrit_command("version")
    return result.stdout.read()


def ls_projects(**kwargs):
    """List projects visible to caller
    """
    client = GerritSSHClient(kwargs['addr'], username=kwargs['user'], port=kwargs['port'])
    client.load_host_keys("/home/nemo/.ssh/%s.id_rsa" % kwargs['key'])
    result = client.run_gerrit_command("ls-projects")
    projects_list = result.stdout.read().split('\n')
    return projects_list
