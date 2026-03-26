import re
from typing import Optional


class LogNormalizer:
    """
    Normalizes raw log messages before template extraction.
    Removes noise like IPs, timestamps, UUIDs, hex values etc.
    """

    # Common patterns to mask
    PATTERNS = [
        (re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), '<IP>'),
        (re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'), '<UUID>'),
        (re.compile(r'\b0x[0-9a-fA-F]+\b'), '<HEX>'),
        (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '<EMAIL>'),
        (re.compile(r'(?<=[^a-zA-Z])\d+(?=[^a-zA-Z])'), '<NUM>'),
    ]

    def normalize(self, log_message: str) -> str:
        """
        Apply all normalization patterns to a log message.
        
        Args:
            log_message: Raw log string
            
        Returns:
            Normalized log string with variable parts masked
        """
        normalized = log_message.strip()
        for pattern, replacement in self.PATTERNS:
            normalized = pattern.sub(replacement, normalized)
        return normalized

    def extract_severity(self, log_message: str) -> Optional[str]:
        """
        Extract severity level from log message if present.
        """
        severity_pattern = re.compile(
            r'\b(DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|CRITICAL)\b',
            re.IGNORECASE
        )
        match = severity_pattern.search(log_message)
        if match:
            level = match.group(1).upper()
            if level == "WARNING":
                return "WARN"
            if level == "CRITICAL":
                return "FATAL"
            return level
        return None
