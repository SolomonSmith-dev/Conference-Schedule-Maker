"""Shared fixtures and Streamlit mock for testing scheduling functions."""
import sys
import types
import unittest.mock
from datetime import datetime, date, time
from contextlib import contextmanager

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Streamlit mock -- must happen before any `from app import ...`
# ---------------------------------------------------------------------------
_st_mock = unittest.mock.MagicMock()
# st.tabs() returns a list of context managers matching the number of tab names
_st_mock.tabs = lambda names: [unittest.mock.MagicMock() for _ in names]
# st.columns() returns a list of context managers
_st_mock.columns = lambda spec: [unittest.mock.MagicMock() for _ in (spec if isinstance(spec, list) else range(spec))]
# st.file_uploader must return None so `if uploaded_file:` blocks are skipped
_st_mock.file_uploader = lambda *a, **kw: None
sys.modules["streamlit"] = _st_mock

# Now safe to import
from app import (  # noqa: E402
    parse_constraint,
    match_constraint_to_sections,
    assign_with_constraints,
    _assign_no_constraints,
    build_xlsx,
    make_sheet_name,
)


# ---------------------------------------------------------------------------
# Section factory
# ---------------------------------------------------------------------------
def make_section(name, d, start, end):
    """Build a section dict matching the structure expected by all functions."""
    start_dt = datetime.combine(d, start)
    end_dt = datetime.combine(d, end)
    return {
        "name": name,
        "sheet_name": make_sheet_name(d, start, end),
        "date": d,
        "start": start,
        "end": end,
        "start_dt": start_dt,
        "end_dt": end_dt,
    }


# ---------------------------------------------------------------------------
# Real MOTM section fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def motm_oral_sections():
    return [
        make_section("Section 1", date(2026, 4, 15), time(14, 30), time(16, 0)),
        make_section("Section 2", date(2026, 4, 15), time(16, 15), time(17, 30)),
        make_section("Section 3", date(2026, 4, 16), time(14, 30), time(16, 0)),
        make_section("Section 4", date(2026, 4, 16), time(16, 15), time(17, 30)),
    ]


@pytest.fixture
def motm_poster_sections():
    return [
        make_section("Poster Section 1", date(2026, 4, 15), time(10, 0), time(11, 0)),
        make_section("Poster Section 2", date(2026, 4, 16), time(10, 0), time(11, 0)),
    ]


# ---------------------------------------------------------------------------
# DataFrame factory
# ---------------------------------------------------------------------------
def make_df(rows, include_constraint=True):
    """Build a test DataFrame.

    rows: list of dicts, each with at least "Theme".
    Optional keys: "Title", "Presenter(s)", "Faculty Mentor", "Availability Constraint".
    Missing keys are filled with defaults.
    """
    data = []
    for i, r in enumerate(rows):
        entry = {
            "Theme": r.get("Theme", "General"),
            "Title": r.get("Title", f"Presentation {i+1}"),
            "Presenter(s)": r.get("Presenter(s)", f"Presenter {i+1}"),
            "Faculty Mentor": r.get("Faculty Mentor", f"Mentor {i+1}"),
        }
        if include_constraint:
            entry["Availability Constraint"] = r.get("Availability Constraint", None)
        data.append(entry)
    return pd.DataFrame(data)


def make_simple_df(n, themes=None, constraints=None, include_constraint=True):
    """Quick helper: n rows, cycling through themes and constraints."""
    themes = themes or ["Theme A", "Theme B", "Theme C"]
    rows = []
    for i in range(n):
        row = {"Theme": themes[i % len(themes)]}
        if constraints and include_constraint:
            row["Availability Constraint"] = constraints[i % len(constraints)]
        rows.append(row)
    return make_df(rows, include_constraint=include_constraint)
