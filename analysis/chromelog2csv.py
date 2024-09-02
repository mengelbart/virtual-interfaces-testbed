#!/usr/bin/env python3


"""Generate a CSV file with sctp congestion information from a chrome or pion log file.
"""
import argparse
from datamodel.chromelog import LogEntry as ChromeLogEntry
from datamodel.pion_sctp import LogEntry as PionSCTPLogEntry
from datamodel.pion_offerer import LogEntry as PionOffererLogEntry
from datamodel.utils import write_out


formats = {
    "chrome": {
        "filter": "retransmission_queue",
        "parser": ChromeLogEntry.parse,
    },
    "pion_sctp": {
        "filter": "cwnd=",
        "parser": PionSCTPLogEntry.parse,
    },
    "pion_offerer": {
        "filter": "offerer TRACE",
        "parser": PionOffererLogEntry.parse,
    },
}


def read_in(log_file):
    with open(log_file, "r") as f:
        return f.read()
    
def filter_data(raw_data, filter):
    filtered = [x for x in raw_data.split("\n") if filter in x]
    return filtered

def parse_data(filtered_data, parser):
    entries = [parser(x) for x in filtered_data]
    return entries


    
def main():
    parser = argparse.ArgumentParser(description="Generate a CSV file with sctp congestion information from a chrome log file.")
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("log_file", help="The log file to parse.")
    parser.add_argument("output_file", help="The output CSV file.")
    parser.add_argument("--format", default="chrome", help="The log format to parse (chrome or pion).")
    parser.add_argument("--log-level", default="INFO", help="The log level to use.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")

    args = parser.parse_args()
    raw_data = read_in(args.log_file)
    filtered_data = filter_data(raw_data, formats[args.format]['filter'])
    parsed_data = parse_data(filtered_data, formats[args.format]['parser'])
    write_out(parsed_data, args.output_file)

if __name__ == "__main__":
    main()