from dataclasses import dataclass, field
from omegaconf import OmegaConf
from typing import List, Dict



@dataclass
class ExperimentConfig:
    data_dir_offset: str = "/tmp"
    _used_config_files: list = field(default_factory=list)
    collect_chrome_logs: bool = True
    data_a: str = "data_a"
    data_b: str = "data_b"
    _collect_chrome_logs_from: Dict[str, str] = field(default_factory=dict)
    pcap_path: str = "/tmp/"
    

def configure(config_files: list[str]) -> ExperimentConfig:
    config = OmegaConf.structured(ExperimentConfig)
    if config_files:
        for config_file in config_files:
            config = OmegaConf.merge(config, OmegaConf.load(config_file))
    return config