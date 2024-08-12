"""Generate a CSV file with sctp congestion information from a chrome log file.
"""
import argparse
import re
import csv
import sys
import pathlib
from loguru import logger 
from dataclasses import dataclass, asdict, field
from typing import List
from datetime import datetime
from datamodel.chromelog import LogEntry
from datamodel.utils import write_out


def read_in(log_file):
    with open(log_file, "r") as f:
        return f.read()
    
def filter_data(raw_data):
    filtered = [x for x in raw_data.split("\n") if "retransmission_queue" in x]
    return filtered

def parse_data(filtered_data):
    entries = [LogEntry.parse(x) for x in filtered_data]
    return entries


    
def main():
    parser = argparse.ArgumentParser(description="Generate a CSV file with sctp congestion information from a chrome log file.")
    parser.add_argument("log_file", help="The log file to parse.")
    parser.add_argument("output_file", help="The output CSV file.")
    parser.add_argument("--log-level", default="INFO", help="The log level to use.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()
    raw_data = read_in(args.log_file)
    filtered_data = filter_data(raw_data)
    parsed_data = parse_data(filtered_data)
    write_out(parsed_data, args.output_file)

if __name__ == "__main__":
    main()