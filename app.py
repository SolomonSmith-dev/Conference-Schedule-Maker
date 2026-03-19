import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="Conference Schedule Maker", layout="wide")
st.markdown("""
    <style>
        body { background-color: #121212; color: white; }
        .stRadio>div>label { color: white; }
        .stDataFrame { background-color: #1e1e1e; color: white; }
        .stSelectbox>div>label { color: white; }
        .stNumberInput>div>label { color: white; }
        h1 { text-align: center; margin-bottom: 50px; }
        .column-spacing { padding-left: 70px; padding-right: 70px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>Conference Schedule Maker</h1>", unsafe_allow_html=True)

# ----------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------
HEADER_FILL  = PatternFill("solid", start_color="1F3864")
HEADER_FONT  = Font(bold=True, color="FFFFFF", name="Arial", size=11)
ROW_FONT     = Font(name="Arial", size=10)
EVEN_FILL    = PatternFill("solid", start_color="DCE6F1")
ODD_FILL     = PatternFill("solid", start_color="FFFFFF")
THIN_BORDER  = Border(
    left=Side(style="thin"),  right=Side(style="thin"),
    top=Side(style="thin"),   bottom=Side(style="thin"),
)
COL_WIDTHS   = {"Section": 14, "Date": 12, "Session ID": 11,
                "Time Slot": 11, "Theme": 20, "Title": 40,
                "Presenter(s)": 28, "Faculty Mentor": 24}

def style_sheet(ws, columns):
    for col_idx, col_name in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN_BORDER
        ws.column_dimensions[get_column_letter(col_idx)].width = COL_WIDTHS.get(col_name, 18)
    ws.row_dimensions[1].height = 20

def write_rows(ws, df, columns, has_date=True):
    for row_idx, (_, row) in enumerate(df.iterrows(), start=2):
        fill = EVEN_FILL if row_idx % 2 == 0 else ODD_FILL
        for col_idx, col_name in enumerate(columns, start=1):
            val = row.get(col_name, "")
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = ROW_FONT
            cell.fill = fill
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = THIN_BORDER

def make_sheet_name(section_date, start_time, end_time):
    """Format: MMDD HHMM-HHMM  e.g. 415 1430-1600"""
    d = section_date.strftime("%-m%d").lstrip("0") or "0"
    s = start_time.strftime("%H%M")
    e = end_time.strftime("%H%M")
    return f"{d} {s}-{e}"

def build_xlsx(sections_data, final_df, columns, output_filename):
    """
    sections_data: list of dicts with keys: sheet_name, section_df
    final_df: master dataframe with all rows
    columns: list of column names to write
    Returns BytesIO object.
    """
    wb = Workbook()
    wb.remove(wb.active)  # remove default empty sheet

    # Master sheet first
    ws_master = wb.create_sheet("Master")
    style_sheet(ws_master, columns)
    write_rows(ws_master, final_df, columns)

    # One sheet per section
    for sd in sections_data:
        ws = wb.create_sheet(sd["sheet_name"])
        style_sheet(ws, columns)
        write_rows(ws, sd["section_df"], columns)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

# ----------------------------------------------------------------
# LAYOUT
# ----------------------------------------------------------------
col1, col2 = st.columns([1, 2])
col1.markdown('<div class="column-spacing"></div>', unsafe_allow_html=True)
col2.markdown('<div class="column-spacing"></div>', unsafe_allow_html=True)

with col1:
    st.markdown("""
    **Welcome to the Conference Schedule Maker!**
    Please follow the instructions below to ensure smooth processing of your schedule:

    #### Required Columns in the Excel File:
    Your Excel file must include **exactly** the following columns (case-sensitive):
    - **Theme**
    - **Title**
    - **Presenter(s)**
    - **Faculty Mentor**

    #### Column Descriptions:
    - **Theme**: Category or department (e.g., Arts, Biology, Computer Science)
    - **Title**: Title of the presentation
    - **Presenter(s)**: Name(s), comma-separated for multiple
    - **Faculty Mentor**: Name(s) of the faculty mentor(s)

    #### Multi-Day / Multi-Sheet Output:
    Each section is assigned a **date + time window**. The downloaded XLSX will contain
    a **Master sheet** plus one tab per section, named `MMDD HHMM-HHMM`
    (e.g. `415 1430-1600` = April 15, 2:30-4:00 PM).
    """)

with col2:
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

    if uploaded_file:
        all_sheets = pd.read_excel(uploaded_file, sheet_name=None)
        # Always read from Master if it exists, otherwise first sheet
        if "Master" in all_sheets:
            df = all_sheets["Master"]
        else:
            df = list(all_sheets.values())[0]

        required_columns = ['Theme', 'Title', 'Presenter(s)', 'Faculty Mentor']
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            st.error(f"Missing columns: {missing_cols}")
        elif df.empty:
            st.warning("The Master sheet is empty. Add your presentations to the Master sheet and re-upload.")
        else:
            session_type = st.radio("Choose Session Type:", ["Oral Session Maker", "Poster Session Maker"])

            # ----------------------------------------------------------------
            # ORAL SESSION MAKER
            # ----------------------------------------------------------------
            if session_type == "Oral Session Maker":
                slot_duration     = st.number_input("Duration per presentation (minutes):", min_value=5, max_value=20, value=15)
                max_presentations = st.number_input("Max presentations per session:",       min_value=3, max_value=10, value=4)
                num_sections      = st.number_input("Number of sections (across all days):", min_value=1, max_value=10, value=2)

                sections = []
                for i in range(int(num_sections)):
                    st.subheader(f"Section {i+1}")
                    c_date, c_start, c_end = st.columns(3)
                    with c_date:
                        section_date = st.date_input("Date:", key=f"date_{i}", value=datetime.today().date())
                    with c_start:
                        start = st.time_input("Start time:", key=f"start_{i}",
                                              value=datetime.strptime("10:00 AM", "%I:%M %p").time() if i == 0
                                              else datetime.strptime("2:00 PM",   "%I:%M %p").time())
                    with c_end:
                        end = st.time_input("End time:", key=f"end_{i}",
                                            value=datetime.strptime("11:00 AM", "%I:%M %p").time() if i == 0
                                            else datetime.strptime("3:00 PM",   "%I:%M %p").time())

                    start_dt = datetime.combine(section_date, start)
                    end_dt   = datetime.combine(section_date, end)
                    if end_dt <= start_dt:
                        end_dt += timedelta(days=1)

                    sections.append({
                        'name':       f"Section {i+1}",
                        'sheet_name': make_sheet_name(section_date, start, end),
                        'date':       section_date,
                        'start':      start,
                        'end':        end,
                        'start_dt':   start_dt,
                        'end_dt':     end_dt,
                    })

                if st.button("Generate Schedule"):
                    df_work = df.copy().sort_values(by="Theme").reset_index(drop=True)
                    split_indices = np.linspace(0, len(df_work), int(num_sections)+1, dtype=int)
                    section_dfs   = [df_work.iloc[split_indices[i]:split_indices[i+1]] for i in range(int(num_sections))]

                    df_work['Session ID'] = None
                    df_work['Date']       = None
                    df_work['Time Slot']  = None
                    df_work['Section']    = None

                    session_id   = 1
                    current_time = [s['start_dt'] for s in sections]
                    overflow_warnings = []

                    for si, section_df in enumerate(section_dfs):
                        section_end = sections[si]['end_dt']
                        for theme, theme_df in section_df.groupby('Theme'):
                            for i in range(0, len(theme_df), int(max_presentations)):
                                group       = theme_df.iloc[i:i+int(max_presentations)]
                                required_end = current_time[si] + timedelta(minutes=len(group)*int(slot_duration))
                                if required_end > section_end:
                                    overflow_warnings.append(
                                        f"Section {si+1} ({sections[si]['date']}) ran out of time during theme '{theme}'.")
                                time_cursor = current_time[si]
                                for idx in group.index:
                                    df_work.at[idx, 'Session ID'] = session_id
                                    df_work.at[idx, 'Date']       = sections[si]['date'].strftime("%Y-%m-%d")
                                    df_work.at[idx, 'Time Slot']  = time_cursor.strftime("%I:%M %p")
                                    df_work.at[idx, 'Section']    = sections[si]['name']
                                    time_cursor += timedelta(minutes=int(slot_duration))
                                current_time[si] = time_cursor
                                session_id += 1

                    for w in overflow_warnings:
                        st.warning(w)

                    cols = ['Section', 'Date', 'Session ID', 'Time Slot', 'Theme', 'Title', 'Presenter(s)', 'Faculty Mentor']
                    final_df = df_work[cols]

                    st.write("**Oral Schedule Preview (first 20 rows):**")
                    st.dataframe(final_df.head(20))
                    if len(final_df) > 20:
                        st.caption(f"Showing 20 of {len(final_df)} rows.")
                    st.write(f"Total scheduled: {final_df['Session ID'].notna().sum()} presentations | Sessions: {session_id-1}")

                    # Build per-section data for XLSX tabs
                    sections_data = []
                    for si, s in enumerate(sections):
                        mask = final_df['Section'] == s['name']
                        sections_data.append({
                            "sheet_name": s['sheet_name'],
                            "section_df": final_df[mask].reset_index(drop=True),
                        })

                    xlsx_buf = build_xlsx(sections_data, final_df, cols, "oral_schedule.xlsx")
                    st.download_button(
                        "Download Oral Schedule XLSX",
                        xlsx_buf,
                        "oral_presentation_schedule.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

            # ----------------------------------------------------------------
            # POSTER SESSION MAKER
            # ----------------------------------------------------------------
            elif session_type == "Poster Session Maker":
                num_sections  = st.number_input("Number of poster sections (across all days):", min_value=1, max_value=10, value=2)
                poster_duration = st.number_input("Duration per poster (minutes):", min_value=5, max_value=60, value=10)

                poster_sections = []
                for i in range(int(num_sections)):
                    st.subheader(f"Poster Section {i+1}")
                    c_date, c_start, c_end = st.columns(3)
                    with c_date:
                        section_date = st.date_input("Date:", key=f"poster_date_{i}", value=datetime.today().date())
                    with c_start:
                        start = st.time_input("Start Time:", key=f"poster_start_{i}",
                                              value=datetime.strptime("10:00 AM", "%I:%M %p").time() if i == 0
                                              else datetime.strptime("1:00 PM",   "%I:%M %p").time())
                    with c_end:
                        end = st.time_input("End Time:", key=f"poster_end_{i}",
                                            value=datetime.strptime("11:30 AM", "%I:%M %p").time() if i == 0
                                            else datetime.strptime("2:30 PM",   "%I:%M %p").time())

                    start_dt = datetime.combine(section_date, start)
                    end_dt   = datetime.combine(section_date, end)
                    if end_dt <= start_dt:
                        end_dt += timedelta(days=1)

                    poster_sections.append({
                        'name':       f"Poster Section {i+1}",
                        'sheet_name': make_sheet_name(section_date, start, end),
                        'date':       section_date,
                        'start':      start,
                        'end':        end,
                        'start_dt':   start_dt,
                        'end_dt':     end_dt,
                    })

                if st.button("Generate Poster Schedule"):
                    df_work = df.copy().sort_values(by="Theme").reset_index(drop=True)
                    split_indices = np.linspace(0, len(df_work), int(num_sections)+1, dtype=int)
                    poster_groups = [df_work.iloc[split_indices[i]:split_indices[i+1]] for i in range(int(num_sections))]

                    df_work['Session ID'] = None
                    df_work['Date']       = None
                    df_work['Time Slot']  = None
                    df_work['Section']    = None

                    global_session_id = 1
                    overflow_warnings = []

                    for idx, group in enumerate(poster_groups):
                        time_cursor = poster_sections[idx]['start_dt']
                        end_time    = poster_sections[idx]['end_dt']
                        for i in range(len(group)):
                            if time_cursor >= end_time:
                                overflow_warnings.append(
                                    f"Poster Section {idx+1} ({poster_sections[idx]['date']}) ran out of time at poster #{i+1}.")
                            df_work.at[group.index[i], 'Session ID'] = global_session_id
                            df_work.at[group.index[i], 'Date']       = poster_sections[idx]['date'].strftime("%Y-%m-%d")
                            df_work.at[group.index[i], 'Time Slot']  = time_cursor.strftime("%I:%M %p")
                            df_work.at[group.index[i], 'Section']    = poster_sections[idx]['name']
                            time_cursor       += timedelta(minutes=int(poster_duration))
                            global_session_id += 1

                    for w in overflow_warnings:
                        st.warning(w)

                    cols = ['Section', 'Date', 'Session ID', 'Time Slot', 'Theme', 'Title', 'Presenter(s)', 'Faculty Mentor']
                    final_df = df_work[cols]

                    st.write("**Poster Schedule Preview (first 20 rows):**")
                    st.dataframe(final_df.head(20))
                    if len(final_df) > 20:
                        st.caption(f"Showing 20 of {len(final_df)} rows.")
                    st.write(f"Total scheduled: {final_df['Session ID'].notna().sum()} posters | Slots: {global_session_id-1}")

                    sections_data = []
                    for si, s in enumerate(poster_sections):
                        mask = final_df['Section'] == s['name']
                        sections_data.append({
                            "sheet_name": s['sheet_name'],
                            "section_df": final_df[mask].reset_index(drop=True),
                        })

                    xlsx_buf = build_xlsx(sections_data, final_df, cols, "poster_schedule.xlsx")
                    st.download_button(
                        "Download Poster Schedule XLSX",
                        xlsx_buf,
                        "poster_presentation_schedule.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
