from dataclasses import dataclass, field, astuple, asdict
from typing import Optional, Callable
import json
import logging


@dataclass
class Config:
    db_path: str
    scan_interval_minutes: int
    overwrite_db: bool
    new_job_callback: Optional[str] = None  # Optional if no callback is needed
    log_level: str = field(default="INFO")  # Default to "INFO"

    def __post_init__(self):
        """Validate the configuration after initialization."""
        # Validate log_level
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level not in valid_log_levels:
            raise ValueError(f"Invalid log_level: {self.log_level}. Must be one of {valid_log_levels}.")

        # Validate scan_interval_minutes
        if self.scan_interval_minutes <= 0:
            raise ValueError("scan_interval_minutes must be a positive integer.")

        # Validate db_path
        if not self.db_path:
            raise ValueError("db_path is required and cannot be empty.")

    @classmethod
    def from_json(cls, json_path: str):
        """Load configuration from a JSON file."""
        try:
            with open(json_path, "r") as f:
                config_data = json.load(f)
            return cls(**config_data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Error loading configuration: {e}")

    def to_dict(self):
        """Convert the configuration to a dictionary."""
        return asdict(self)


@dataclass
class JobListing:
    url: str
    job_title: str
    company_name: Optional[str] = None
    contract_type: Optional[str] = None
    role_type: Optional[str] = None
    employment_type: Optional[str] = None
    contact: Optional[str] = None
    closing_date: Optional[str] = None

    def __post_init__(self):
        """Ensure required fields are present."""
        if not self.url or not self.job_title:
            raise ValueError("Job must have at least a URL and a title.")

    def to_dict(self):
        """Convert the Job object to a dictionary."""
        return asdict(self)
    
    def to_tuple(self):
        """Convert the Job object to a tuple."""
        return astuple(self)
    
    def __repr__(self):
        return f"JobListing({self.job_title}, {self.url})"
    
    def __str__(self):
        return f"{self.job_title} at {self.url}"
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create a JobListing object from a dictionary."""
        return cls(**data)
