import re
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class LogEntry:
    timestamp: int
    cwnd: int
    ssthresh: int
    unix_timestamp: float = field(init=False)

    @staticmethod
    def parse(logline: str):
        log_pattern = re.compile(
            r'sctp\sTRACE\:\s(\d{2}:\d{2}:\d{2}.\d+).*cwnd=(\d+)\sssthresh=(\d+).*'
        )
        match = log_pattern.match(logline)
        if match:
            timestamp = match.group(1)
            cwnd = int(match.group(2))
            ssthresh = int(match.group(3))
            return LogEntry(timestamp, cwnd, ssthresh)
        else:
            raise ValueError("Log line does not match expected format: " + logline)
    
    def __post_init__(self):
        self.unix_timestamp = self.parse_timestamp(self.timestamp)

    @staticmethod
    def parse_timestamp(timestamp: str) -> float:
        dt = datetime.strptime("17:16:02.574043", "%H:%M:%S.%f")
        dt = dt.replace(year=datetime.now().year)
        return dt.timestamp()

    @staticmethod
    def from_dict(data: dict):
        return LogEntry(data['timestamp'], data['cwnd'], data['ssthresh'])
