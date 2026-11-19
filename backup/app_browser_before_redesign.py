"""
STUDY WEEK ASSISTANT - browser app

This file only draws the screens. All calculations are in project_code.py.

Start it with:   streamlit run app_browser.py
(or run project_code.py and choose 1)
"""

import io
import os
from datetime import datetime

import streamlit as st

import project_code as core

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO_FOLDER = os.path.join(HERE, "test_cases", "case1_normal_week")
DEMO_NOW = datetime(2026, 11, 16, 9, 0)        # the demo week always starts on this Monday

STATUS_ICONS = {"SAFE": "🟢", "WARNING": "🟡", "DANGER": "🟠", "FAILED": "🔴", "NO DATA": "⚪"}
LEVEL_ICONS = {"OVERDUE": "⚫", "URGENT": "🔴", "SOON": "🟠", "LATER": "🟢"}

st.set_page_config(page_title="Study Week Assistant", page_icon="📚", layout="wide")


# ----------------------------------------------------------------------------
# Memory of the app (kept while the browser tab is open)
# ----------------------------------------------------------------------------

def start_memory():
    defaults = {"group": {}, "my_name": "", "deadlines": [], "attendance": [], "demo": False,
                "upload_round": 0}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_demo_week():
    """Fill the app with the invented students from test case 1."""
    group = {}
    for file_name in ("aziz.csv", "mina.csv", "lucas.csv", "jisoo_screenshot.png"):
        path = os.path.join(DEMO_FOLDER, file_name)
        group[core.member_name_from_file(file_name)] = core.load_timetable(path, file_name)
    st.session_state.group = group
    st.session_state.my_name = "Aziz"
    st.session_state.deadlines = core.load_deadlines(os.path.join(DEMO_FOLDER, "smart_lms_calendar.ics"))
    st.session_state.attendance = core.load_attendance_csv(os.path.join(DEMO_FOLDER, "attendance.csv"))
    st.session_state.demo = True


def clear_everything():
    upload_round = st.session_state.upload_round + 1     # new round = empty upload boxes
    for key in ("group", "my_name", "deadlines", "attendance", "demo"):
        st.session_state.pop(key, None)
    start_memory()
    st.session_state.upload_round = upload_round


def current_time():
    return DEMO_NOW if st.session_state.demo else datetime.now()


# ----------------------------------------------------------------------------
# Sidebar: getting the data in
# ----------------------------------------------------------------------------

def draw_sidebar():
    side = st.sidebar
    side.title("📚 Study Week Assistant")
    side.caption("Step 1: load your data. Step 2: use the three tabs.")

    # on_click runs the function first and then redraws the whole page.
    side.button("▶ Try the demo week", on_click=load_demo_week)
    side.caption("The demo uses invented students, so no password is needed.")

    with side.expander("🔐 Log in to the attendance site"):
        st.caption("Gets your timetable and attendance from att.wsu.ac.kr. "
                   "Your password is used once and is never saved.")
        with st.form("login_form", clear_on_submit=True):
            student_id = st.text_input("Student ID")
            password = st.text_input("Password", type="password")
            pressed = st.form_submit_button("Get my data")
        if pressed:
            try:
                with st.spinner("Asking the attendance site..."):
                    result = core.fetch_from_site(student_id, password)
                name = result["name"] or "Me"
                st.session_state.demo = False
                st.session_state.my_name = name
                st.session_state.group[name] = result["timetable"]
                st.session_state.attendance = result["attendance"]
                st.success(f"Loaded {len(result['attendance'])} courses for {name}.")
            except core.InputError as problem:
                st.error(str(problem))

    with side.expander("📁 Upload my files instead"):
        typed_name = st.text_input("My name", value=st.session_state.my_name)
        upload_round = st.session_state.upload_round
        timetable_file = st.file_uploader("My timetable (screenshot or .csv)",
                                          type=["png", "jpg", "jpeg", "csv"],
                                          key=f"my_timetable_{upload_round}")
        calendar_file = st.file_uploader("Smart LMS calendar (.ics)", type=["ics"],
                                         key=f"my_calendar_{upload_round}")
        attendance_file = st.file_uploader("Attendance file (.csv, optional)", type=["csv"],
                                           key=f"my_attendance_{upload_round}")
        if timetable_file is not None:
            try:
                name = typed_name.strip() or "Me"
                blocks = core.load_timetable(io.BytesIO(timetable_file.getvalue()), timetable_file.name)
                st.session_state.my_name = name
                st.session_state.group[name] = blocks
                st.success(f"Timetable loaded: {len(blocks)} class blocks.")
            except core.InputError as problem:
                st.error(str(problem))
        if calendar_file is not None:
            try:
                st.session_state.deadlines = core.load_deadlines(io.BytesIO(calendar_file.getvalue()))
                st.success(f"Calendar loaded: {len(st.session_state.deadlines)} entries.")
            except core.InputError as problem:
                st.error(str(problem))
        if attendance_file is not None:
            try:
                st.session_state.attendance = core.load_attendance_csv(io.BytesIO(attendance_file.getvalue()))
                st.success(f"Attendance loaded: {len(st.session_state.attendance)} courses.")
            except core.InputError as problem:
                st.error(str(problem))

    my_blocks = st.session_state.group.get(st.session_state.my_name)
    if my_blocks is not None:
        side.download_button("⬇ Save my timetable file (share it with your group)",
                             data=core.timetable_to_csv(my_blocks),
                             file_name=f"{st.session_state.my_name.split()[0].lower()}_timetable.csv",
                             mime="text/csv")
    side.button("🗑 Clear everything", on_click=clear_everything)


# ----------------------------------------------------------------------------
# Tab 1: Meet
# ----------------------------------------------------------------------------

def week_grid_html(timetables, days, earliest, latest):
    """Draw the week as a coloured table: green = everyone free."""
    start, end = core.parse_time(earliest), core.parse_time(latest)
    cell = "padding:3px 6px;border:1px solid #fff;text-align:center;font-size:12px;color:#222;"
    html = ['<table style="border-collapse:collapse;width:100%;">', "<tr>",
            f'<th style="{cell}background:#fff;"></th>']
    html += [f'<th style="{cell}background:#37474f;color:#fff;">{day}</th>' for day in days]
    html.append("</tr>")
    for minute in range(start, end, 30):
        html.append(f'<tr><td style="{cell}background:#fff;white-space:nowrap;">{core.format_time(minute)}</td>')
        for day in days:
            busy = [name for name, blocks in timetables.items()
                    if any(b["day"] == day and b["start"] < minute + 30 and b["end"] > minute for b in blocks)]
            if not busy:
                colour, text = "#a5d6a7", "free"
            elif len(busy) == 1:
                colour, text = "#ffe082", busy[0].split()[0]
            else:
                colour, text = "#cfd8dc", f"{len(busy)} busy"
            html.append(f'<td style="{cell}background:{colour};">{text}</td>')
        html.append("</tr>")
    html.append("</table>")
    return "".join(html)


def draw_meet_tab():
    st.subheader("When can the group meet?")
    uploads = st.file_uploader("Add your teammates' timetables (screenshots or .csv files). "
                               "The file name becomes the member's name, for example mina.png.",
                               type=["png", "jpg", "jpeg", "csv"], accept_multiple_files=True,
                               key=f"team_files_{st.session_state.upload_round}")
    for upload in uploads or []:
        name = core.member_name_from_file(upload.name)
        try:
            st.session_state.group[name] = core.load_timetable(io.BytesIO(upload.getvalue()), upload.name)
        except core.InputError as problem:
            st.error(f"{upload.name}: {problem}")

    group = st.session_state.group
    if len(group) < 2:
        st.info("Load at least two timetables: yours in the sidebar and your teammates' here. "
                "Or press **Try the demo week** in the sidebar.")
        return
    st.write("**In this group:** " + ", ".join(f"{name} ({len(blocks)} classes)"
                                               for name, blocks in group.items()))

    hours = [f"{hour:02d}:00" for hour in range(7, 24)]
    first, second, third, fourth = st.columns(4)
    earliest = first.selectbox("Earliest start", hours, index=hours.index("09:00"))
    latest = second.selectbox("Latest end", hours, index=hours.index("18:00"))
    min_minutes = third.selectbox("Meeting length (minutes)", [30, 60, 90, 120, 180], index=1)
    weekend = fourth.checkbox("Include Saturday", value=False)
    days = core.DAYS[:6] if weekend else core.DAYS[:5]

    try:
        everyone, almost = core.find_meeting_slots(group, earliest, latest, min_minutes, days)
    except core.InputError as problem:
        st.error(str(problem))
        return

    if everyone:
        st.success(f"{len(everyone)} time slots work for everyone. The best ones:")
        for column, slot in zip(st.columns(3), everyone[:3]):
            column.metric(f'{slot["day"]} ({core.format_duration(slot["minutes"])})',
                          f'{core.format_time(slot["start"])} - {core.format_time(slot["end"])}')
        if len(everyone) > 3:
            with st.expander(f"Show all {len(everyone)} slots"):
                for slot in everyone:
                    st.write(f'{slot["day"]} {core.format_time(slot["start"])} - '
                             f'{core.format_time(slot["end"])} ({core.format_duration(slot["minutes"])})')
    else:
        st.warning("No time slot works for everyone with these settings.")
        if almost:
            st.write("**Plan B: times when only one person is busy**")
            for slot in almost[:5]:
                st.write(f'{slot["day"]} {core.format_time(slot["start"])} - {core.format_time(slot["end"])} '
                         f'({core.format_duration(slot["minutes"])}), busy: {slot["busy"][0]}')
        else:
            st.write("Try a shorter meeting, a longer day or Saturday.")

    st.write("**The week at a glance** (green = everyone free, yellow = one person busy)")
    st.markdown(week_grid_html(group, days, earliest, latest), unsafe_allow_html=True)
    st.write("**Message for the group chat** (use the copy button)")
    st.code(core.group_message(everyone), language="text")


# ----------------------------------------------------------------------------
# Tab 2: Deadlines
# ----------------------------------------------------------------------------

def draw_deadlines_tab():
    st.subheader("What is due next?")
    if not st.session_state.deadlines:
        st.info("No calendar loaded yet.\n\n"
                "1. Open Smart LMS and go to **Calendar**.\n"
                "2. Click **Export calendar**, choose *All events* and *Recent and next 60 days*.\n"
                "3. Click **Export** and upload the file in the sidebar (Upload my files instead).")
        return
    now = current_time()
    my_timetable = st.session_state.group.get(st.session_state.my_name)
    rated = core.rate_deadlines(st.session_state.deadlines, now, my_timetable)
    if st.session_state.demo:
        st.caption(f"Demo date: {now.strftime('%A %d %B %Y, %H:%M')}")

    counts = {level: sum(item["level"] == level for item in rated) for level in LEVEL_ICONS}
    for column, level in zip(st.columns(4), LEVEL_ICONS):
        column.metric(f"{LEVEL_ICONS[level]} {level.capitalize()}", counts[level])

    show_old = st.checkbox("Show overdue entries", value=True)
    for item in rated:
        if item["level"] == "OVERDUE" and not show_old:
            continue
        left = "overdue" if item["level"] == "OVERDUE" else core.time_left_text(item["hours_left"])
        line = (f'{LEVEL_ICONS[item["level"]]} **{item["title"]}** ({item["course"]}), '
                f'due {item["due"].strftime("%a %d %b, %H:%M")}: {left}')
        st.markdown(line)
        notes = []
        if "free_hours" in item:
            notes.append(f'{item["free_hours"]} free daytime hours before it is due (classes removed)')
        if item["midnight"] and item["level"] != "OVERDUE":
            notes.append("due at midnight, so finish it the evening before")
        if notes:
            st.caption(" | ".join(notes))


# ----------------------------------------------------------------------------
# Tab 3: Attendance
# ----------------------------------------------------------------------------

def draw_attendance_tab():
    st.subheader("How many classes can I still miss?")
    if not st.session_state.attendance:
        st.info("No attendance loaded yet. Log in to the attendance site in the sidebar, "
                "or press **Try the demo week**.")
        return
    st.caption("Woosong rule: a course is failed when absences are more than 1/3 of all class "
               "sessions. Three lates (or early leaves) count as one absence.")
    results = [core.check_attendance(record) for record in st.session_state.attendance]
    order = ["FAILED", "DANGER", "WARNING", "SAFE", "NO DATA"]
    for result in sorted(results, key=lambda r: order.index(r["status"])):
        left, right = st.columns([3, 2])
        left.markdown(f'{STATUS_ICONS[result["status"]]} **{result["course"]}** ({result["status"]})')
        if result["status"] == "NO DATA":
            right.caption("No class sessions recorded.")
            continue
        used = result["counted_absences"] / result["allowed"] if result["allowed"] else 1.0
        left.progress(min(1.0, max(0.0, used)))
        if result["status"] == "FAILED":
            right.error(f'Over the limit by {-result["can_still_miss"]} session(s). Talk to your professor.')
        else:
            right.metric("Sessions you can still miss", result["can_still_miss"])
        left.caption(f'{result["counted_absences"]} of {result["allowed"]} allowed absences used '
                     f'({result["absent"]} absent, {result["late"]} late, {result["early"]} left early, '
                     f'{result["excused"]} excused). '
                     f'{result["lates_to_next"]} more late(s) until the next one costs an absence.')


def draw_help_tab():
    st.subheader("How to use this tool")
    st.markdown(
        "**1. Load your data (sidebar)**\n"
        "- *Log in to the attendance site* gets your timetable and attendance in one step.\n"
        "- No password? Upload a screenshot of the Timetable page of the attendance app. "
        "It finds your busy times from the coloured blocks.\n"
        "- For deadlines, export your calendar from Smart LMS and upload the .ics file.\n\n"
        "**2. Meet**\n"
        "- Every teammate saves a timetable file (button in the sidebar) or a screenshot and sends it to you.\n"
        "- Upload the files in the Meet tab. Never share passwords, only files.\n\n"
        "**3. Deadlines and Attendance**\n"
        "- Deadlines are sorted by urgency and show how many free hours you have before each one.\n"
        "- Attendance shows how close every course is to the 1/3 absence limit.\n\n"
        "**Privacy:** nothing is uploaded anywhere. The app runs on your own computer, "
        "and your password is never written to a file.")


# ----------------------------------------------------------------------------
# The page
# ----------------------------------------------------------------------------

start_memory()
draw_sidebar()
st.title("Study Week Assistant")
st.caption("One place for three weekly questions: when can we meet, what is due, "
           "and how many classes can I still miss?")
meet_tab, deadlines_tab, attendance_tab, help_tab = st.tabs(
    ["📅 Meet", "⏰ Deadlines", "✅ Attendance", "❓ How to use"])
with meet_tab:
    draw_meet_tab()
with deadlines_tab:
    draw_deadlines_tab()
with attendance_tab:
    draw_attendance_tab()
with help_tab:
    draw_help_tab()
