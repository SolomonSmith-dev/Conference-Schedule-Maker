# Conference Schedule Maker

Streamlit app for generating academic conference schedules. Originally forked from [sakshi1802](https://github.com/sakshi1802/Conference-Schedule-Maker) and extended for CSUSB's Meeting of the Minds undergraduate research symposium.

## Extensions Added

- Multi-day schedule support
- Multi-sheet XLSX output (one sheet per day)
- Used in production for the 15th Annual CSUSB Meeting of the Minds (April 2026, 300+ presenters)

## Features

- Upload Excel file with Theme, Title, Presenter(s), and Faculty Mentor columns
- Choose between Oral or Poster session scheduling
- Configure session duration, max presentations per session, and sections per day
- Auto-sorts by theme, splits across sections, assigns time slots
- Preview schedule in-app before downloading
- Export as CSV or multi-sheet XLSX

## Stack

Python, Streamlit, pandas, openpyxl

## Setup

```bash
git clone https://github.com/SolomonSmith-dev/Conference-Schedule-Maker
cd Conference-Schedule-Maker
pip install -r requirements.txt
streamlit run app.py
```

Or use the [live demo](https://conference-schedule-maker-app-git-mabxnjmbagengxvdttnhfg.streamlit.app/).
