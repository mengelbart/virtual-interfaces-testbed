import os

from pathlib import Path

from pyroute2 import NSPopen

from network.network import setup_tc
from network.network import clear_tc


def iperf3test():
    output_dir = 'iperf3test'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    server_log = os.path.join(output_dir, 'server.json')
    client_log = os.path.join(output_dir, 'client.json')

    setup_tc()
    server = NSPopen('ns1', [
        'iperf3',
        '-s',
        '-J',
        '--logfile', server_log,
    ])
    print('server process started')
    client = NSPopen('ns4', [
        'iperf3',
        '-c', '10.1.0.10',
        '-J',
        '--logfile', client_log,
        '-i', '0.1',
        '-C', 'cubic',
    ])
    print('client process started')
    client.communicate()
    print('client process finished')
    server.terminate()
    print('server process terminated')
    server.communicate()
    print('done')
    clear_tc()

