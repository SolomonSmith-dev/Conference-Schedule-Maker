# CSUSB Meeting of the Minds -- Schedule Maker (MOTM Edition)

## What This Is

A fork of the [Conference Schedule Maker](https://github.com/sakshi1802/Conference-Schedule-Maker) with a new tab built specifically for the **15th Annual CSUSB Meeting of the Minds** conference. The original tool is preserved as-is. The new "CSUSB MOTM Edition" tab adds availability-constraint-aware scheduling for both oral and poster presentations.

## Why It Exists

The original Conference Schedule Maker distributes presentations evenly across sections with no regard for presenter availability. For the CSUSB Meeting of the Minds (April 15-16, 2026), presenters submitted availability forms indicating which days and time windows they could attend. This edition reads that availability data and schedules presenters only into sections they can actually make it to.

## What Changed

The app now has two tabs when you open it:

**Original tab** -- Untouched upstream logic. Works exactly as the original author built it.

**CSUSB MOTM Edition tab** -- The new version with these differences:

| Feature | Original | MOTM Edition |
|---|---|---|
| Availability constraints | Not supported | Reads "Availability Constraint" column from Excel |
| Scheduling algorithm | Even split across sections | Constrained-first placement, then balanced fill |
| Poster time slots | Sequential per-poster slots | Day/section assignment only (all posters display simultaneously) |
| Oral session time slots | One slot per presenter | Concurrent presenters share a time slot (up to max per session) |
| Excluded presenters | N/A | Separate "Excluded" sheet for those who cannot attend |
| Column order in output | Section, Date, Session ID, Time Slot, Theme, Title, ... | Theme, Title, Presenter(s), Faculty Mentor, [Constraint], Section, Date, ... |

## Conference Numbers

- **86 oral presentations** across 4 sections (2 per day)
  - April 15: 2:30-4:00 PM, 4:15-5:30 PM
  - April 16: 2:30-4:00 PM, 4:15-5:30 PM
- **246 poster presentations** across 2 sections (1 per day)
  - April 15: 10:00-11:00 AM
  - April 16: 10:00-11:00 AM
- **25 poster presenters excluded** (marked "Neither day" / "None")
- **1 oral presenter excluded**
- **10+ academic themes** (Behavioral and Social Sciences, Biological and Agricultural Sciences, Engineering and Computer Science, etc.)

## Availability Constraint Formats

The "Availability Constraint" column in the Excel input supports these formats:

| Value | Meaning |
|---|---|
| *(empty)* | No constraint, schedule anywhere |
| `April 15, 2:30 - 4:00 PM` | Must be in that specific section |
| `April 15, 2:30 - 4:00 PM, April 16, 4:15 - 5:45 PM` | Can go in either listed section |
| `April 15 only` | Any section on April 15 |
| `Either day` | No constraint |
| `Late submission` | Treated as no constraint |
| `None (please notify osr@csusb.edu)` | Cannot attend -- placed in Excluded sheet |
| `Neither day (please notify osr@csusb.edu)` | Cannot attend -- placed in Excluded sheet |

## How the MOTM Algorithm Works

1. **Parse constraints** -- Each presenter's availability is parsed into allowed sections
2. **Exclude** -- Presenters marked "None" or "Neither day" are removed and placed in the Excluded sheet
3. **Place constrained presenters first** -- Most restricted presenters (fewest allowed sections) are placed first, using greedy balancing to avoid overloading any one section
4. **Fill with unconstrained** -- Remaining presenters are distributed proportionally to fill remaining capacity, keeping same-theme presentations together
5. **Assign time slots** -- Oral: concurrent presenters in a session share one time slot. Poster: all posters in a section get the same time range label.

## Input Files

These Excel files were used for the 15th Annual Meeting of the Minds:

- `Oral Presentation Schedule Maker Sheet.xlsx` -- 86 oral presentations with availability constraints
- `Poster Presentation Schedule Maker Sheet.xlsx` -- 246 poster presentations with availability constraints
- `MOTM Application Closing Results.xlsx` -- Raw application data from the submission system
- `15th Annual Meeting of the Minds Oral Presentation Availability (Responses).xlsx` -- Google Form responses for oral availability
- `15th Annual Meeting of the Minds Poster Presentation Availability (Responses).xlsx` -- Google Form responses for poster availability

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`. Pick the "CSUSB MOTM Edition" tab, upload your Excel file, configure sections, and generate.

## Branch

All MOTM changes are on the `feature/availability-constraints` branch.

## Tech Stack

- Python 3.7+
- Streamlit (web UI)
- pandas (data processing)
- numpy (section splitting)
- openpyxl (Excel read/write)
- re (constraint parsing)
