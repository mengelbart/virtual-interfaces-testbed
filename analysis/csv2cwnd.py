import argparse
import csv
from datamodel.chromelog import LogEntry
from datamodel.utils import read_csv, write_out
import re
from dataclasses import dataclass, asdict
cwnd_r = re.compile(r'cwnd=(\d+)')

def main():
    parser = argparse.ArgumentParser(description='Convert Chrome log to cwnd')
    parser.add_argument('input', type=str, help='Input CSV file')
    parser.add_argument('output', type=str, help='Output CSV file')
    args = parser.parse_args()
    
    # Read the CSV file
    data = read_csv(args.input)
    data = [LogEntry.from_dict(row) for row in data]
    out = []
    for row in data:
        cwnd = cwnd_r.search(row.details)
        if cwnd:
            entry = asdict(row)
            entry["cwnd"] = int(cwnd.group(1))
            out.append(entry)
            
    if not out:
        print("No cwnd entries found")
        return
    with open(args.output, mode='w+') as file:
        writer = csv.DictWriter(file, fieldnames=out[0].keys())
        writer.writeheader()
        for entry in out:
            writer.writerow(entry)
    
    
if __name__ == '__main__':
    main()