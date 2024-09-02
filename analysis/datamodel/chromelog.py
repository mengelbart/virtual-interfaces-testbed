import re
from dataclasses import dataclass, field
from typing import List
from datetime import datetime

@dataclass
class LogEntry:
    process_id: int
    thread_id: int
    timestamp: str
    log_level: str
    file: str
    line_number: int
    message: str
    details: str
    unix_timestamp: float = field(init=False)
    
    @staticmethod
    def parse(logline: str):
        log_pattern = re.compile(
            r'\[(\d+):(\d+):(\d{4}/\d{6}\.\d+):(\w+):([\w\.]+)\((\d+)\)\] (.*?): (.*)'
        )
        match = log_pattern.match(logline)
        if match:
            process_id = int(match.group(1))
            thread_id = int(match.group(2))
            timestamp = match.group(3)
            log_level = match.group(4)
            file = match.group(5)
            line_number = int(match.group(6))
            message = match.group(7)
            details = match.group(8)
            return LogEntry(process_id, thread_id, timestamp, log_level, file, line_number, message, details)
        else:
            raise ValueError("Log line does not match expected format")

    def __post_init__(self):
        # Convert timestamp to Unix timestamp
        self.unix_timestamp = self.parse_timestamp(self.timestamp)

    @staticmethod
    def parse_timestamp(timestamp: str) -> float:
        # Convert the custom timestamp format to Unix timestamp
        dt = datetime.strptime(timestamp, '%m%d/%H%M%S.%f')
        # Assuming the timestamp is in the current year
        dt = dt.replace(year=datetime.now().year)
        return dt.timestamp()

    @staticmethod
    def from_dict(data: dict):
        return LogEntry(data['process_id'], data['thread_id'], data['timestamp'], data['log_level'], data['file'], data['line_number'], data['message'], data['details'])
