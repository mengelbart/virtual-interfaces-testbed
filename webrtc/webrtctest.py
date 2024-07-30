import time
from pathlib import Path
from pyroute2 import NSPopen
from subprocess import Popen
from network.network import setup_tc, clear_tc

WEBDRIVER_PATH = './webrtc/driver/chromedriver-linux64/chromedriver'

def setup():
    setup_tc()
    webserver_a = NSPopen('ns1', ['python', '-m', 'http.server'])
    webserver_b = NSPopen('ns4', ['python', '-m', 'http.server'])
    time.sleep(1)
    webdriver_a = NSPopen('ns1', [WEBDRIVER_PATH, '--port=8080', '--allowed-ips', '--verbose', '--log-path=./webrtc/webdriver_a.log'])
    webdriver_b = NSPopen('ns4', [WEBDRIVER_PATH, '--port=8080', '--allowed-ips', '--verbose', '--log-path=./webrtc/webdriver_b.log'])
    return [webserver_a, webserver_b, webdriver_a, webdriver_b]

def teardown(ps):
    for p in ps:
        p.terminate()
    clear_tc()

def collect_logs(destination):
    srcdir = './webrtc'
    logfiles = [
        'webdriver_a.log',
        'webdriver_b.log',
        'get_stats_client_0.json',
        'get_stats_client_1.json',
        'media_recording.txt',
    ]
    Path(destination).mkdir(parents=True, exist_ok=True)
    for file in logfiles:
        d = Path(srcdir) / file
        d.rename(Path(destination) / file)

def webrtc_media():
    ps = setup()
    npm = Popen(['npm', 'run', 'jest', '--prefix', './webrtc', '--', '-t', 'basic single'])
    npm.communicate()
    teardown(ps)
    collect_logs('webrtc/media')


def webrtc_media_x_data():
    ps = setup()
    npm = Popen(['npm', 'run', 'jest', '--prefix', './webrtc', '--', '-t', 'basic concurrent'])
    npm.communicate()
    teardown(ps)
    collect_logs('webrtc/media_x_data')