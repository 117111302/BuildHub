from pygerrit.ssh import GerritSSHClient
from pygerrit.client import GerritClient


client = GerritSSHClient("tools")


def ls_projects(**kwargs):
    """List projects visible to caller
    """
    client = GerritSSHClient(kwargs['addr'], username=kwargs['user'], port=kwargs['port'])
    client.load_host_keys("/home/nemo/.ssh/%s.id_rsa" % kwargs['key_name'])
    result = client.run_gerrit_command("ls-projects")
    projects_list = result.stdout.read().split('\n')
    return projects_list


def stream_events():
    """Monitor events occurring in real time
    """
    client = GerritClient("nemo-precise.bj.intel.com", username='xuesonggao', port=29418)
    client.start_event_stream()
    event = client.get_event()
    return event.json
