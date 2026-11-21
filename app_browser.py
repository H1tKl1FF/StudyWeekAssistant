"""
STUDY WEEK ASSISTANT - browser app

This file only draws the screens. All calculations are in project_code.py.

Layout: a home dashboard with three cards (Meet, Deadlines, Attendance).
Each card opens a full page. Colours: deep blue with warm accents.

Start it with:   streamlit run app_browser.py
(or run project_code.py and choose 1)
"""

import html
import importlib
import io
import os
from datetime import datetime

import streamlit as st

import project_code as core

# Streamlit keeps project_code in memory while the app runs. When the file has
# been changed since then, load it again so the newest code is always used.
_core_changed = os.path.getmtime(core.__file__)
if getattr(core, "loaded_at_change_time", None) != _core_changed:
    core = importlib.reload(core)
    core.loaded_at_change_time = _core_changed

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO_FOLDER = os.path.join(HERE, "test_cases", "case1_normal_week")
DEMO_NOW = datetime(2026, 11, 16, 9, 0)        # the demo week always starts on this Monday

# Plain words instead of codes, and the badge colour for each one.
DEADLINE_LABELS = {"OVERDUE": "Overdue", "URGENT": "Due within 2 days",
                   "SOON": "Due this week", "LATER": "Later"}
DEADLINE_COLOURS = {"OVERDUE": "grey", "URGENT": "red", "SOON": "amber", "LATER": "green"}
ATTENDANCE_LABELS = {"FAILED": "Over the limit", "DANGER": "Almost at the limit",
                     "WARNING": "Be careful", "SAFE": "Safe", "NO DATA": "No data yet"}
ATTENDANCE_COLOURS = {"FAILED": "red", "DANGER": "red", "WARNING": "amber",
                      "SAFE": "green", "NO DATA": "grey"}
ATTENDANCE_ORDER = ["FAILED", "DANGER", "WARNING", "SAFE", "NO DATA"]
# The amber is the darker one, so bars and row edges stand out at least 3:1 on white
BAR_COLOURS = {"red": "#E24B4A", "amber": "#BA7517", "green": "#639922", "grey": "#888780"}

PAGES = [("home", "Home", ":material/home:"),
         ("meet", "Meet", ":material/groups:"),
         ("deadlines", "Deadlines", ":material/schedule:"),
         ("attendance", "Attendance", ":material/fact_check:"),
         ("data", "My data", ":material/upload_file:"),
         ("help", "Help", ":material/help:")]

# Colours of theme 2: deep blue (#0C447C, #185FA5, #E6F1FB) with warm accents (#EF9F27).
STYLE = """
<style>
.block-container {padding-top: 3.2rem; max-width: 1120px;}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {display: none;}
button[kind="primary"], [data-testid="stBaseButton-primary"] {
    background: #EF9F27; border-color: #EF9F27; color: #412402;}
/* Darker amber on hover so the white text stays readable (5:1) */
button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {
    background: #9A6212; border-color: #9A6212; color: #FFFFFF;}
/* Keyboard focus: keep the amber button readable and draw a clear blue ring */
button[kind="primary"]:focus:not(:hover), [data-testid="stBaseButton-primary"]:focus:not(:hover) {
    background: #EF9F27; border-color: #EF9F27; color: #412402;}
button[kind="primary"]:focus-visible, [data-testid="stBaseButton-primary"]:focus-visible {
    box-shadow: 0 0 0 2px #FFFFFF, 0 0 0 4px #0C447C; outline: none;}  /* shows in light and dark mode */
/* The open page is marked by an underline too, not only by its colour */
.st-key-swa_nav [data-testid="stBaseButton-primary"] p {
    text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: 4px;}
/* Text only screen readers read out */
.swa-sr {position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden;
         clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;}
.swa-top {background: #0C447C; border-radius: 14px; padding: 18px 24px; margin-bottom: 10px;}
.swa-top .title {color: #FFFFFF; font-size: 1.55rem; font-weight: 700; margin: 0; padding: 0;}
.swa-top p {color: #B5D4F4; margin: 4px 0 0 0;}
.swa-top h1.title {line-height: 1.3;}
.swa-top [data-testid="stHeaderActionElements"] {display: none;}  /* no link icon on the greeting */
.swa-demo {background: rgba(239, 159, 39, 0.18); border: 1px solid rgba(239, 159, 39, 0.6);
            border-radius: 12px; padding: 9px 14px; margin: 0;}
/* Everything below uses see-through tints and inherits the text colour,
   so it looks right in light mode, dark mode and system mode. */
.swa-card, .swa-tile, .swa-step {background: rgba(55, 138, 221, 0.12);
           border: 1px solid rgba(55, 138, 221, 0.30); color: inherit;}
.swa-card {border-radius: 14px; padding: 16px 18px; min-height: 168px; margin-bottom: 8px;}
.swa-card .label, .swa-card .sub, .swa-tile .label, .swa-step p, .swa-row .meta {
           font-size: 0.85rem; opacity: 0.8;}
.swa-card .label {margin: 0;}
.swa-card .big {font-size: 1.4rem; font-weight: 600; margin: 4px 0 10px 0; line-height: 1.25;}
.swa-card .sub {margin: 10px 0 0 0;}
.swa-badge {display: inline-block; font-size: 0.8rem; font-weight: 500; padding: 2px 10px;
            border-radius: 999px; color: inherit;}
.swa-badge.green {background: rgba(99, 153, 34, 0.30);}
.swa-badge.amber {background: rgba(239, 159, 39, 0.35);}
.swa-badge.red {background: rgba(226, 75, 74, 0.30);}
.swa-badge.grey {background: rgba(136, 135, 128, 0.30);}
.swa-badge.blue {background: rgba(55, 138, 221, 0.30);}
.swa-row {background: rgba(55, 138, 221, 0.05); border: 1px solid rgba(55, 138, 221, 0.30);
          border-radius: 12px; padding: 12px 16px; margin-bottom: 8px; color: inherit;}
.swa-row .title {font-weight: 600; margin: 0;}
/* Course name and "N more absences left" share one line, and wrap on phones */
.swa-row .head {display: flex; flex-wrap: wrap; justify-content: space-between;
                align-items: center; gap: 2px 12px;}
/* On phones keep the page buttons in a grid of three instead of seven rows */
@media (max-width: 640px) {
  .st-key-swa_nav [data-testid="stHorizontalBlock"] {flex-flow: row wrap; gap: 0.5rem;}
  .st-key-swa_nav [data-testid="stColumn"] {flex: 1 1 calc(33.3% - 0.5rem) !important;
                                            min-width: calc(33.3% - 0.5rem) !important;}
  .st-key-swa_nav button {padding-left: 0.3rem; padding-right: 0.3rem;}
}
.swa-row .meta {margin: 4px 0 0 0;}
.swa-bar {height: 8px; background: rgba(55, 138, 221, 0.18); border-radius: 4px; overflow: hidden;
          margin-top: 8px;}
.swa-bar span {display: block; height: 100%;}
.swa-tile {border-radius: 12px; padding: 10px 14px;}
.swa-tile .num {font-size: 1.6rem; font-weight: 600; margin: 0;}
.swa-tile .label {margin: 0;}
.swa-step {border-radius: 12px; padding: 14px 16px; min-height: 120px;}
.swa-step .num {display: inline-block; width: 28px; height: 28px; line-height: 28px;
                text-align: center; border-radius: 50%; background: #185FA5; color: #FFFFFF;
                font-weight: 600; margin-bottom: 6px;}
.swa-step p {margin: 0;}
.swa-grid {border-collapse: collapse; width: 100%;}
.swa-grid th {background: #0C447C; color: #FFFFFF; padding: 4px 6px; font-size: 12px;}
.swa-grid td {padding: 3px 6px; border: 1px solid rgba(128, 128, 128, 0.25); text-align: center;
              font-size: 12px; color: inherit;}
.swa-grid td.time, .swa-grid th.time {white-space: nowrap;}
.swa-grid th.time {background: none; color: inherit; font-weight: 400; padding: 3px 6px; text-align: center;
                   border: 1px solid rgba(128, 128, 128, 0.25);}
.swa-grid td.free {background: rgba(99, 153, 34, 0.30);}
.swa-grid td.one {background: rgba(239, 159, 39, 0.35);}
.swa-grid td.many {background: rgba(55, 138, 221, 0.25);}
</style>
"""

st.set_page_config(page_title="Study Week Assistant", page_icon="📚", layout="wide",
                   initial_sidebar_state="collapsed")


def safe(text):
    """Make text from files safe to put inside our HTML."""
    return html.escape(str(text))


def badge(text, colour):
    return f'<span class="swa-badge {colour}">{safe(text)}</span>'


# ----------------------------------------------------------------------------
# Memory of the app (kept while the browser tab is open)
# ----------------------------------------------------------------------------

def start_memory():
    defaults = {"group": {}, "my_name": "", "deadlines": [], "attendance": [], "demo": False,
                "upload_round": 0, "page": "home", "loaded_files": set(),
                "member_sources": {}}           # member name -> the file it came from
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to(page):
    st.session_state.page = page


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
    st.session_state.page = "home"


def clear_everything():
    upload_round = st.session_state.upload_round + 1     # new round = empty upload boxes
    for key in ("group", "my_name", "deadlines", "attendance", "demo", "loaded_files",
                "member_sources"):
        st.session_state.pop(key, None)
    start_memory()
    st.session_state.upload_round = upload_round
    st.session_state.page = "home"


def current_time():
    """Korean time, whatever time zone the laptop is set to (deadlines are in Korean time)."""
    if st.session_state.demo:
        return DEMO_NOW
    return datetime.now(core.KOREA_TIME).replace(tzinfo=None)


def has_any_data():
    return bool(st.session_state.group or st.session_state.deadlines or st.session_state.attendance)


def is_new_upload(upload, label):
    """True the first time a file is seen, so pictures are not read again on every click."""
    key = (label, upload.name, upload.size)
    if key in st.session_state.loaded_files:
        return False
    st.session_state.loaded_files.add(key)
    return True


def rated_deadlines():
    my_timetable = st.session_state.group.get(st.session_state.my_name)
    return core.rate_deadlines(st.session_state.deadlines, current_time(), my_timetable)


def checked_attendance():
    results = [core.check_attendance(record) for record in st.session_state.attendance]
    return sorted(results, key=lambda r: ATTENDANCE_ORDER.index(r["status"]))


def miss_text(result):
    if result["status"] == "FAILED":
        return f'Over the limit by {-result["can_still_miss"]}'
    if result["status"] == "NO DATA":
        return "No classes recorded"
    left = result["can_still_miss"]
    if left == 0:
        return "No absences left"
    return f"{left} more absence left" if left == 1 else f"{left} more absences left"


# ----------------------------------------------------------------------------
# Top bar and navigation
# ----------------------------------------------------------------------------

def draw_top_bar():
    name = st.session_state.my_name.split()[0] if st.session_state.my_name else "there"
    hour = current_time().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    date_text = current_time().strftime("%A %d %B %Y")
    st.markdown(f'<div class="swa-top"><h1 class="title">{greeting}, {safe(name)}</h1>'
                f'<p>{date_text} · light or dark mode: ⋮ menu, top right</p></div>',
                unsafe_allow_html=True)
    if st.session_state.demo:
        message, button = st.columns([5, 1], vertical_alignment="center")
        message.markdown('<p class="swa-demo">You\'re viewing the <b>demo week</b>: invented '
                         'students and courses, not your own data.</p>', unsafe_allow_html=True)
        button.button("Exit demo", icon=":material/close:", width="stretch",
                      on_click=clear_everything)
    with st.container(key="swa_nav"):
        for column, (page, label, icon) in zip(st.columns(len(PAGES)), PAGES):
            active = st.session_state.page == page
            column.button(label, icon=icon, key=f"nav_{page}", width="stretch",
                          type="primary" if active else "secondary",
                          on_click=go_to, args=(page,))
    st.write("")


# ----------------------------------------------------------------------------
# Home: welcome steps (no data yet) or the three dashboard cards
# ----------------------------------------------------------------------------

def draw_welcome():
    st.subheader("Welcome! Let's set up your week", anchor=False)
    st.write("This tool answers three questions in one place: when can my group meet, "
             "what is due next, and how many classes can I still miss?")
    steps = [("1", "Log in once", "Your student ID gets your timetable, attendance and deadlines."),
             ("2", "Or upload files", "A timetable screenshot and the Smart LMS calendar (.ics)."),
             ("3", "Add your teammates", "Upload their timetable files in the Meet page.")]
    for column, (number, title, text) in zip(st.columns(3), steps):
        column.markdown(f'<div class="swa-step"><span class="num">{number}</span><br>'
                        f'<b>{title}</b><p>{text}</p></div>', unsafe_allow_html=True)
    st.write("")
    left, right, _ = st.columns([1, 1, 2])
    left.button("Try the demo week", icon=":material/play_arrow:", type="primary",
                width="stretch", on_click=load_demo_week)
    right.button("Add my data", icon=":material/upload_file:", width="stretch",
                 on_click=go_to, args=("data",))
    st.caption("The demo uses invented students, so no password is needed.")


def meet_card():
    group = st.session_state.group
    card = {"label": ":material/groups: Next group meeting", "page": "meet", "button": "Open meetings"}
    if len(group) < 2:
        return dict(card, big="Add your teammates", badge=("Need 2 or more timetables", "grey"),
                    sub=f"{len(group)} timetable loaded so far", button="Add teammates")
    try:
        everyone, almost = core.find_meeting_slots(group)
    except core.InputError as problem:
        return dict(card, big="Check the settings", badge=(str(problem), "red"), sub="")
    if everyone:
        slot = everyone[0]
        return dict(card, big=f'{slot["day"]} {core.format_time(slot["start"])}',
                    badge=(f'Everyone free · {core.format_duration(slot["minutes"])}', "green"),
                    sub=f'{len(everyone)} times work for all {len(group)} people')
    if almost:
        slot = almost[0]
        return dict(card, big=f'{slot["day"]} {core.format_time(slot["start"])}',
                    badge=("Second choice: one person busy", "amber"),
                    sub=f'{slot["busy"][0]} has class then')
    return dict(card, big="No common time", badge=("Try a shorter meeting", "red"), sub="")


def deadline_card():
    card = {"label": ":material/schedule: Due next", "page": "deadlines", "button": "Open deadlines"}
    if not st.session_state.deadlines:
        return dict(card, big="Add your deadlines", badge=("No deadlines yet", "grey"),
                    sub="Log in, or upload the Smart LMS calendar", page="data", button="Add deadlines")
    upcoming = [item for item in rated_deadlines() if item["level"] != "OVERDUE"]
    if not upcoming:
        return dict(card, big="Nothing due", badge=("All clear", "green"), sub="")
    first = upcoming[0]
    urgent = sum(item["level"] == "URGENT" for item in upcoming)
    return dict(card, big=first["title"],
                badge=(core.time_left_text(first["hours_left"]), DEADLINE_COLOURS[first["level"]]),
                sub=f'{first["course"]} · {urgent} due within 2 days')


def attendance_card():
    card = {"label": ":material/fact_check: Attendance", "page": "attendance",
            "button": "Open attendance"}
    if not st.session_state.attendance:
        return dict(card, big="Add attendance", badge=("No attendance yet", "grey"),
                    sub="Log in or upload a file", page="data", button="Add attendance")
    results = checked_attendance()
    at_risk = [r for r in results if r["status"] in ("FAILED", "DANGER", "WARNING")]
    if not at_risk:
        return dict(card, big="All courses safe", badge=(f"{len(results)} courses", "green"), sub="")
    worst = at_risk[0]
    big = "1 course needs care" if len(at_risk) == 1 else f"{len(at_risk)} courses need care"
    return dict(card, big=big, badge=(miss_text(worst), ATTENDANCE_COLOURS[worst["status"]]),
                sub=f'Most at risk: {worst["course"]}')


def draw_card(column, card):
    text, colour = card["badge"]
    with column:
        st.markdown(card["label"])
        st.markdown(f'<div class="swa-card"><p class="big">{safe(card["big"])}</p>'
                    f'{badge(text, colour)}<p class="sub">{safe(card["sub"])}</p></div>',
                    unsafe_allow_html=True)
        st.button(card["button"], key=f'card_{card["label"]}', icon=":material/arrow_forward:",
                  width="stretch", on_click=go_to, args=(card["page"],))


def draw_heads_up():
    """One plain sentence about what needs attention this week."""
    notes = []
    if st.session_state.deadlines:
        urgent = sum(item["level"] == "URGENT" for item in rated_deadlines())
        if urgent:
            notes.append(f"{urgent} deadline{'s' if urgent != 1 else ''} in the next 48 hours")
    if st.session_state.attendance:
        risky = sum(r["status"] in ("FAILED", "DANGER") for r in checked_attendance())
        if risky:
            notes.append(f"{risky} course{'s' if risky != 1 else ''} close to the absence limit")
    if notes:
        st.warning("Please check: " + " and ".join(notes) + ".", icon=":material/warning:")
    else:
        st.success("Nothing urgent this week.", icon=":material/check_circle:")


def draw_home():
    if not has_any_data():
        draw_welcome()
        return
    draw_heads_up()
    for column, card in zip(st.columns(3), (meet_card(), deadline_card(), attendance_card())):
        draw_card(column, card)


# ----------------------------------------------------------------------------
# Meet page
# ----------------------------------------------------------------------------

def week_grid_html(timetables, days, earliest, latest):
    """Draw the week as a coloured table: green = everyone free."""
    start, end = core.parse_time(earliest), core.parse_time(latest)
    rows = ['<table class="swa-grid"><caption class="swa-sr">Who is busy in each half hour of '
            'the week</caption><tr><th scope="col"><span class="swa-sr">Time</span></th>'] + \
           [f'<th scope="col">{day}</th>' for day in days] + ["</tr>"]
    for minute in range(start, end, 30):
        rows.append(f'<tr><th scope="row" class="time">{core.format_time(minute)}</th>')
        for day in days:
            busy = [name for name, blocks in timetables.items()
                    if any(b["day"] == day and b["start"] < minute + 30 and b["end"] > minute for b in blocks)]
            if not busy:
                kind, text = "free", "free"
            elif len(busy) == 1:
                kind, text = "one", safe(busy[0].split()[0])
            else:
                kind, text = "many", f"{len(busy)} busy"
            rows.append(f'<td class="{kind}">{text}</td>')
        rows.append("</tr>")
    rows.append("</table>")
    return "".join(rows)


# File names from phones and screenshot tools say nothing about the person.
GENERIC_FILE_NAMES = ("photo", "image", "img", "screenshot", "screen", "kakaotalk", "picture",
                      "pic", "scan", "file", "download", "untitled", "timetable", "schedule")


def unique_name(name):
    """Add a number when the name is taken, so no timetable replaces another one."""
    group = st.session_state.group
    if name not in group:
        return name
    number = 2
    while f"{name} {number}" in group:
        number += 1
    return f"{name} {number}"


def teammate_name(file_name):
    """mina.png -> Mina, but photo_123.jpg -> Teammate 1 (the student can rename it)."""
    name = core.member_name_from_file(file_name)
    if name.lower().startswith(GENERIC_FILE_NAMES) or name[:1].isdigit():
        number = 1
        while f"Teammate {number}" in st.session_state.group:
            number += 1
        return f"Teammate {number}"
    return unique_name(name)


def add_team_uploads():
    group = st.session_state.group
    with st.expander("Add teammates' timetables", icon=":material/person_add:",
                     expanded=len(group) < 2):
        uploads = st.file_uploader("Screenshots or .csv files. A file called mina.png becomes "
                                   "Mina. You can change every name in Your group below.",
                                   type=["png", "jpg", "jpeg", "csv"], accept_multiple_files=True,
                                   key=f"team_files_{st.session_state.upload_round}")
        for upload in uploads or []:
            if not is_new_upload(upload, "team"):
                continue
            try:
                blocks = core.load_timetable(io.BytesIO(upload.getvalue()), upload.name)
            except core.InputError as problem:
                st.error(f"{upload.name}: {problem}")
                continue
            name = teammate_name(upload.name)
            group[name] = blocks
            st.session_state.member_sources[name] = upload.name


def rename_member(old_name):
    """Called when a name box in Your group is changed."""
    key = f"rename_{old_name}"
    new_name = st.session_state[key].strip()
    group = st.session_state.group
    if new_name == old_name:
        return
    if not new_name or new_name in group:
        st.session_state[key] = old_name                   # put the old name back
        st.session_state.member_problem = (f'"{new_name}" is already in the group. Pick another name.'
                                           if new_name else "A name can't be empty.")
        return
    st.session_state.group = {(new_name if name == old_name else name): blocks
                              for name, blocks in group.items()}
    sources = st.session_state.member_sources
    if old_name in sources:
        sources[new_name] = sources.pop(old_name)
    if st.session_state.my_name == old_name:
        st.session_state.my_name = new_name


def remove_member(name):
    st.session_state.group = {other: blocks for other, blocks in st.session_state.group.items()
                              if other != name}
    st.session_state.member_sources.pop(name, None)


def draw_group_members():
    """Every member with a name box, where the timetable came from, and a remove button."""
    with st.container(border=True):
        st.markdown("**Your group** (type in a box to change a name)")
        problem = st.session_state.pop("member_problem", None)
        if problem:
            st.error(problem)
        for name, blocks in list(st.session_state.group.items()):
            key = f"rename_{name}"
            if key not in st.session_state:
                st.session_state[key] = name
            is_me = name == st.session_state.my_name
            name_box, info, remove = st.columns([3, 3, 2], vertical_alignment="center")
            name_box.text_input(f"Name of {name}", key=key, on_change=rename_member, args=(name,),
                                label_visibility="collapsed")
            source = st.session_state.member_sources.get(name)
            details = [f"{len(blocks)} classes"] + (["you"] if is_me else []) + \
                      ([f"from {source}"] if source else [])
            info.caption(" · ".join(details))
            if not is_me:
                remove.button(f"Remove {name}", key=f"remove_{name}", icon=":material/delete:",
                              on_click=remove_member, args=(name,))


def draw_slot_cards(slots):
    for column, slot in zip(st.columns(3), slots[:3]):
        column.markdown(f'<div class="swa-card" style="min-height:0">'
                        f'<p class="label">{slot["day"]}</p>'
                        f'<p class="big">{core.format_time(slot["start"])} - {core.format_time(slot["end"])}</p>'
                        f'{badge(core.format_duration(slot["minutes"]), "green")}</div>',
                        unsafe_allow_html=True)


def draw_meet_page():
    st.subheader("When can the group meet?", anchor=False)
    add_team_uploads()
    if st.session_state.group:
        draw_group_members()
    group = st.session_state.group
    if len(group) < 2:
        st.info("Add at least two timetables: yours in **My data** and your teammates' above.",
                icon=":material/info:")
        return

    hours = [f"{hour:02d}:00" for hour in range(7, 24)]
    with st.container(border=True):
        first, second, third, fourth = st.columns(4)
        earliest = first.selectbox("Earliest start", hours, index=hours.index("09:00"))
        latest = second.selectbox("Latest end", hours, index=hours.index("18:00"))
        min_minutes = third.selectbox("Meeting length (minutes)", [30, 60, 90, 120, 180], index=1)
        weekend = fourth.toggle("Include Saturday", value=False)
    days = core.DAYS[:6] if weekend else core.DAYS[:5]

    try:
        everyone, almost = core.find_meeting_slots(group, earliest, latest, min_minutes, days)
    except core.InputError as problem:
        st.error(str(problem))
        return

    if everyone:
        st.markdown(f"**Best times for everyone** ({len(everyone)} found)")
        draw_slot_cards(everyone)
        if len(everyone) > 3:
            with st.expander(f"Show all {len(everyone)} times"):
                for slot in everyone:
                    st.write(f'{slot["day"]} {core.format_time(slot["start"])} - '
                             f'{core.format_time(slot["end"])} ({core.format_duration(slot["minutes"])})')
    else:
        st.warning("No time works for everyone with these settings.", icon=":material/warning:")
        if almost:
            st.markdown("**Second choice: times when only one person is busy**")
            for slot in almost[:5]:
                st.write(f'{slot["day"]} {core.format_time(slot["start"])} - {core.format_time(slot["end"])} '
                         f'({core.format_duration(slot["minutes"])}), busy: {slot["busy"][0]}')
        else:
            st.write("Try a shorter meeting, a longer day or Saturday.")

    st.markdown("**The week at a glance** " + badge("free", "green") + " " + badge("one person busy", "amber")
                + " " + badge("2+ busy", "blue"), unsafe_allow_html=True)
    st.markdown(week_grid_html(group, days, earliest, latest), unsafe_allow_html=True)
    st.write("")
    st.markdown("**Message for the group chat** (use the copy button)")
    st.code(core.group_message(everyone), language="text")


# ----------------------------------------------------------------------------
# Deadlines page
# ----------------------------------------------------------------------------

def draw_deadline_row(item):
    left = "overdue" if item["level"] == "OVERDUE" else core.time_left_text(item["hours_left"])
    notes = [f'{item["course"]} · due {item["due"].strftime("%a %d %b, %H:%M")}']
    if "free_hours" in item:
        notes.append(f'{item["free_hours"]} free daytime hours before it (classes removed)')
    if item["midnight"] and item["level"] != "OVERDUE":
        notes.append("due at midnight, so finish it the evening before")
    colour = DEADLINE_COLOURS[item["level"]]
    st.markdown(f'<div class="swa-row" style="border-left:6px solid {BAR_COLOURS[colour]};">'
                f'<p class="title">{safe(item["title"])} &nbsp;{badge(left, colour)}</p>'
                f'<p class="meta">{safe(" · ".join(notes))}</p></div>', unsafe_allow_html=True)


def draw_deadlines_page():
    st.subheader("What is due next?", anchor=False)
    if not st.session_state.deadlines:
        st.info("No deadlines yet. The quickest way: log in with your student ID in **My data**.\n\n"
                "Or add the calendar file by hand:\n"
                "1. Open Smart LMS and go to **Calendar**.\n"
                "2. Click **Export calendar**, choose *All events* and *Recent and next 60 days*.\n"
                "3. Click **Export** and upload the file in **My data**.", icon=":material/info:")
        st.button("Go to My data", icon=":material/upload_file:", on_click=go_to, args=("data",))
        return
    rated = rated_deadlines()
    for column, level in zip(st.columns(4), DEADLINE_LABELS):
        count = sum(item["level"] == level for item in rated)
        column.markdown(f'<div class="swa-tile"><p class="num">{count}</p>'
                        f'<p class="label">{DEADLINE_LABELS[level]}</p></div>', unsafe_allow_html=True)
    st.write("")
    show_old = st.toggle("Show overdue entries", value=False)
    for item in rated:
        if item["level"] == "OVERDUE" and not show_old:
            continue
        draw_deadline_row(item)


# ----------------------------------------------------------------------------
# Attendance page
# ----------------------------------------------------------------------------

def draw_attendance_row(result):
    colour = ATTENDANCE_COLOURS[result["status"]]
    label = badge(ATTENDANCE_LABELS[result["status"]], colour)
    if result["status"] == "NO DATA":
        st.markdown(f'<div class="swa-row"><p class="title">{safe(result["course"])} &nbsp;{label}</p>'
                    f'<p class="meta">No class sessions recorded yet.</p></div>', unsafe_allow_html=True)
        return
    used = result["counted_absences"] / result["allowed"] if result["allowed"] else 1.0
    width = int(min(1.0, max(0.0, used)) * 100)
    lates = result["lates_to_next"]
    details = (f'{result["counted_absences"]} of {result["allowed"]} allowed absences used '
               f'({result["absent"]} absent, {result["late"]} late, {result["early"]} left early, '
               f'{result["excused"]} excused). {lates} more {"late arrival" if lates == 1 else "late arrivals"} '
               f'until the next one counts as an absence.')
    st.markdown(f'<div class="swa-row"><div class="head"><p class="title">{safe(result["course"])} '
                f'&nbsp;{label}</p><p class="title">{safe(miss_text(result))}</p></div>'
                f'<div class="swa-bar" role="img" aria-label="{width}% of allowed absences used">'
                f'<span style="width:{width}%;background:{BAR_COLOURS[colour]};"></span></div>'
                f'<p class="meta">{safe(details)}</p></div>', unsafe_allow_html=True)


def draw_attendance_page():
    st.subheader("How many classes can I still miss?", anchor=False)
    if not st.session_state.attendance:
        st.info("No attendance added yet. Log in to the attendance site in **My data**, "
                "or try the demo week.", icon=":material/info:")
        st.button("Go to My data", icon=":material/upload_file:", on_click=go_to, args=("data",))
        return
    with st.expander("How is this counted?", icon=":material/help:"):
        st.write("Woosong rule: a course is failed when absences are more than 1/3 of all class "
                 "sessions. Three late arrivals (or early leaves) count as one absence. "
                 "Excused absences do not count.")
    results = checked_attendance()
    for result in results:
        draw_attendance_row(result)
    if any(r["status"] == "FAILED" for r in results):
        st.error("A course is over the limit. Talk to your professor as soon as possible.",
                 icon=":material/error:")


# ----------------------------------------------------------------------------
# My data page: getting the data in
# ----------------------------------------------------------------------------

def draw_data_status():
    me = st.session_state.group.get(st.session_state.my_name)
    items = [("Your timetable", me is not None),
             ("Smart LMS calendar", bool(st.session_state.deadlines)),
             ("Attendance", bool(st.session_state.attendance)),
             ("Teammates", len(st.session_state.group) >= 2)]
    for column, (label, done) in zip(st.columns(4), items):
        mark = badge("Added", "green") if done else badge("Not yet", "grey")
        column.markdown(f'<div class="swa-tile"><p class="label">{label}</p>{mark}</div>',
                        unsafe_allow_html=True)


def get_from_attendance_site(student_id, password):
    """Timetable and attendance from att.wsu.ac.kr. Returns the problem text, or None."""
    try:
        with st.spinner("Getting your timetable and attendance..."):
            result = core.fetch_from_site(student_id, password)
    except core.InputError as problem:
        return f"Attendance site: {problem}"
    name = result["name"] or "Me"
    st.session_state.my_name = name
    st.session_state.group[name] = result["timetable"]
    st.session_state.attendance = result["attendance"]
    st.success(f"Timetable and attendance loaded: {len(result['attendance'])} courses for {name}.")
    if result["skipped"]:
        st.info("These courses had no class times or attendance to read and were left out: "
                + ", ".join(result["skipped"]) + ".")
    return None


def get_from_smart_lms(student_id, password):
    """Deadlines from smart.wsu.ac.kr and nsmart.wsu.ac.kr. Returns the problems if both failed."""
    with st.spinner("Getting your deadlines from Smart LMS (smart and nsmart)..."):
        deadlines, problems = core.fetch_all_deadlines(student_id, password)
    if len(problems) == len(core.DEADLINE_SITES):      # neither site worked
        return problems
    st.session_state.deadlines = deadlines
    st.success(f"Deadlines loaded from Smart LMS: {len(deadlines)} entries.")
    for problem in problems:                           # the other site still worked
        st.info(problem)
    return []


def show_login_problems(problems):
    """One box for everything that went wrong, instead of one box per site."""
    if not problems:
        return
    if len(problems) == 1:
        st.warning(problems[0])
        return
    st.error("The sites did not give any data:\n" + "\n".join(f"- {text}" for text in problems))


def draw_login_box():
    with st.container(border=True):
        st.markdown("**Option 1: log in once, get everything**")
        st.caption("Gets your timetable and attendance from att.wsu.ac.kr and your deadlines "
                   "from smart.wsu.ac.kr and nsmart.wsu.ac.kr. Your password is used for these requests only and is never saved.")
        with st.form("login_form", clear_on_submit=True, border=False):
            # autocomplete off: the browser should not suggest saved IDs or passwords here
            student_id = st.text_input("Student ID", autocomplete="off")
            password = st.text_input("Password", type="password", autocomplete="off")
            pressed = st.form_submit_button("Get my data", icon=":material/login:", type="primary")
        if not pressed:
            return
        if not student_id.strip() or not password:
            st.error("Type both your student ID and your password.")
            return
        if st.session_state.demo:              # never mix the demo students with real data
            clear_everything()
            st.session_state.page = "data"
        problems = [get_from_attendance_site(student_id, password)]
        problems = [text for text in problems if text] + get_from_smart_lms(student_id, password)
        show_login_problems(problems)


def load_upload(upload, label, loader, message):
    """Run one loader on an uploaded file and show a friendly result."""
    if upload is None or not is_new_upload(upload, label):
        return
    try:
        count = loader(io.BytesIO(upload.getvalue()), upload.name)
        st.success(message.format(count))
    except core.InputError as problem:
        st.session_state.loaded_files.discard((label, upload.name, upload.size))
        st.error(str(problem))


def draw_upload_box():
    upload_round = st.session_state.upload_round
    with st.container(border=True):
        st.markdown("**Option 2: upload your files**")
        typed_name = st.text_input("Your name", value=st.session_state.my_name)

        def save_timetable(data, file_name):
            name = typed_name.strip() or "Me"
            blocks = core.load_timetable(data, file_name)
            st.session_state.my_name = name
            st.session_state.group[name] = blocks
            return len(blocks)

        def save_calendar(data, _):
            st.session_state.deadlines = core.load_deadlines(data)
            return len(st.session_state.deadlines)

        def save_attendance(data, _):
            st.session_state.attendance = core.load_attendance_csv(data)
            return len(st.session_state.attendance)

        load_upload(st.file_uploader("Your timetable (screenshot or .csv)", type=["png", "jpg", "jpeg", "csv"],
                                     key=f"my_timetable_{upload_round}"),
                    "timetable", save_timetable, "Timetable loaded: {} class blocks.")
        load_upload(st.file_uploader("Smart LMS calendar (.ics)", type=["ics"],
                                     key=f"my_calendar_{upload_round}"),
                    "calendar", save_calendar, "Calendar loaded: {} entries.")
        load_upload(st.file_uploader("Attendance file (.csv, optional)", type=["csv"],
                                     key=f"my_attendance_{upload_round}"),
                    "attendance", save_attendance, "Attendance loaded: {} courses.")


def draw_data_page():
    st.subheader("My data", anchor=False)
    draw_data_status()
    st.write("")
    left, right = st.columns(2)
    with left:
        draw_login_box()
    with right:
        draw_upload_box()

    st.write("")
    first, second, third = st.columns(3)
    first.button("Try the demo week", icon=":material/play_arrow:", width="stretch",
                 on_click=load_demo_week)
    my_blocks = st.session_state.group.get(st.session_state.my_name)
    if my_blocks is not None:
        second.download_button("Save my timetable file", icon=":material/download:", width="stretch",
                               data=core.timetable_to_csv(my_blocks),
                               file_name=f"{st.session_state.my_name.split()[0].lower()}_timetable.csv",
                               mime="text/csv", help="Send this file to your group. Never share passwords.")
    third.button("Clear everything", icon=":material/delete:", width="stretch",
                 on_click=clear_everything)


# ----------------------------------------------------------------------------
# Help page
# ----------------------------------------------------------------------------

def draw_help_page():
    st.subheader("How to use this tool", anchor=False)
    steps = [("1", "Add your data", "In My data, log in once with your student ID (timetable, "
              "attendance and deadlines), or upload a timetable screenshot and the Smart LMS calendar (.ics)."),
             ("2", "Add your team", "Every teammate saves a timetable file or a screenshot and "
              "sends it to you. Upload them in Meet. Share files, never passwords."),
             ("3", "Check your week", "Home shows the best meeting time, the next deadline and "
              "the course closest to the absence limit. Click a card for details.")]
    for column, (number, title, text) in zip(st.columns(3), steps):
        column.markdown(f'<div class="swa-step"><span class="num">{number}</span><br>'
                        f'<b>{title}</b><p>{text}</p></div>', unsafe_allow_html=True)
    st.write("")
    st.info("Light, dark or system mode: open the ⋮ menu in the top right corner and pick "
            "System, Light or Dark. System follows your computer's setting.",
            icon=":material/contrast:")
    st.info("Privacy: the app runs on your own computer. Nothing is sent anywhere except the "
            "login requests to the attendance site (att.wsu.ac.kr) and the two Smart LMS sites "
            "(smart.wsu.ac.kr and nsmart.wsu.ac.kr), and your password is never written to a file.",
            icon=":material/lock:")


# ----------------------------------------------------------------------------
# The page
# ----------------------------------------------------------------------------

DRAW_PAGE = {"home": draw_home, "meet": draw_meet_page, "deadlines": draw_deadlines_page,
             "attendance": draw_attendance_page, "data": draw_data_page, "help": draw_help_page}

start_memory()
st.markdown(STYLE, unsafe_allow_html=True)
draw_top_bar()
DRAW_PAGE.get(st.session_state.page, draw_home)()
