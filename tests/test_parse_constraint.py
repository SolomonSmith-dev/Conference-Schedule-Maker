"""Unit tests for parse_constraint()."""
from datetime import date, time

import numpy as np
import pandas as pd
import pytest

from tests.conftest import parse_constraint


YEAR = 2026


# -------------------------------------------------------------------
# type: "any" -- unconstrained
# -------------------------------------------------------------------
class TestParseAny:
    @pytest.mark.parametrize("value", [
        None,
        np.nan,
        pd.NA,
        "",
        "   ",
        float("nan"),
    ])
    def test_blank_values(self, value):
        assert parse_constraint(value, YEAR) == {"type": "any"}

    @pytest.mark.parametrize("value", [
        "Either day",
        "either day",
        "EITHER DAY",
    ])
    def test_either_day(self, value):
        assert parse_constraint(value, YEAR) == {"type": "any"}

    @pytest.mark.parametrize("value", [
        "Late submission",
        "Late submission -- moved from Poster",
        "late submission",
    ])
    def test_late_submission(self, value):
        assert parse_constraint(value, YEAR) == {"type": "any"}


# -------------------------------------------------------------------
# type: "excluded"
# -------------------------------------------------------------------
class TestParseExcluded:
    def test_none_with_note(self):
        r = parse_constraint("None (please notify osr@csusb.edu)", YEAR)
        assert r["type"] == "excluded"
        assert "None" in r["note"]

    def test_neither_day(self):
        r = parse_constraint("Neither day (please notify osr@csusb.edu)", YEAR)
        assert r["type"] == "excluded"
        assert "Neither day" in r["note"]

    def test_bare_none(self):
        assert parse_constraint("none", YEAR)["type"] == "excluded"


# -------------------------------------------------------------------
# type: "day_only"
# -------------------------------------------------------------------
class TestParseDayOnly:
    def test_april_15_only(self):
        r = parse_constraint("April 15 only (Dr. Looney)", YEAR)
        assert r["type"] == "day_only"
        assert r["dates"] == [date(YEAR, 4, 15)]

    def test_april_16_only_bare(self):
        r = parse_constraint("April 16 only", YEAR)
        assert r["type"] == "day_only"
        assert r["dates"] == [date(YEAR, 4, 16)]


# -------------------------------------------------------------------
# type: "windows"
# -------------------------------------------------------------------
class TestParseWindows:
    def test_single_window_pm(self):
        r = parse_constraint("April 15, 2:30 - 4:00 PM", YEAR)
        assert r["type"] == "windows"
        assert len(r["windows"]) == 1
        d, s, e = r["windows"][0]
        assert d == date(YEAR, 4, 15)
        assert s == time(14, 30)
        assert e == time(16, 0)

    def test_two_windows(self):
        r = parse_constraint(
            "April 15, 2:30 - 4:00 PM, April 16, 4:15 - 5:45 PM", YEAR
        )
        assert r["type"] == "windows"
        assert len(r["windows"]) == 2

    def test_four_windows(self):
        r = parse_constraint(
            "April 15, 2:30 - 4:00 PM, April 15, 4:15 - 5:45 PM, "
            "April 16, 2:30 - 4:00 PM, April 16, 4:15 - 5:45 PM",
            YEAR,
        )
        assert r["type"] == "windows"
        assert len(r["windows"]) == 4

    def test_lowercase_am(self):
        r = parse_constraint("April 16, 10:00 - 11:00 am", YEAR)
        assert r["type"] == "windows"
        assert r["windows"][0][1] == time(10, 0)
        assert r["windows"][0][2] == time(11, 0)

    def test_uppercase_AM(self):
        r = parse_constraint("April 15, 10:00 - 11:00 AM", YEAR)
        assert r["type"] == "windows"


# -------------------------------------------------------------------
# type: "unrecognized"
# -------------------------------------------------------------------
class TestParseUnrecognized:
    def test_garbage_string(self):
        r = parse_constraint("some garbage string", YEAR)
        assert r["type"] == "unrecognized"
        assert r["raw"] == "some garbage string"

    def test_invalid_date(self):
        r = parse_constraint("April 99, 2:30 - 4:00 PM", YEAR)
        assert r["type"] == "unrecognized"
