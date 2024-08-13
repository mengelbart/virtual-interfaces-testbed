#!/usr/bin/env python3

import argparse

from network.network import setup, clean, setup_tc, clear_tc
from iperf3test.iperf3test import iperf3test
from webrtc.webrtctest import webrtc_media, webrtc_media_x_data
import configuration
from pion.piontest import piontest

def iperf3test_cmd(args, config):
    setup(config)
    iperf3test()
    clean()


def webrtctest_cmd(args, config):
    setup(config)
    webrtc_media(config)
    clean()

    setup(config)
    webrtc_media_x_data(config)
    clean()


def setup_cmd(args, config):
    setup(config)


def piontest_cmd(args):
    setup()
    piontest()
    clean()


def clean_cmd(args, config):
    clean()


def setup_tc_cmd(args, config):
    setup_tc()


def clear_tc_cmd(args, config):
    clear_tc()


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("--config", type=str,action="append", help="path to config file")
    
    
    subparsers = parser.add_subparsers(help='sub-command help', required=True)

    clean = subparsers.add_parser('clean', help='clean up virtual interaces and namespaces')
    clean.set_defaults(func=clean_cmd)

    setup = subparsers.add_parser('setup', help='setup virtual interfaces and namespaces')
    setup.set_defaults(func=setup_cmd)

    setup_tc = subparsers.add_parser('tc', help='add netem delay qdisc')
    setup_tc.set_defaults(func=setup_tc_cmd)

    clean_tc = subparsers.add_parser('clear', help='remove any tc qdiscs')
    clean_tc.set_defaults(func=clear_tc_cmd)

    iperf3test = subparsers.add_parser('iperf3', help='run iperf3 test')
    iperf3test.set_defaults(func=iperf3test_cmd)

    webrtctest = subparsers.add_parser('webrtc', help='run webrtc test')
    webrtctest.set_defaults(func=webrtctest_cmd)

    piontest = subparsers.add_parser('pion', help='run pion test')
    piontest.set_defaults(func=piontest_cmd)

    args = parser.parse_args()
    config = configuration.configure(args.config)
    args.func(args, config)


if __name__ == "__main__":
    main()

