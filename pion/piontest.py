
import time
import os

from pathlib import Path
from pyroute2 import NSPopen
from network.network import setup_tc, clear_tc


def piontest():
    output_dir = 'pion'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    offer_log = os.path.join(output_dir, 'offer.log')
    offer_err = os.path.join(output_dir, 'offer.err')
    answer_log = os.path.join(output_dir, 'answer.log')
    answer_err = os.path.join(output_dir, 'answer.err')
    with open(answer_log, 'w') as al, open(answer_err, 'w') as ae, open(offer_log, 'w') as ol, open(offer_err, 'w') as oe:
        setup_tc()
        env = os.environ.copy()
        env["PION_LOG_TRACE"] = "sctp,gcc_delay_controller,gcc_loss_controller"
        answer = NSPopen('ns1', [
            './pion/answer/answer',
            '-answer-address', ':8080',
            '-offer-address', '10.3.0.20:8080',
        ], env=env, stdout=al, stderr=ae)
        print('answerer started')
        time.sleep(1)
        offer = NSPopen('ns4', [
            './pion/offer/offer',
            '-answer-address', '10.1.0.10:8080',
            '-offer-address', ':8080',
            '-high',  './pion/offer/high.ivf',
            '-med',  './pion/offer/med.ivf',
            '-low',  './pion/offer/low.ivf',
        ], env=env, stdout=ol, stderr=oe)
        print('offerer started')
        offer.communicate()
        print('offerer finished')
        answer.terminate()
        print('answerer terminated')
        answer.communicate()
        print('done')
        clear_tc()

