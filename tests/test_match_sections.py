"""Unit tests for match_constraint_to_sections()."""
from datetime import date, time

import pytest

from tests.conftest import match_constraint_to_sections, make_section


@pytest.fixture
def two_sections():
    return [
        make_section("S1", date(2026, 4, 15), time(14, 30), time(16, 0)),
        make_section("S2", date(2026, 4, 16), time(14, 30), time(16, 0)),
    ]


@pytest.fixture
def four_sections():
    return [
        make_section("S1", date(2026, 4, 15), time(14, 30), time(16, 0)),
        make_section("S2", date(2026, 4, 15), time(16, 15), time(17, 30)),
        make_section("S3", date(2026, 4, 16), time(14, 30), time(16, 0)),
        make_section("S4", date(2026, 4, 16), time(16, 15), time(17, 30)),
    ]


class TestMatchAny:
    def test_any_returns_all(self, two_sections):
        assert match_constraint_to_sections({"type": "any"}, two_sections) == [0, 1]

    def test_unrecognized_returns_all(self, four_sections):
        parsed = {"type": "unrecognized", "raw": "???"}
        assert match_constraint_to_sections(parsed, four_sections) == [0, 1, 2, 3]


class TestMatchExcluded:
    def test_excluded_returns_empty(self, two_sections):
        parsed = {"type": "excluded", "note": "None"}
        assert match_constraint_to_sections(parsed, two_sections) == []


class TestMatchDayOnly:
    def test_matches_correct_day(self, four_sections):
        parsed = {"type": "day_only", "dates": [date(2026, 4, 15)]}
        assert match_constraint_to_sections(parsed, four_sections) == [0, 1]

    def test_no_match_returns_empty(self, four_sections):
        parsed = {"type": "day_only", "dates": [date(2026, 4, 17)]}
        assert match_constraint_to_sections(parsed, four_sections) == []


class TestMatchWindows:
    def test_exact_match_single(self, four_sections):
        parsed = {
            "type": "windows",
            "windows": [(date(2026, 4, 15), time(14, 30), time(16, 0))],
        }
        result = match_constraint_to_sections(parsed, four_sections)
        assert result == [0]

    def test_exact_match_multiple(self, four_sections):
        parsed = {
            "type": "windows",
            "windows": [
                (date(2026, 4, 15), time(14, 30), time(16, 0)),
                (date(2026, 4, 16), time(16, 15), time(17, 30)),
            ],
        }
        result = match_constraint_to_sections(parsed, four_sections)
        assert sorted(result) == [0, 3]

    def test_no_date_match_returns_empty(self, four_sections):
        parsed = {
            "type": "windows",
            "windows": [(date(2026, 4, 17), time(14, 30), time(16, 0))],
        }
        assert match_constraint_to_sections(parsed, four_sections) == []

    def test_fuzzy_overlap(self):
        """A constraint window that overlaps a section should match."""
        sections = [
            make_section("S1", date(2026, 4, 15), time(14, 0), time(16, 0)),
        ]
        parsed = {
            "type": "windows",
            "windows": [(date(2026, 4, 15), time(15, 0), time(17, 0))],
        }
        result = match_constraint_to_sections(parsed, sections)
        assert result == [0]
