from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
import re
from typing import Optional

class LogGuardParser:
    """
    Drain3-based log template extractor.
    Automatically discovers log patterns without manual regex.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        config = TemplateMinerConfig()
        config.load(config_path or "drain3.ini")
        self.miner = TemplateMiner(config=config)
        self._numeric_pattern = re.compile(r'\b\d+\.?\d*\b')
        
    def parse(self, log_message: str) -> dict:
        """
        Parse a raw log message into template + parameters.
        
        Returns:
            {
              "template": "User <*> logged in from <*>",
              "template_id": "a3f8b2",
              "parameters": ["john_doe", "192.168.1.1"],
              "response_time_ms": 145.0  # extracted if present
            }
        """
        result = self.miner.add_log_message(log_message)
        
        if result is None:
            return {
                "template": log_message[:200],
                "template_id": "unknown",
                "parameters": [],
                "response_time_ms": None
            }
        
        template = result["template_mined"]
        
        # Extract response time if pattern like "in 145ms" or "took 145ms"
        response_time = self._extract_response_time(log_message)
        
        return {
            "template": template,
            "template_id": result["cluster_id"],
            "parameters": self._extract_parameters(template, log_message),
            "response_time_ms": response_time
        }

    def _extract_parameters(self, template: str, log_message: str) -> list:
        """Extract placeholder values by aligning Drain3 template with raw message."""
        if not template or "<*>" not in template:
            return []

        escaped = re.escape(template)
        pattern = "^" + escaped.replace(re.escape("<*>"), r"(.+?)") + "$"
        match = re.match(pattern, log_message)
        if not match:
            return []
        return [group.strip() for group in match.groups()]
    
    def _extract_response_time(self, log_message: str) -> Optional[float]:
        """Extract response time in ms from common log patterns."""
        patterns = [
            r'(\d+\.?\d*)\s*ms',
            r'took\s+(\d+\.?\d*)',
            r'duration[=:]\s*(\d+\.?\d*)',
            r'"(?:GET|POST|PUT|DELETE)[^"]*"\s+\d+\s+(\d+)',  # Nginx response time
        ]
        for pattern in patterns:
            match = re.search(pattern, log_message, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    def get_template_vocabulary(self) -> dict:
        """Return all discovered templates — expose this to dashboard."""
        return {
            cluster.cluster_id: cluster.get_template()
            for cluster in self.miner.drain.id_to_cluster.values()
        }
