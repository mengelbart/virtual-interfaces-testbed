from pathlib import Path

from pyroute2 import netns
from pyroute2 import IPRoute
from pyroute2 import NetNS
from pyroute2.netlink.exceptions import NetlinkError
import subprocess
import os
import signal

NAMESPACES = [
    {
        'name': 'ns1',
        'routes': [
            {
                'dst': '10.2.0.0/24',
                'gateway': '10.1.0.20',
                'if': 'v1p1',
            },
            {
                'dst': '10.3.0.0/24',
                'gateway': '10.1.0.20',
                'if': 'v1p1',
            },
        ],
    },
    {
        'name': 'ns2',
        'routes': [
            {
                'dst': '10.3.0.0/24',
                'gateway': '10.2.0.20',
                'if': 'v3p1',
            },
        ],
    },
    {
        'name': 'ns3',
        'routes': [
            {
                'dst': '10.1.0.0/24',
                'gateway': '10.2.0.10',
                'if': 'v4p1',
            },
        ],
    },
    {
        'name': 'ns4',
        'routes': [
            {
                'dst': '10.1.0.0/24',
                'gateway': '10.3.0.10',
                'if': 'v6p1',
            },
            {
                'dst': '10.2.0.0/24',
                'gateway': '10.3.0.10',
                'if': 'v6p1',
            },
        ],
    },
]

BRIDGES = [
    {
        'name': 'br1',
        'address': '10.1.0.1',
        'mask': 24,
    },
    {
        'name': 'br2',
        'address': '10.2.0.1',
        'mask': 24,
    },
    {
        'name': 'br3',
        'address': '10.3.0.1',
        'mask': 24,
    },
]

DEVICES = [
    {
        'name': 'v1p1',
        'peer': 'v1p2',
        'ns': 'ns1',
        'ip': '10.1.0.10',
        'mask': 24,
        'broadcast': '10.1.0.255',
        'bridge': 'br1',
    },
    {
        'name': 'v2p1',
        'peer': 'v2p2',
        'ns': 'ns2',
        'ip': '10.1.0.20/24',
        'mask': 24,
        'broadcast': '10.1.0.255',
        'bridge': 'br1',
    },
    {
        'name': 'v3p1',
        'peer': 'v3p2',
        'ns': 'ns2',
        'ip': '10.2.0.10/24',
        'mask': 24,
        'broadcast': '10.2.0.255',
        'bridge': 'br2',
    },
    {
        'name': 'v4p1',
        'peer': 'v4p2',
        'ns': 'ns3',
        'ip': '10.2.0.20/24',
        'mask': 24,
        'broadcast': '10.2.0.255',
        'bridge': 'br2',
    },
    {
        'name': 'v5p1',
        'peer': 'v5p2',
        'ns': 'ns3',
        'ip': '10.3.0.10/24',
        'mask': 24,
        'broadcast': '10.3.0.255',
        'bridge': 'br3',
    },
    {
        'name': 'v6p1',
        'peer': 'v6p2',
        'ns': 'ns4',
        'ip': '10.3.0.20/24',
        'mask': 24,
        'broadcast': '10.3.0.255',
        'bridge': 'br3',
    },
]


def create_ns():
    for ns in NAMESPACES:
        try:
            netns.create(ns['name'])
        except Exception as e:
            print(e)


def remove_ns():
    for ns in NAMESPACES:
        try:
            netns.remove(ns['name'])
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f'{e}:', type(e).__name__)


def create_bridge():
    with IPRoute() as ipr:
        for br in BRIDGES:
            try:
                ipr.link('add', ifname=br['name'], kind='bridge')
                dev = ipr.link_lookup(ifname=br['name'])[0]
                ipr.link('set', index=dev, state='up')
                ipr.addr('add', index=dev, address=br['address'],
                         mask=br['mask'])
            except Exception as e:
                print(f'error: {e}, while creating bridge: {br}')


def remove_bridge():
    with IPRoute() as ipr:
        for br in BRIDGES:
            try:
                ipr.link('del', ifname=br['name'])
            except NetlinkError as e:
                if e.code == 19:  # No such device
                    continue
                print(f'{e}:', type(e).__name__)


def create_iface():
    with IPRoute() as ipr:
        for config in DEVICES:
            try:
                ipr.link('add', ifname=config['name'], kind='veth',
                         peer=config['peer'])
                peer = ipr.link_lookup(ifname=config['peer'])[0]
                br = ipr.link_lookup(ifname=config['bridge'])[0]
                ipr.link('set', index=peer, master=br)
                dev = ipr.link_lookup(ifname=config['name'])[0]
                ipr.link('set', index=dev, net_ns_fd=config['ns'])
                ns = NetNS(config['ns'])
                ns.addr('add', index=dev, address=config['ip'],
                        mask=config['mask'], broadcast=config['broadcast'])
                ns.link('set', index=dev, state='up')
                lo = ns.link_lookup(ifname='lo')[0]
                ns.link('set', index=lo, state='up')
                ns.close()
                ipr.link('set', index=peer, state='up')
            except Exception as e:
                print(f'{type(e).__name__}: {e}, config: {config}')


def remove_iface():
    with IPRoute() as ipr:
        for config in DEVICES:
            try:
                devs = ipr.link_lookup(ifname=config['name'])
                peers = ipr.link_lookup(ifname=config['peer'])
                if len(devs) > 0:
                    ipr.link('del', index=devs[0])
                if len(peers) > 0:
                    ipr.link('del', index=peers[0])
            except Exception as e:
                print(f'{e}: ', type(e).__name__)


def create_routes():
    for namespace in NAMESPACES:
        for route in namespace['routes']:
            try:
                ns = NetNS(namespace['name'])
                # iface = ns.link_lookup(ifname=route['if'])[0]
                ns.route('add', dst=route['dst'], gateway=route['gateway'])
                ns.close()
            except Exception as e:
                print(e, namespace, route)


def add_delay(delay_us=10000):
    with NetNS('ns2') as ns:
        dev = ns.link_lookup(ifname='v3p1')[0]
        ns.tc('add', 'netem', index=dev, handle='1:', delay=delay_us)
    with NetNS('ns3') as ns:
        dev = ns.link_lookup(ifname='v4p1')[0]
        ns.tc('add', 'netem', index=dev, handle='1:', delay=delay_us)


def remove_delay():
    with NetNS('ns2') as ns:
        dev = ns.link_lookup(ifname='v3p1')[0]
        ns.tc('del', index=dev, handle='1:')
    with NetNS('ns3') as ns:
        dev = ns.link_lookup(ifname='v4p1')[0]
        ns.tc('del', index=dev, handle='1:')


def add_bandwidth_limit(rate='2mbit', latency='50ms', burst=5000):
    with NetNS('ns2') as ns:
        dev = ns.link_lookup(ifname='v3p1')[0]
        ns.tc('add', 'tbf', index=dev, handle='0:', parent='1:', rate=rate,
              latency=latency, burst=burst)
    with NetNS('ns3') as ns:
        dev = ns.link_lookup(ifname='v4p1')[0]
        ns.tc('add', 'tbf', index=dev, handle='0:', parent='1:', rate=rate,
              latency=latency, burst=burst)


def remove_bandwidth_limit():
    with NetNS('ns2') as ns:
        dev = ns.link_lookup(ifname='v3p1')[0]
        ns.tc('del', index=dev, handle='0:', parent='1:')
    with NetNS('ns3') as ns:
        dev = ns.link_lookup(ifname='v4p1')[0]
        ns.tc('del', index=dev, handle='0:', parent='1:')


PID_FILE = '/tmp/tcpdump.br1.pid'

def create_listener(config):
    pid_file = Path(PID_FILE)
    if pid_file.exists():
        pid = int(Path(PID_FILE).read_text())
        if check_pid_alive(pid):
            print('tcpdump is already running')
    process=subprocess.Popen(["tcpdump", "-i", "br1", "-w", config.pcap_path])
    pid = process.pid
    pid_file.write_text(str(pid))
    
def check_pid_alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def setup_tc():
    add_delay()
    add_bandwidth_limit()


def clear_tc():
    try:
        remove_bandwidth_limit()
    except Exception as e:
        print(e)
    try:
        remove_delay()
    except Exception as e:
        print(e)

def clear_listener():
    if Path(PID_FILE).exists():
        pid = int(Path(PID_FILE).read_text())
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            print('tcpdump is not running')
        Path(PID_FILE).unlink()
    else:
        print('tcpdump is not running')

def clean():
    remove_iface()
    clear_listener()
    remove_bridge()
    remove_ns()


def setup(config):
    create_ns()
    create_bridge()
    create_iface()
    create_listener(config)
    create_routes()
