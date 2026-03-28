# Conference Schedule Maker

Streamlit app for generating academic conference schedules. Forked from [sakshi1802](https://github.com/sakshi1802/Conference-Schedule-Maker) and extended for CSUSB's 15th Annual Meeting of the Minds (April 2026, 300+ presenters across 2 days).

## What I Added

**The original handled a single session with CSV export. I extended it to handle multi-day conferences:**

- **Multi-day support** — define multiple sections across different dates. Each section gets its own date, start time, and end time. Works for both oral and poster schedules.
- **Multi-sheet XLSX output** — instead of a flat CSV, the download is an Excel workbook with a Master sheet (all rows) plus one tab per section, named by date and time (e.g. `415 1430-1600` = April 15, 2:30-4:00 PM).
- **Smart tab naming** — tab names auto-generate in `MMDD HHMM-HHMM` format from the section's date and time inputs.
- **Overflow detection** — if a section runs out of time before all presentations are scheduled, it warns instead of silently dropping rows.
- **Styled output** — openpyxl workbook with alternating row colors, bold headers, and proper column widths for each section coordinator.

**For MOTM specifically:** 221 poster entries and 85 oral entries split across April 15-16. The original couldn't handle that. This version splits them cleanly across both days and gives each section coordinator their own tab.

## Original Features

- Upload Excel file with Theme, Title, Presenter(s), and Faculty Mentor columns
- Choose between Oral or Poster session scheduling
- Configure session duration, max presentations per session, and sections per day
- Auto-sorts by theme, splits across sections, assigns time slots
- Preview schedule in-app before downloading

## Stack

Python, Streamlit, pandas, openpyxl

## Setup

```bash
git clone https://github.com/SolomonSmith-dev/Conference-Schedule-Maker
cd Conference-Schedule-Maker
pip install -r requirements.txt
streamlit run app.py
```
