import re
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class LogEntry:
    timestamp: int
    target_rate: int
    unix_timestamp: float = field(init=False)

    @staticmethod
    def parse(logline: str):
        log_pattern = re.compile(
            r'offerer\sTRACE\:\s(\d{2}:\d{2}:\d{2}.\d+).*target-bitrate=(\d+).*'
        )
        match = log_pattern.match(logline)
        if match:
            timestamp = match.group(1)
            target_rate = int(match.group(2))
            return LogEntry(timestamp, target_rate)
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
        return LogEntry(data['timestamp'], data['target_rate'])
