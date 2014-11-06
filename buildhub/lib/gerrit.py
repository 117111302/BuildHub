from pygerrit.ssh import GerritSSHClient
from pygerrit.client import GerritClient
#TODO make this to .ssh/config or use ssh key
#client = GerritSSHClient("otctools.jf.intel.com", username='gaoxuesx', port=29418)
#client.load_host_keys("/home/nemo/.ssh/id_rsa")
#


client = GerritSSHClient("tools")


def ls_projects():
    """List projects visible to caller
    """
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
