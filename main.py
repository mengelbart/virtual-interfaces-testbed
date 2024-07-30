#!/usr/bin/env python3

import argparse

from network.network import setup, clean, setup_tc, clear_tc
from iperf3test.iperf3test import iperf3test
from webrtc.webrtctest import webrtc_media, webrtc_media_x_data

def iperf3test_cmd(args):
    setup()
    iperf3test()
    clean()


def webrtctest_cmd(args):
    setup()
    webrtc_media()
    clean()

    setup()
    webrtc_media_x_data()
    clean()


def setup_cmd(args):
    setup()


def clean_cmd(args):
    clean()


def setup_tc_cmd(args):
    setup_tc()


def clear_tc_cmd(args):
    clear_tc()


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
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

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

