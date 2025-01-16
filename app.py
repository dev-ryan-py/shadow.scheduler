import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta

# ------------------------------------
# Page Config for Wide Layout
# ------------------------------------
st.set_page_config(page_title="Trainee Shadow Schedule", layout="wide")

# ------------------------------------
# Scheduling Logic
# ------------------------------------
def schedule_with_distributed_no_assignment(names, stations, time_slots):
    stations_sorted = sorted(stations)
    visited_map = {n: set() for n in names}
    station_visited_map = {s: set() for s in stations_sorted}

    station_rotation_index = 0
    name_rotation_index = 0
    final_schedule = []

    fill_count = min(len(names), len(stations_sorted))

    for _ in time_slots:
        row_assignments = ["-"] * len(stations_sorted)
        stations_to_fill = []
        for offset in range(fill_count):
            st_idx = (station_rotation_index + offset) % len(stations_sorted)
            stations_to_fill.append(st_idx)

        station_rotation_index = (station_rotation_index + fill_count) % len(stations_sorted)
        used_this_slot = set()

        for offset, st_index in enumerate(stations_to_fill):
            st_name = stations_sorted[st_index]
            assigned = None

            for n_offset in range(len(names)):
                candidate = names[(name_rotation_index + n_offset) % len(names)]
                if candidate in used_this_slot:
                    continue

                if len(station_visited_map[st_name]) == len(names):
                    station_visited_map[st_name].clear()

                if len(visited_map[candidate]) == len(stations_sorted):
                    visited_map[candidate].clear()

                if st_name not in visited_map[candidate]:
                    assigned = candidate
                    break

            if assigned is None:
                for fallback_name in names:
                    if fallback_name not in used_this_slot:
                        assigned = fallback_name
                        station_visited_map[st_name].clear()
                        visited_map[fallback_name].clear()
                        break
                if assigned is None:
                    continue

            row_assignments[st_index] = assigned
            used_this_slot.add(assigned)

            if assigned != "-":
                visited_map[assigned].add(st_name)
                station_visited_map[st_name].add(assigned)

            name_rotation_index = (name_rotation_index + 1) % len(names)

        final_schedule.append(row_assignments)

    return stations_sorted, final_schedule

# ------------------------------------
# Fuzzy Time Parsing
# ------------------------------------
def parse_fuzzy_time(t_str: str) -> time:
    t_str = t_str.strip().lower()
    is_am = 'am' in t_str
    is_pm = 'pm' in t_str
    numeric_part = t_str.replace('am','').replace('pm','').strip()

    if ':' in numeric_part:
        parts = numeric_part.split(':')
        hour_12 = int(parts[0])
        minute = int(parts[1])
    else:
        if len(numeric_part) <= 2:
            hour_12 = int(numeric_part)
            minute = 0
        else:
            hr_str = numeric_part[:-2]
            mn_str = numeric_part[-2:]
            hour_12 = int(hr_str)
            minute = int(mn_str)

    if hour_12 < 1 or hour_12 > 12:
        hour_12 = hour_12 % 12
        if hour_12 == 0:
            hour_12 = 12

    if not is_am and not is_pm:
        if hour_12 == 12:
            is_pm = True
        elif 1 <= hour_12 <= 6:
            is_pm = True
        else:
            is_am = True

    final_hour_24 = hour_12
    if is_pm and hour_12 < 12:
        final_hour_24 += 12
    if is_am and hour_12 == 12:
        final_hour_24 = 0

    return time(final_hour_24, minute)

def parse_fuzzy_time_range(range_str: str):
    parts = range_str.split('-')
    if len(parts) != 2:
        raise ValueError("Time range must have a dash '-', e.g. '2pm-5pm' or '11-5'")
    start_part = parts[0].strip()
    end_part = parts[1].strip()

    start_t = parse_fuzzy_time(start_part)
    end_t   = parse_fuzzy_time(end_part)
    return start_t, end_t

# ------------------------------------
# Helper: "FirstName LastInitial."
# ------------------------------------
def shorten_name(full_name: str) -> str:
    txt = full_name.strip()
    if txt == "-" or not txt:
        return txt
    parts = txt.split()
    if len(parts) > 1:
        return f"{parts[0]} {parts[-1][0]}."
    else:
        return parts[0]

# ------------------------------------
# Main Streamlit App
# ------------------------------------
def main():
    st.markdown(
    """
    <div style="text-align: center; margin-bottom: 20px;">
      <h1>Get-Me-Outta-This-Room Calculator</h1>
    </div>
    """,
    unsafe_allow_html=True
    )
    
    col_ratio = [1.0, 0.75, 2.5, 1.0, 1.0]
    col1, col2, col3, col4, col5 = st.columns(col_ratio)

    with col1:
        some_col_one_var = 0
        
    with col2:
        time_range_str = st.text_input(
            "Time Range",
            value="3-6"
        )
        
        duration = st.number_input(
            label="Duration (min)",
            value=30,
            step=15,
            min_value=15,
            max_value=120
        )
        
    with col3:
        all_stations = [
            "Row A", "Row C", "Row D", "Row E", "Row F",
            "Row G", "Row H", "Row I", "Row J", "Row K",
            "Row L", "Bulk ", " CLR "
        ]
        chosen_stations = st.multiselect(
            "Pick all stations you want to include:",
            all_stations,
            default=["Row C", "Row D", "Row E", "Row H", "Row J", "Row K", "Row L"]
        )

        st.markdown(
        """
        <div style="margin-bottom: 20px;">
        </div>
        """,
        unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns([1.3,2,0.7])
        with col2:
            generate_btn = st.button("Generate Schedule")

    with col4:
        names_entries = st.text_area(
            "Trainees",
            value="Ariel Currie\nJade Wilson\nJen Cochrane",
            height=160
        )

    with col5:
        some_col_five_var = 0

    if generate_btn:
        try:
            start_t, end_t = parse_fuzzy_time_range(time_range_str)
        except ValueError as e:
            st.error(f"Time range parse error: {e}")
            return

        start_dt = datetime.combine(date.today(), start_t)
        end_dt   = datetime.combine(date.today(), end_t)
        if end_dt <= start_dt:
            st.error("End time must be strictly after Start time!")
            return

        if not chosen_stations:
            st.error("No stations selected!")
            return

        names = [line.strip() for line in names_entries.split("\n") if line.strip()]
        if not names:
            st.error("No names provided!")
            return

        time_slots_dt = []
        current = start_dt
        while current < end_dt:
            time_slots_dt.append(current)
            current += timedelta(minutes=duration)
        if not time_slots_dt:
            st.error("No time slots generated! Check times/duration.")
            return

        stations_sorted, final_schedule = schedule_with_distributed_no_assignment(
            names,
            chosen_stations,
            time_slots_dt
        )

        for r_idx, row in enumerate(final_schedule):
            for c_idx, name_val in enumerate(row):
                final_schedule[r_idx][c_idx] = shorten_name(name_val)

        times_str = [dt.strftime("%I:%M %p").lstrip("0") for dt in time_slots_dt]
        table_header = ["Time"] + stations_sorted
        table_rows = []
        for i, t_str in enumerate(times_str):
            row = [t_str] + final_schedule[i]
            table_rows.append(row)

        df = pd.DataFrame(table_rows, columns=table_header)

        df = df.set_index("Time")
        df.index.name = None

        st.markdown(
            """
            <style>
            table td, table th {
                text-align: center !important; background-color: #101726;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.subheader("Teamlead Shadow Schedule")
        st.markdown(
        """
        <div style="margin-top: -15px; margin-bottom: 20px; font-style: italic; font-size: 14px;">
        <p>You can reduce browser window size to reduce table size for screenshot</p>
        </div>
        """,
        unsafe_allow_html=True
        )
        st.table(df)

if __name__ == "__main__":
    main()
