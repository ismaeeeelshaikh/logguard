import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parsers.drain3_parser import LogGuardParser


@pytest.fixture
def parser():
    """Create a fresh LogGuardParser instance for each test."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'drain3.ini')
    return LogGuardParser(config_path=config_path)


class TestDrain3Parser:
    """Tests for Drain3-based log template extraction."""

    def test_basic_parse_returns_dict(self, parser):
        result = parser.parse("User john logged in from 192.168.1.1")
        assert isinstance(result, dict)
        assert "template" in result
        assert "template_id" in result
        assert "parameters" in result
        assert "response_time_ms" in result

    def test_parse_nginx_log(self, parser):
        log = '10.0.0.1 - - [19/Mar/2026:10:00:00 +0000] "GET /api/v1/users 200 145ms"'
        result = parser.parse(log)
        assert result["template"] is not None
        assert result["template_id"] is not None

    def test_parse_error_log(self, parser):
        log = "ERROR: Database connection refused after 5 retries"
        result = parser.parse(log)
        assert result["template"] is not None

    def test_parse_syslog(self, parser):
        log = "Mar 19 10:00:00 web-01 sshd[12345]: Accepted publickey for user from 10.0.0.5"
        result = parser.parse(log)
        assert result["template"] is not None

    def test_extract_response_time_ms(self, parser):
        result = parser.parse("GET /api/users completed in 245ms")
        assert result["response_time_ms"] == 245.0

    def test_extract_response_time_took(self, parser):
        result = parser.parse("Request took 1500 to complete")
        assert result["response_time_ms"] == 1500.0

    def test_extract_response_time_duration(self, parser):
        result = parser.parse("duration=320 for request /api/data")
        assert result["response_time_ms"] == 320.0

    def test_no_response_time(self, parser):
        result = parser.parse("User john logged in successfully")
        assert result["response_time_ms"] is None

    def test_template_consistency(self, parser):
        """Same pattern should produce same template after training."""
        parser.parse("User alice logged in from 10.0.0.1")
        parser.parse("User bob logged in from 10.0.0.2")
        result = parser.parse("User charlie logged in from 10.0.0.3")
        assert result["template"] is not None
        assert result["template_id"] is not None

    def test_multiple_log_formats(self, parser):
        """Test that parser handles various log formats."""
        logs = [
            "INFO: Health check passed for service api-gateway",
            "WARN: Disk usage at 85% on /data",
            "ERROR: Authentication failed for user admin from 10.0.0.99",
            "FATAL: Out of memory - killing process 4567",
            "DEBUG: Cache hit for key session_abc: 5ms",
            "GET /api/v1/orders 200 89ms",
            "POST /api/v1/users 201 234ms",
            "Database connection pool: 45/100 connections active",
            "Container abc123 started successfully",
            "Kubernetes pod web-01-xyz restarted 3 times",
        ]
        for log in logs:
            result = parser.parse(log)
            assert result["template"] is not None, f"Failed to parse: {log}"

    def test_get_template_vocabulary(self, parser):
        """After parsing logs, vocabulary should contain discovered templates."""
        parser.parse("User alice logged in from 10.0.0.1")
        parser.parse("ERROR: Connection timeout after 5000ms")
        vocab = parser.get_template_vocabulary()
        assert isinstance(vocab, dict)
        assert len(vocab) > 0

    def test_empty_log_message(self, parser):
        result = parser.parse("")
        assert result["template"] is not None

    def test_very_long_log_message(self, parser):
        long_log = "A" * 5000
        result = parser.parse(long_log)
        assert result["template"] is not None
