import csv
from dataclasses import dataclass, asdict, field


def read_csv(args):
    with open(args, "r") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]
    
def write_out(log_entries, file_path: str):
    if not log_entries:
        return
    with open(file_path, mode='w+') as file:
        writer = csv.DictWriter(file, fieldnames=asdict(log_entries[0]).keys())
        writer.writeheader()
        for entry in log_entries:
            writer.writerow(asdict(entry))