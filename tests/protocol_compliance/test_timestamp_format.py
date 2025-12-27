"""
Protocol compliance tests for timestamp format.

Tests that all timestamps follow ISO 8601 format with UTC timezone (Z suffix).
Format: YYYY-MM-DDTHH:MM:SSZ
"""

import re
from datetime import datetime

import pytest

from league_sdk.utils import generate_timestamp, validate_timestamp


@pytest.mark.protocol
class TestTimestampFormat:
    """Test timestamp format compliance with ISO 8601 UTC."""

    def test_timestamp_format_matches_iso8601(self):
        """Test that generated timestamps match ISO 8601 format."""
        timestamp = generate_timestamp()

        # ISO 8601 format: 2025-12-25T14:30:00Z
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        assert re.match(pattern, timestamp), f"Timestamp {timestamp} doesn't match ISO 8601 format"

    def test_timestamp_has_utc_timezone(self):
        """Test that timestamps use UTC timezone (Z suffix)."""
        timestamp = generate_timestamp()

        assert timestamp.endswith("Z"), f"Timestamp {timestamp} must end with 'Z' for UTC"

    def test_timestamp_components_valid(self):
        """Test that timestamp components are valid dates/times."""
        timestamp = generate_timestamp()

        # Remove Z suffix and parse
        timestamp_str = timestamp.rstrip("Z")

        try:
            dt = datetime.fromisoformat(timestamp_str)
            assert dt.year >= 2024
            assert 1 <= dt.month <= 12
            assert 1 <= dt.day <= 31
            assert 0 <= dt.hour <= 23
            assert 0 <= dt.minute <= 59
            assert 0 <= dt.second <= 59
        except ValueError as e:
            pytest.fail(f"Invalid timestamp components: {e}")

    def test_valid_timestamp_validation(self):
        """Test that valid timestamps pass validation."""
        valid_timestamps = [
            "2025-12-25T14:30:00Z",
            "2024-01-01T00:00:00Z",
            "2025-06-15T23:59:59Z",
            "2025-12-31T12:00:00Z",
        ]

        for ts in valid_timestamps:
            assert validate_timestamp(ts) is True, f"{ts} should be valid"

    def test_invalid_timestamp_format_rejected(self):
        """Test that invalid timestamp formats are rejected."""
        invalid_timestamps = [
            "2025-12-25",  # Missing time
            "2025-12-25 14:30:00",  # Space instead of T
            "2025-12-25T14:30:00",  # Missing Z
            "2025-12-25T14:30:00+00:00",  # +00:00 instead of Z
            "25-12-2025T14:30:00Z",  # Wrong date format
            "2025/12/25T14:30:00Z",  # Wrong delimiter
            "2025-12-25T14:30Z",  # Missing seconds
            "not-a-timestamp",  # Complete nonsense
        ]

        for ts in invalid_timestamps:
            assert validate_timestamp(ts) is False, f"{ts} should be invalid"

    def test_timestamp_year_format(self):
        """Test that year is 4 digits."""
        timestamp = generate_timestamp()

        year_part = timestamp.split("-")[0]
        assert len(year_part) == 4, "Year must be 4 digits"
        assert year_part.isdigit(), "Year must be numeric"

    def test_timestamp_month_format(self):
        """Test that month is 2 digits (01-12)."""
        timestamp = generate_timestamp()

        month_part = timestamp.split("-")[1]
        assert len(month_part) == 2, "Month must be 2 digits"
        assert month_part.isdigit(), "Month must be numeric"
        assert 1 <= int(month_part) <= 12, "Month must be 01-12"

    def test_timestamp_day_format(self):
        """Test that day is 2 digits (01-31)."""
        timestamp = generate_timestamp()

        day_part = timestamp.split("-")[2].split("T")[0]
        assert len(day_part) == 2, "Day must be 2 digits"
        assert day_part.isdigit(), "Day must be numeric"
        assert 1 <= int(day_part) <= 31, "Day must be 01-31"

    def test_timestamp_hour_format(self):
        """Test that hour is 2 digits (00-23)."""
        timestamp = generate_timestamp()

        hour_part = timestamp.split("T")[1].split(":")[0]
        assert len(hour_part) == 2, "Hour must be 2 digits"
        assert hour_part.isdigit(), "Hour must be numeric"
        assert 0 <= int(hour_part) <= 23, "Hour must be 00-23"

    def test_timestamp_minute_format(self):
        """Test that minute is 2 digits (00-59)."""
        timestamp = generate_timestamp()

        minute_part = timestamp.split(":")[1]
        assert len(minute_part) == 2, "Minute must be 2 digits"
        assert minute_part.isdigit(), "Minute must be numeric"
        assert 0 <= int(minute_part) <= 59, "Minute must be 00-59"

    def test_timestamp_second_format(self):
        """Test that second is 2 digits (00-59)."""
        timestamp = generate_timestamp()

        second_part = timestamp.split(":")[2].rstrip("Z")
        assert len(second_part) == 2, "Second must be 2 digits"
        assert second_part.isdigit(), "Second must be numeric"
        assert 0 <= int(second_part) <= 59, "Second must be 00-59"

    def test_timestamp_no_milliseconds(self):
        """Test that timestamps don't include milliseconds."""
        timestamp = generate_timestamp()

        # Should not contain decimal point
        assert "." not in timestamp, "Timestamp should not include milliseconds"

    def test_timestamp_t_separator(self):
        """Test that date and time are separated by 'T'."""
        timestamp = generate_timestamp()

        assert "T" in timestamp, "Timestamp must have 'T' separator between date and time"
        parts = timestamp.split("T")
        assert len(parts) == 2, "Timestamp must have exactly one 'T' separator"

    def test_timestamp_consistency(self):
        """Test that timestamps generated in sequence are valid."""
        timestamps = [generate_timestamp() for _ in range(10)]

        for ts in timestamps:
            assert validate_timestamp(ts) is True, f"Generated timestamp {ts} is invalid"

    def test_invalid_date_rejected(self):
        """Test that invalid dates (like Feb 30) are rejected."""
        invalid_dates = [
            "2025-02-30T12:00:00Z",  # Feb 30 doesn't exist
            "2025-13-01T12:00:00Z",  # Month 13 doesn't exist
            "2025-00-15T12:00:00Z",  # Month 00 doesn't exist
            "2025-12-32T12:00:00Z",  # Dec 32 doesn't exist
        ]

        for ts in invalid_dates:
            assert validate_timestamp(ts) is False, f"{ts} should be rejected as invalid"

    def test_invalid_time_rejected(self):
        """Test that invalid times are rejected."""
        invalid_times = [
            "2025-12-25T24:00:00Z",  # Hour 24 doesn't exist (should be 00)
            "2025-12-25T12:60:00Z",  # Minute 60 doesn't exist
            "2025-12-25T12:30:60Z",  # Second 60 doesn't exist
            "2025-12-25T25:00:00Z",  # Hour 25 doesn't exist
        ]

        for ts in invalid_times:
            assert validate_timestamp(ts) is False, f"{ts} should be rejected as invalid"
