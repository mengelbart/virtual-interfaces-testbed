import time
from pathlib import Path
from pyroute2 import NSPopen
from subprocess import Popen
from network.network import setup_tc, clear_tc
import os
import shutil

WEBDRIVER_PATH = './webrtc/driver/chromedriver-linux64/chromedriver'


def setup(config):
    setup_tc()
    webserver_a = NSPopen('ns1', ['python', '-m', 'http.server'])
    webserver_b = NSPopen('ns4', ['python', '-m', 'http.server'])
    time.sleep(1)
    webdriver_a = NSPopen('ns1', [WEBDRIVER_PATH, '--port=8080',
                          '--allowed-ips', '--verbose', '--log-path=./webrtc/webdriver_a.log'])
    webdriver_b = NSPopen('ns4', [WEBDRIVER_PATH, '--port=8080',
                          '--allowed-ips', '--verbose', '--log-path=./webrtc/webdriver_b.log'])
    return [webserver_a, webserver_b, webdriver_a, webdriver_b]


def teardown(ps):
    for p in ps:
        p.terminate()
    clear_tc()


def collect_logs(destination, config):
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
    if config.collect_chrome_logs:
        for key, value in config._collect_chrome_logs_from.items():
            d = Path(value)
            shutil.copy(d, (Path(destination) / key))


def webrtc_media(config):
    webrtc(config, data=False)


def webrtc_media_x_data(config):
    webrtc(config, data=True)


def webrtc(config, data=False):
    ps = setup(config)
    env = os.environ.copy()
    data_a = Path(config.data_dir_offset) / config.data_a
    data_b = Path(config.data_dir_offset) / config.data_b
    if data_a.exists():
        shutil.rmtree(data_a)
    if data_b.exists():
        shutil.rmtree(data_b)
    env['USER_DATA_DIR_A'] = str(data_a)
    env['USER_DATA_DIR_B'] = str(data_b)
    config._collect_chrome_logs_from[f'chromelog_a.{'webrtc_media_x_data' if data else 'webrtc_media'}.log'] = data_a / \
        "chrome_debug.log"
    config._collect_chrome_logs_from[f'chromelog_b.{'webrtc_media_x_data' if data else 'webrtc_media'}.log'] = data_b / \
        "chrome_debug.log"
    if data:
        npm = Popen(['npm', 'run', 'jest', '--prefix', './webrtc',
                    '--', '-t', 'basic concurrent'], env=env)
    else:
        npm = Popen(['npm', 'run', 'jest', '--prefix', './webrtc',
                    '--', '-t', 'basic single'], env=env)
    npm.communicate()
    teardown(ps)
    collect_logs(f'{'webrtc_media_x_data' if data else 'webrtc_media'}', config)
