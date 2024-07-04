import time
from pathlib import Path
from pyroute2 import NSPopen
from subprocess import Popen
from network.network import setup_tc, clear_tc

WEBDRIVER_PATH = './webrtc/driver/chromedriver-linux64/chromedriver'

def webrtctest():
    setup_tc()
    webserver_a = NSPopen('ns1', ['python', '-m', 'http.server'])
    webserver_b = NSPopen('ns4', ['python', '-m', 'http.server'])
    time.sleep(1)
    webdriver_a = NSPopen('ns1', [WEBDRIVER_PATH, '--port=8080', '--allowed-ips', '--verbose', '--log-path=./webrtc/webdriver_a.log'])
    webdriver_b = NSPopen('ns4', [WEBDRIVER_PATH, '--port=8080', '--allowed-ips', '--verbose', '--log-path=./webrtc/webdriver_b.log'])

    npm = Popen(['npm', 'run', 'jest', '--prefix', './webrtc'])
    npm.communicate()

    webdriver_a.terminate()
    webdriver_b.terminate()
    webserver_a.terminate()
    webserver_b.terminate()
    clear_tc()
