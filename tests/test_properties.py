"""Property-based tests using Hypothesis.

Key invariants that must always hold regardless of input:
1. No presenter assigned outside their allowed sections
2. Every schedulable presenter is assigned (scheduled + excluded = total)
3. No duplicate assignments
4. Session IDs are positive integers
5. Poster time slots are uniform within a section
"""
from datetime import date, time, datetime
import string

import pandas as pd
import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from tests.conftest import (
    parse_constraint,
    match_constraint_to_sections,
    assign_with_constraints,
    make_section,
    make_df,
)


# -------------------------------------------------------------------
# Strategies
# -------------------------------------------------------------------
CONSTRAINT_TEMPLATES = [
    None,
    "",
    "Either day",
    "Late submission",
    "None (please notify osr@csusb.edu)",
    "Neither day (please notify osr@csusb.edu)",
    "April 15 only",
    "April 16 only",
    "April 15, 2:30 - 4:00 PM",
    "April 15, 4:15 - 5:45 PM",
    "April 16, 2:30 - 4:00 PM",
    "April 16, 4:15 - 5:45 PM",
    "April 15, 10:00 - 11:00 am",
    "April 16, 10:00 - 11:00 am",
    "April 15, 2:30 - 4:00 PM, April 16, 2:30 - 4:00 PM",
]

THEMES = [
    "Behavioral and Social Sciences",
    "Biological and Agricultural Sciences",
    "Engineering and Computer Science",
    "Health Sciences",
    "Humanities",
]

constraint_strategy = st.sampled_from(CONSTRAINT_TEMPLATES)
theme_strategy = st.sampled_from(THEMES)


def build_random_df(rows):
    """Build a DataFrame from a list of (theme, constraint) tuples."""
    data = []
    for i, (theme, constraint) in enumerate(rows):
        data.append({
            "Theme": theme,
            "Title": f"Title {i}",
            "Presenter(s)": f"Presenter {i}",
            "Faculty Mentor": f"Mentor {i}",
            "Availability Constraint": constraint,
        })
    return pd.DataFrame(data)


ORAL_SECTIONS = [
    make_section("Section 1", date(2026, 4, 15), time(14, 30), time(16, 0)),
    make_section("Section 2", date(2026, 4, 15), time(16, 15), time(17, 30)),
    make_section("Section 3", date(2026, 4, 16), time(14, 30), time(16, 0)),
    make_section("Section 4", date(2026, 4, 16), time(16, 15), time(17, 30)),
]

POSTER_SECTIONS = [
    make_section("Poster Section 1", date(2026, 4, 15), time(10, 0), time(11, 0)),
    make_section("Poster Section 2", date(2026, 4, 16), time(10, 0), time(11, 0)),
]


# -------------------------------------------------------------------
# Invariant 1: No presenter outside allowed sections
# -------------------------------------------------------------------
@given(
    rows=st.lists(
        st.tuples(theme_strategy, constraint_strategy),
        min_size=1,
        max_size=50,
    )
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_no_assignment_outside_allowed_sections(rows):
    df = build_random_df(rows)
    sections = POSTER_SECTIONS
    year = 2026

    result_df, excluded, warnings, sid = assign_with_constraints(
        df.copy(), sections, has_constraints=True, mode="poster",
    )

    section_name_to_idx = {s["name"]: i for i, s in enumerate(sections)}

    for _, row in result_df.iterrows():
        if pd.isna(row.get("Section")):
            continue
        constraint = row["Availability Constraint"]
        parsed = parse_constraint(constraint, year)
        allowed = match_constraint_to_sections(parsed, sections)
        if parsed["type"] == "excluded":
            continue
        sec_idx = section_name_to_idx.get(row["Section"])
        assert sec_idx in allowed, (
            f"Presenter '{row['Title']}' assigned to section {row['Section']} "
            f"(idx {sec_idx}) but allowed sections are {allowed}. "
            f"Constraint: '{constraint}'"
        )


# -------------------------------------------------------------------
# Invariant 2: scheduled + excluded = total
# -------------------------------------------------------------------
@given(
    rows=st.lists(
        st.tuples(theme_strategy, constraint_strategy),
        min_size=1,
        max_size=50,
    )
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_total_accounting(rows):
    df = build_random_df(rows)
    sections = ORAL_SECTIONS

    result_df, excluded, warnings, sid = assign_with_constraints(
        df.copy(), sections, has_constraints=True, mode="oral",
        slot_duration=15, max_presentations=4,
    )

    scheduled = result_df[result_df["Section"].notna()]
    assert len(scheduled) + len(excluded) == len(df), (
        f"scheduled={len(scheduled)} + excluded={len(excluded)} != total={len(df)}"
    )


# -------------------------------------------------------------------
# Invariant 3: No duplicate assignments
# -------------------------------------------------------------------
@given(
    rows=st.lists(
        st.tuples(theme_strategy, constraint_strategy),
        min_size=1,
        max_size=50,
    )
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_no_duplicate_assignments(rows):
    df = build_random_df(rows)
    sections = POSTER_SECTIONS

    result_df, excluded, warnings, sid = assign_with_constraints(
        df.copy(), sections, has_constraints=True, mode="poster",
    )

    scheduled = result_df[result_df["Section"].notna()]
    # No row should appear in more than one section
    assert scheduled.index.is_unique


# -------------------------------------------------------------------
# Invariant 4: Session IDs are positive integers
# -------------------------------------------------------------------
@given(
    rows=st.lists(
        st.tuples(theme_strategy, constraint_strategy),
        min_size=1,
        max_size=30,
    )
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_session_ids_positive(rows):
    df = build_random_df(rows)
    sections = ORAL_SECTIONS

    result_df, excluded, warnings, sid = assign_with_constraints(
        df.copy(), sections, has_constraints=True, mode="oral",
        slot_duration=15, max_presentations=4,
    )

    scheduled = result_df[result_df["Section"].notna()]
    for _, row in scheduled.iterrows():
        sid_val = row["Session ID"]
        assert sid_val is not None
        assert isinstance(sid_val, (int, float))
        assert sid_val > 0


# -------------------------------------------------------------------
# Invariant 5: Poster time slots uniform per section
# -------------------------------------------------------------------
@given(
    rows=st.lists(
        st.tuples(theme_strategy, constraint_strategy),
        min_size=1,
        max_size=50,
    )
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_poster_uniform_time_slots(rows):
    df = build_random_df(rows)
    sections = POSTER_SECTIONS

    result_df, excluded, warnings, sid = assign_with_constraints(
        df.copy(), sections, has_constraints=True, mode="poster",
    )

    scheduled = result_df[result_df["Section"].notna()]
    for sec_name in ["Poster Section 1", "Poster Section 2"]:
        sec_rows = scheduled[scheduled["Section"] == sec_name]
        if len(sec_rows) > 0:
            assert sec_rows["Time Slot"].nunique() == 1, (
                f"{sec_name} has {sec_rows['Time Slot'].nunique()} unique time slots, expected 1"
            )
