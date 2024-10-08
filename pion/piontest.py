
from subprocess import TimeoutExpired
import time
import os

from pathlib import Path
from pyroute2 import NSPopen
from network.network import add_delay, add_bandwidth_limit, clear_tc


def piontest(config, name='pion', video=False, data=False, duration=60):
    output_dir = Path(config.output_dir) / name
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    offer_log = os.path.join(output_dir, 'offer.log')
    offer_err = os.path.join(output_dir, 'offer.err')
    answer_log = os.path.join(output_dir, 'answer.log')
    answer_err = os.path.join(output_dir, 'answer.err')
    add_delay()
    add_bandwidth_limit(rate='5mbit')
    tcpdump_answerer = NSPopen(
        'ns1', ['tcpdump', '-s', '200', '-w', 'answerer.pcap'], cwd=output_dir)
    tcpdump_offerer = NSPopen(
        'ns4', ['tcpdump', '-s', '200', '-w', 'offerer.pcap'], cwd=output_dir)
    with open(answer_log, 'w') as al, open(answer_err, 'w') as ae, open(offer_log, 'w') as ol, open(offer_err, 'w') as oe:
        env = os.environ.copy()
        env["PION_LOG_TRACE"] = "offerer,sctp,gcc_delay_controller,gcc_loss_controller"
        answer = NSPopen('ns1', [
            os.path.abspath('./pion/answer/answer'),
            '-answer-address', ':8080',
            '-offer-address', '10.3.0.20:8080',
        ], env=env, stdout=al, stderr=ae, cwd=output_dir)
        print('answerer started')
        time.sleep(1)
        offer_cmd = [
            os.path.abspath('./pion/offer/offer'),
            '-answer-address', '10.1.0.10:8080',
            '-offer-address', ':8080',
            '-high', os.path.abspath('./pion/offer/high.ivf'),
            '-med',  os.path.abspath('./pion/offer/med.ivf'),
            '-low',  os.path.abspath('./pion/offer/low.ivf'),
            '-duration', f'{duration}s',
        ]
        if data:
            offer_cmd.append('-data')
        if video:
            offer_cmd.append('-video')
        offer = NSPopen('ns4', offer_cmd, env=env,
                        stdout=ol, stderr=oe, cwd=output_dir)

        try:
            # give some extra time for setup and teardown
            offer.wait(duration + 10)
            answer.terminate()
            answer.wait(5)
        except TimeoutExpired as e:
            print(
                f'timeout while waiting for processes to exit, kiling offerer and answerer ({e})')
            answer.kill()
            offer.kill()

    tcpdump_answerer.terminate()
    tcpdump_offerer.terminate()
    clear_tc()
