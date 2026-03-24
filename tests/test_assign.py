"""Integration tests for assign_with_constraints and _assign_no_constraints."""
from datetime import date, time

import pandas as pd
import pytest

from tests.conftest import (
    assign_with_constraints,
    _assign_no_constraints,
    make_section,
    make_df,
    make_simple_df,
)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _two_day_sections():
    return [
        make_section("Section 1", date(2026, 4, 15), time(14, 30), time(16, 0)),
        make_section("Section 2", date(2026, 4, 16), time(14, 30), time(16, 0)),
    ]


# -------------------------------------------------------------------
# No-constraint fallback
# -------------------------------------------------------------------
class TestNoConstraints:
    def test_even_split_oral(self):
        sections = _two_day_sections()
        df = make_simple_df(12, include_constraint=False)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, sections, has_constraints=False, mode="oral",
            slot_duration=15, max_presentations=4,
        )
        scheduled = result_df[result_df["Section"].notna()]
        assert len(scheduled) == 12
        assert excluded.empty
        s1 = scheduled[scheduled["Section"] == "Section 1"]
        s2 = scheduled[scheduled["Section"] == "Section 2"]
        assert len(s1) == 6
        assert len(s2) == 6

    def test_even_split_poster(self):
        sections = _two_day_sections()
        df = make_simple_df(10, include_constraint=False)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, sections, has_constraints=False, mode="poster",
        )
        scheduled = result_df[result_df["Section"].notna()]
        assert len(scheduled) == 10
        assert excluded.empty


# -------------------------------------------------------------------
# Constraint-aware scheduling
# -------------------------------------------------------------------
class TestConstrainedAssignment:
    def test_constrained_land_in_correct_section(self):
        sections = _two_day_sections()
        rows = [
            {"Theme": "A", "Availability Constraint": "April 15, 2:30 - 4:00 PM"},
            {"Theme": "A", "Availability Constraint": "April 15, 2:30 - 4:00 PM"},
            {"Theme": "A", "Availability Constraint": "April 15, 2:30 - 4:00 PM"},
            {"Theme": "B", "Availability Constraint": "April 16, 2:30 - 4:00 PM"},
            {"Theme": "B", "Availability Constraint": "April 16, 2:30 - 4:00 PM"},
            {"Theme": "C"},  # unconstrained
            {"Theme": "C"},
            {"Theme": "C"},
            {"Theme": "D"},
            {"Theme": "D"},
        ]
        df = make_df(rows)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, sections, has_constraints=True, mode="oral",
            slot_duration=15, max_presentations=4,
        )
        scheduled = result_df[result_df["Section"].notna()]
        assert len(scheduled) == 10
        assert excluded.empty

        # Constrained to April 15 must be in Section 1
        for idx in [0, 1, 2]:
            assert result_df.at[idx, "Section"] == "Section 1"
        # Constrained to April 16 must be in Section 2
        for idx in [3, 4]:
            assert result_df.at[idx, "Section"] == "Section 2"

    def test_excluded_presenters_removed(self):
        sections = _two_day_sections()
        rows = [
            {"Theme": "A"},
            {"Theme": "A"},
            {"Theme": "A"},
            {"Theme": "A"},
            {"Theme": "A", "Availability Constraint": "None (please notify osr@csusb.edu)"},
        ]
        df = make_df(rows)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, sections, has_constraints=True, mode="poster",
        )
        scheduled = result_df[result_df["Section"].notna()]
        assert len(scheduled) == 4
        assert len(excluded) == 1

    def test_no_match_constraint_excluded_with_warning(self):
        sections = _two_day_sections()  # April 15 and 16
        rows = [
            {"Theme": "A", "Availability Constraint": "April 17, 2:30 - 4:00 PM"},
            {"Theme": "A"},
        ]
        df = make_df(rows)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, sections, has_constraints=True, mode="oral",
            slot_duration=15, max_presentations=4,
        )
        scheduled = result_df[result_df["Section"].notna()]
        assert len(scheduled) == 1
        assert len(excluded) == 1
        assert any("doesn't match" in w for w in warnings)


# -------------------------------------------------------------------
# Poster mode specifics
# -------------------------------------------------------------------
class TestPosterMode:
    def test_uniform_time_slot_per_section(self):
        sections = _two_day_sections()
        df = make_simple_df(20)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, sections, has_constraints=True, mode="poster",
        )
        scheduled = result_df[result_df["Section"].notna()]
        for sec_name in ["Section 1", "Section 2"]:
            sec_rows = scheduled[scheduled["Section"] == sec_name]
            if len(sec_rows) > 0:
                assert sec_rows["Time Slot"].nunique() == 1


# -------------------------------------------------------------------
# Oral concurrent sessions
# -------------------------------------------------------------------
class TestOralConcurrency:
    def test_shared_time_slots(self):
        """With max_presentations=4, groups of 4 should share a time slot."""
        sections = [make_section("S1", date(2026, 4, 15), time(14, 0), time(16, 0))]
        df = make_simple_df(8, themes=["Theme A"], include_constraint=False)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, sections, has_constraints=False, mode="oral",
            slot_duration=15, max_presentations=4,
        )
        scheduled = result_df[result_df["Section"].notna()]
        assert len(scheduled) == 8
        # 8 presenters / 4 per session = 2 unique time slots
        assert scheduled["Time Slot"].nunique() == 2


# -------------------------------------------------------------------
# Edge cases
# -------------------------------------------------------------------
class TestEdgeCases:
    def test_empty_dataframe(self):
        sections = _two_day_sections()
        df = make_simple_df(0)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, sections, has_constraints=True, mode="poster",
        )
        assert len(result_df) == 0

    def test_single_presentation(self):
        sections = _two_day_sections()
        df = make_simple_df(1)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, sections, has_constraints=True, mode="oral",
            slot_duration=15, max_presentations=4,
        )
        scheduled = result_df[result_df["Section"].notna()]
        assert len(scheduled) == 1

    def test_all_excluded(self):
        sections = _two_day_sections()
        rows = [
            {"Theme": "A", "Availability Constraint": "None"},
            {"Theme": "B", "Availability Constraint": "Neither day"},
            {"Theme": "C", "Availability Constraint": "none"},
        ]
        df = make_df(rows)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, sections, has_constraints=True, mode="poster",
        )
        scheduled = result_df[result_df["Section"].notna()]
        assert len(scheduled) == 0
        assert len(excluded) == 3

    def test_all_constrained_to_one_section(self):
        sections = _two_day_sections()
        rows = [
            {"Theme": "A", "Availability Constraint": "April 15, 2:30 - 4:00 PM"},
            {"Theme": "A", "Availability Constraint": "April 15, 2:30 - 4:00 PM"},
            {"Theme": "A", "Availability Constraint": "April 15, 2:30 - 4:00 PM"},
            {"Theme": "A", "Availability Constraint": "April 15, 2:30 - 4:00 PM"},
            {"Theme": "A", "Availability Constraint": "April 15, 2:30 - 4:00 PM"},
            {"Theme": "A", "Availability Constraint": "April 15, 2:30 - 4:00 PM"},
        ]
        df = make_df(rows)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, sections, has_constraints=True, mode="oral",
            slot_duration=15, max_presentations=4,
        )
        scheduled = result_df[result_df["Section"].notna()]
        assert len(scheduled) == 6
        assert all(scheduled["Section"] == "Section 1")

    def test_constraint_column_all_blank(self):
        sections = _two_day_sections()
        df = make_simple_df(10, constraints=[None])
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, sections, has_constraints=True, mode="poster",
        )
        scheduled = result_df[result_df["Section"].notna()]
        assert len(scheduled) == 10
        assert excluded.empty
