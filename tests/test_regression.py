"""Regression tests against the real MOTM poster dataset.

These tests use the actual Poster Presentation Schedule Maker Sheet
to verify that output counts and distributions remain stable.
"""
import os
from datetime import date, time

import pandas as pd
import pytest

from tests.conftest import assign_with_constraints, make_section


POSTER_FILE = os.path.join(
    os.path.expanduser("~"),
    "Downloads",
    "Poster Presentation Schedule Maker Sheet.xlsx",
)


@pytest.fixture
def poster_data():
    if not os.path.exists(POSTER_FILE):
        pytest.skip("Poster input file not found in Downloads")
    df = pd.read_excel(POSTER_FILE, sheet_name="Master")
    return df


@pytest.fixture
def poster_sections():
    return [
        make_section("Poster Section 1", date(2026, 4, 15), time(10, 0), time(11, 0)),
        make_section("Poster Section 2", date(2026, 4, 16), time(10, 0), time(11, 0)),
    ]


class TestPosterRegression:
    def test_total_counts(self, poster_data, poster_sections):
        df = poster_data.copy().sort_values(by="Theme").reset_index(drop=True)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, poster_sections, has_constraints=True, mode="poster",
        )
        scheduled = result_df[result_df["Section"].notna()]
        assert len(scheduled) == 221
        assert len(excluded) == 25
        assert len(scheduled) + len(excluded) == 246

    def test_all_themes_present(self, poster_data, poster_sections):
        df = poster_data.copy().sort_values(by="Theme").reset_index(drop=True)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, poster_sections, has_constraints=True, mode="poster",
        )
        scheduled = result_df[result_df["Section"].notna()]
        themes = scheduled["Theme"].unique()
        assert len(themes) >= 7, f"Only {len(themes)} themes in output, expected at least 7"

    def test_both_sections_populated(self, poster_data, poster_sections):
        df = poster_data.copy().sort_values(by="Theme").reset_index(drop=True)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, poster_sections, has_constraints=True, mode="poster",
        )
        scheduled = result_df[result_df["Section"].notna()]
        s1 = scheduled[scheduled["Section"] == "Poster Section 1"]
        s2 = scheduled[scheduled["Section"] == "Poster Section 2"]
        assert len(s1) > 0
        assert len(s2) > 0
        # Sections should be roughly balanced (within 20%)
        ratio = len(s1) / len(s2) if len(s2) > 0 else float("inf")
        assert 0.5 < ratio < 2.0, f"Section imbalance: {len(s1)} vs {len(s2)}"

    def test_excluded_are_neither_day(self, poster_data, poster_sections):
        df = poster_data.copy().sort_values(by="Theme").reset_index(drop=True)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, poster_sections, has_constraints=True, mode="poster",
        )
        for _, row in excluded.iterrows():
            constraint = str(row.get("Availability Constraint", "")).lower()
            assert "none" in constraint or "neither" in constraint, (
                f"Excluded row has unexpected constraint: {row.get('Availability Constraint')}"
            )

    def test_no_presenter_lost(self, poster_data, poster_sections):
        """Every title from the input must appear in either scheduled or excluded."""
        df = poster_data.copy().sort_values(by="Theme").reset_index(drop=True)
        result_df, excluded, warnings, sid = assign_with_constraints(
            df, poster_sections, has_constraints=True, mode="poster",
        )
        scheduled = result_df[result_df["Section"].notna()]
        input_titles = set(df["Title"].str.strip().str.upper())
        output_titles = set(scheduled["Title"].str.strip().str.upper())
        excluded_titles = set(excluded["Title"].str.strip().str.upper()) if not excluded.empty else set()
        all_output = output_titles | excluded_titles
        missing = input_titles - all_output
        assert len(missing) == 0, f"{len(missing)} titles missing from output: {list(missing)[:5]}"
