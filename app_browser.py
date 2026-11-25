"""
STUDY WEEK ASSISTANT - browser app

This file only draws the screens. All calculations are in project_code.py.

Layout: a greeting and a row of page tabs. Home shows the week as three ruled
lines (Meet, Deadlines, Attendance), and each line opens a full page.
The look (warm paper, ink and one deep coral) is in the styles/ folder.

Start it with:   streamlit run app_browser.py
(or run project_code.py and choose 1)
"""

import html
import importlib
import io
import math
import os
from datetime import datetime, timedelta

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

PAGES = [("home", "Home", ":material/home:"),
         ("meet", "Meet", ":material/groups:"),
         ("deadlines", "Deadlines", ":material/schedule:"),
         ("attendance", "Attendance", ":material/fact_check:"),
         ("data", "My data", ":material/upload_file:"),
         ("help", "Help", ":material/help:")]

# The look lives in styles/: tokens.css (colours, type, spacing), base.css and app.css.
STYLE_FILES = ("tokens.css", "base.css", "app.css")
STYLE_FOLDER = os.path.join(HERE, "styles")


def load_styles():
    """Read the three style files once, without their @import lines (the files are joined here)."""
    parts = []
    for file_name in STYLE_FILES:
        with open(os.path.join(STYLE_FOLDER, file_name), encoding="utf-8") as style_file:
            parts.append("".join(line for line in style_file if not line.startswith("@import")))
    return "<style>\n" + "\n".join(parts) + "\n</style>"


# Streamlit switches light and dark mode in the browser without rerunning this file.
# This small script reads the background Streamlit paints and tells the style files
# which mode is on (data-swa-mode on the page), at once and after every switch.
THEME_WATCH = """
<script>
(() => {
  if (window.swaThemeWatch) { window.swaThemeWatch(); return; }
  const root = document.documentElement;
  const isDark = (colour) => {
    const [r, g, b] = (colour.match(/[\\d.]+/g) || ["255", "255", "255"]).map(Number);
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 < 0.45;
  };
  const update = () => {
    const app = document.querySelector(".stApp");
    if (!app) return;
    root.dataset.swaMode = isDark(getComputedStyle(app).backgroundColor) ? "dark" : "light";
  };
  window.swaThemeWatch = update;
  new MutationObserver(() => requestAnimationFrame(update))
    .observe(document.head, {childList: true, subtree: true, characterData: true});
  new MutationObserver(() => requestAnimationFrame(update))
    .observe(document.body, {attributes: true, subtree: true, attributeFilter: ["class"]});
  update();
})();
</script>
"""


def draw_styles():
    """The style files, and the script that follows Streamlit's light or dark mode."""
    st.markdown(load_styles(), unsafe_allow_html=True)
    st.html(THEME_WATCH, unsafe_allow_javascript=True)


st.set_page_config(page_title="Study Week Assistant", page_icon=":material/calendar_month:", layout="wide",
                   initial_sidebar_state="auto")


def safe(text):
    """Make text from files safe to put inside our HTML."""
    return html.escape(str(text))


def badge(text, colour):
    """A small status tag. The colour name (green, amber, red, grey) becomes the tag's state colour."""
    return f'<span class="swa-tag {colour}">{safe(text)}</span>'


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
    name = st.session_state.my_name.split()[0] if st.session_state.my_name else ""
    hour = current_time().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    greeting = f"{greeting}, {safe(name)}" if name else greeting
    date_text = current_time().strftime("%A %d %B %Y")
    st.markdown(f'<div class="swa-head"><p class="swa-brand">Study Week Assistant</p>'
                f'<p class="date">{date_text}</p></div><h1 class="swa-greeting">{greeting}</h1>',
                unsafe_allow_html=True)
    # The pages, in the left sidebar. The open page is a "primary" button, marked in app.css.
    with st.sidebar, st.container(key="swa_nav"):
        for page, label, icon in PAGES:
            active = st.session_state.page == page
            st.button(label, icon=icon, key=f"nav_{page}", width="stretch",
                      type="primary" if active else "secondary",
                      on_click=go_to, args=(page,))
    if st.session_state.demo:
        message, button = st.columns([5, 1], vertical_alignment="center")
        message.markdown('<p class="swa-demo">You\'re viewing the <b>demo week</b>: invented '
                         'students and courses, not your own data.</p>', unsafe_allow_html=True)
        button.button("Exit demo", icon=":material/close:", width="stretch",
                      on_click=clear_everything)
    st.write("")


# ----------------------------------------------------------------------------
# Home: welcome steps (no data yet) or the week as three ruled lines
# ----------------------------------------------------------------------------

def steps_html(steps):
    """A numbered list of (title, text) steps."""
    items = "".join(f"<li><b>{title}.</b> {text}</li>" for title, text in steps)
    return f'<ol class="swa-steps">{items}</ol>'


def draw_welcome():
    steps = [("Log in once", "Your student ID gets your timetable and attendance. "
              "Paste your Smart LMS calendar links for deadlines."),
             ("Or upload files", "A timetable screenshot and the Smart LMS calendar (.ics)."),
             ("Add your teammates", "Upload their timetable files in the Meet page.")]
    with st.container(key="swa_sheet_welcome"):
        st.markdown(steps_html(steps), unsafe_allow_html=True)
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
                    badge=(f'Everyone free, {core.format_duration(slot["minutes"])}', "green"),
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
                sub=[first["course"], f"{urgent} due within 2 days"])


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


def draw_ledger_line(card):
    """One line of the week: what it is about, the answer, its status, and the page that explains it."""
    text, colour = card["badge"]
    title = card["label"].split(": ", 1)[-1]          # the label without its icon
    subs = card["sub"] if isinstance(card["sub"], list) else [card["sub"]]
    notes = "".join(f"<span>{safe(sub)}</span>" for sub in subs if sub)
    with st.container(key=f'swa_ledger_{card["page"]}_{title.split()[0].lower()}'):
        words, action = st.columns([4, 1], vertical_alignment="center")
        words.markdown(f'<div class="swa-entry"><p class="label">{safe(title)}</p>'
                       f'<p class="value">{safe(card["big"])}</p>'
                       f'<p class="note">{badge(text, colour)}{notes}</p></div>',
                       unsafe_allow_html=True)
        action.button(card["button"], key=f'card_{card["label"]}', width="stretch",
                      on_click=go_to, args=(card["page"],))


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


def week_days(now):
    """Monday to Sunday of the week that holds now, as dates."""
    monday = (now - timedelta(days=now.weekday())).date()
    return [monday + timedelta(days=offset) for offset in range(7)]


def meeting_slots_for_home():
    """The times the whole group is free (default settings), or none when it can't be worked out."""
    if len(st.session_state.group) < 2:
        return []
    try:
        everyone, _ = core.find_meeting_slots(st.session_state.group)
    except core.InputError:
        return []
    return everyone


def time_left_parts(item):
    """How long until a deadline, as (number, words): (3, "days left"), (5, "hours left"), (2, "days overdue")."""
    hours = item["hours_left"]
    if hours < 0:
        days = max(1, math.ceil(-hours / 24))
        return days, "day overdue" if days == 1 else "days overdue"
    if hours < 24:
        whole = int(hours)
        return whole, "hour left" if whole == 1 else "hours left"
    days = int(hours // 24)
    return days, "day left" if days == 1 else "days left"


def time_left_label(item):
    number, words = time_left_parts(item)
    return f"{number} {words}"


def day_items_html(day, deadlines, slots, today):
    """What happens on one day: deadlines by time, then the times the group can meet."""
    items = []
    for item in sorted((d for d in deadlines if d["due"].date() == day), key=lambda d: d["due"]):
        colour = DEADLINE_COLOURS[item["level"]]
        items.append(f'<li class="swa-due {colour}"><span class="time">{item["due"].strftime("%H:%M")}</span>'
                     f'<b>{safe(item["title"])}</b><span class="course">{safe(item["course"])}</span>'
                     f'<span class="left">{time_left_label(item)}</span></li>')
    if day >= today:
        now = current_time()
        minute_now = now.hour * 60 + now.minute if day == today else 0
        day_slots = sorted((s for s in slots if s["day"] == core.DAYS[day.weekday()]
                            and s["end"] > minute_now), key=lambda s: s["start"])
        for slot in day_slots[:2]:
            items.append(f'<li class="swa-meet"><span class="time">{core.format_time(slot["start"])} - '
                         f'{core.format_time(slot["end"])}</span>Group can meet</li>')
    if not items:
        return '<p class="swa-none">Nothing due</p>'
    return f'<ul>{"".join(items)}</ul>'


def week_strip_html():
    """The signature of the app: this week as a row of days, today marked."""
    now = current_time()
    today = now.date()
    days = week_days(now)
    deadlines = rated_deadlines() if st.session_state.deadlines else []
    slots = meeting_slots_for_home()
    busy_weekend = [day for day in days[5:]
                    if any(item["due"].date() == day for item in deadlines)]
    shown = days[:5] + busy_weekend
    columns = []
    for day in shown:
        is_today = day == today
        mark = '<p class="swa-today">Today</p>' if is_today else ""
        columns.append(f'<section class="swa-day{" today" if is_today else ""}">'
                       f'<div class="swa-day-head"><h3>{core.DAYS[day.weekday()]} {day.day}</h3>{mark}</div>'
                       f'{day_items_html(day, deadlines, slots, today)}</section>')
    # Deadlines before or after this week, so none is hidden: soonest first, with days left
    outside = sorted((item for item in deadlines
                      if item["due"].date() < days[0] or item["due"].date() > days[-1]),
                     key=lambda item: item["due"])
    note = ""
    if outside:
        rows = "".join(f'<li class="{DEADLINE_COLOURS[item["level"]]}"><span class="left">{time_left_label(item)}</span>'
                       f'<b>{safe(item["title"])}</b><span class="course">{safe(item["course"])}, '
                       f'due {item["due"].strftime("%a %d %b, %H:%M")}</span></li>' for item in outside)
        note = f'<div class="swa-outside"><h3>Outside this week</h3><ul>{rows}</ul></div>'

    span = f'{days[0].day} to {days[-1].strftime("%d %B").lstrip("0")}'
    return (f'<div class="swa-week-head"><h2>This week</h2><p>{span}</p></div>'
            f'<div class="swa-week" style="--days:{len(shown)}">{"".join(columns)}</div>{note}')


def draw_home():
    if not has_any_data():
        draw_welcome()
        return
    draw_heads_up()
    with st.container(key="swa_sheet_strip"):
        st.markdown(week_strip_html(), unsafe_allow_html=True)
    with st.container(key="swa_sheet_week"):
        for card in (meet_card(), deadline_card(), attendance_card()):
            draw_ledger_line(card)


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
    return '<div class="swa-scroll">' + "".join(rows) + "</div>"


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
    with st.container(key="swa_sheet_group"):
        st.subheader("Your group", anchor=False)
        st.caption("Type in a box to change a name.")
        problem = st.session_state.pop("member_problem", None)
        if problem:
            st.error(problem)
        for index, (name, blocks) in enumerate(list(st.session_state.group.items())):
            key = f"rename_{name}"
            if key not in st.session_state:
                st.session_state[key] = name
            is_me = name == st.session_state.my_name
            source = st.session_state.member_sources.get(name)
            details = [f"{len(blocks)} classes"] + (["you"] if is_me else [])
            details += [f"from {source}"] if source else []
            with st.container(key=f"swa_member_{index}"):
                st.text_input(f"Name of {name}", key=key, on_change=rename_member, args=(name,),
                              label_visibility="collapsed")
                st.caption(", ".join(details))
                if not is_me:
                    st.button(f"Remove {name}", key=f"remove_{name}", icon=":material/delete:",
                              type="tertiary", on_click=remove_member, args=(name,))


def slots_table_html(slots, with_busy=False):
    """Meeting times as a ruled table: day, time, length (and who is busy, for second choices)."""
    head = "<th>Day</th><th>Time</th><th>Length</th>" + ("<th>Busy</th>" if with_busy else "")
    rows = []
    for slot in slots:
        cells = (f'<td>{slot["day"]}</td>'
                 f'<td class="figure">{core.format_time(slot["start"])} - {core.format_time(slot["end"])}</td>'
                 f'<td>{core.format_duration(slot["minutes"])}</td>')
        if with_busy:
            cells += f'<td>{safe(slot["busy"][0])}</td>'
        rows.append(f"<tr>{cells}</tr>")
    return f'<table class="swa-table"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def draw_meeting_times(group, days, earliest, latest, min_minutes):
    """The best times, or the second choices, and the week grid. Returns the times for everyone."""
    try:
        everyone, almost = core.find_meeting_slots(group, earliest, latest, min_minutes, days)
    except core.InputError as problem:
        st.error(str(problem))
        return None
    with st.container(key="swa_sheet_times"):
        if everyone:
            st.subheader(f"Best times for everyone ({len(everyone)} found)", anchor=False)
            st.markdown(slots_table_html(everyone[:3]), unsafe_allow_html=True)
            if len(everyone) > 3:
                with st.expander(f"Show all {len(everyone)} times"):
                    st.markdown(slots_table_html(everyone), unsafe_allow_html=True)
        else:
            st.warning("No time works for everyone with these settings.", icon=":material/warning:")
            if almost:
                st.subheader("Second choice: times when only one person is busy", anchor=False)
                st.markdown(slots_table_html(almost[:5], with_busy=True), unsafe_allow_html=True)
            else:
                st.write("Try a shorter meeting, a longer day or Saturday.")
    with st.container(key="swa_sheet_grid"):
        st.subheader("The week at a glance", anchor=False)
        st.markdown('<p class="swa-legend"><span class="swa-key free">free</span> '
                    '<span class="swa-key one">one person busy</span> '
                    '<span class="swa-key many">2+ busy</span></p>', unsafe_allow_html=True)
        st.markdown(week_grid_html(group, days, earliest, latest), unsafe_allow_html=True)
    return everyone


def draw_meet_page():
    st.header("When can the group meet?", anchor=False)
    side, main = st.columns([1, 2.2], gap="large")
    with side:
        add_team_uploads()
        if st.session_state.group:
            draw_group_members()
    group = st.session_state.group
    with main:
        if len(group) < 2:
            st.info("Add at least two timetables: yours in **My data** and your teammates' "
                    "with **Add teammates' timetables**.",
                    icon=":material/info:")
            return
        hours = [f"{hour:02d}:00" for hour in range(7, 24)]
        with st.container(key="swa_settings"):
            first, second, third, fourth = st.columns([1, 1, 1.4, 1.4], vertical_alignment="bottom")
            earliest = first.selectbox("Earliest start", hours, index=hours.index("09:00"))
            latest = second.selectbox("Latest end", hours, index=hours.index("18:00"))
            min_minutes = third.selectbox("Meeting length (minutes)", [30, 60, 90, 120, 180], index=1)
            weekend = fourth.toggle("Include Saturday", value=False)
        days = core.DAYS[:6] if weekend else core.DAYS[:5]
        everyone = draw_meeting_times(group, days, earliest, latest, min_minutes)
        if everyone is None:
            return
        st.markdown("**Message for the group chat** (use the copy button)")
        st.code(core.group_message(everyone), language="text")


# ----------------------------------------------------------------------------
# Deadlines page
# ----------------------------------------------------------------------------

def deadline_line_html(item):
    """One deadline: its title and course, when it is due, and how much time is left."""
    number, words = time_left_parts(item)
    meta = [item["course"], f'Due {item["due"].strftime("%a %d %b, %H:%M")}']
    notes = []
    if "free_hours" in item:
        notes.append(f'{item["free_hours"]} free daytime hours before it (classes removed).')
    if item["midnight"] and item["level"] != "OVERDUE":
        notes.append("Due at midnight, so finish it the evening before.")
    colour = DEADLINE_COLOURS[item["level"]]
    meta_html = "".join(f"<span>{safe(part)}</span>" for part in meta)
    notes_html = f'<p class="meta">{safe(" ".join(notes))}</p>' if notes else ""
    return (f'<div class="swa-line swa-deadline"><p class="swa-left {colour}">'
            f'<span class="num">{number}</span><span class="unit">{words}</span></p>'
            f'<div><p class="title">{safe(item["title"])}</p>'
            f'<p class="meta">{meta_html}</p>{notes_html}</div></div>')


def draw_deadlines_page():
    st.header("What is due next?", anchor=False)
    if not st.session_state.deadlines:
        st.info("No deadlines yet. The quickest way: log in with your student ID in **My data**.\n\n"
                "Or add the calendar file by hand:\n"
                "1. Open Smart LMS and go to **Calendar**.\n"
                "2. Click **Export calendar**, choose *All events* and *Recent and next 60 days*.\n"
                "3. Click **Export** and upload the file in **My data**.", icon=":material/info:")
        st.button("Go to My data", icon=":material/upload_file:", on_click=go_to, args=("data",))
        return
    rated = sorted(rated_deadlines(), key=lambda item: item["due"])
    overdue = sum(item["level"] == "OVERDUE" for item in rated)
    show_old = st.toggle(f"Show overdue entries ({overdue})", value=False)
    # One group per due window: overdue (when switched on), within 2 days, this week, later
    groups = []
    for level, label in DEADLINE_LABELS.items():
        if level == "OVERDUE" and not show_old:
            continue
        items = [item for item in rated if item["level"] == level]
        if items:
            lines = "".join(deadline_line_html(item) for item in items)
            groups.append(f'<section class="swa-group"><h3>{label} ({len(items)})</h3>'
                          f'<div class="swa-lines">{lines}</div></section>')
    if groups:
        with st.container(key="swa_sheet_deadlines"):
            st.markdown("".join(groups), unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Attendance page
# ----------------------------------------------------------------------------

def attendance_line_html(result):
    """One course: its status, how many absences are left, a bar of the absences used, and the counts."""
    colour = ATTENDANCE_COLOURS[result["status"]]
    label = badge(ATTENDANCE_LABELS[result["status"]], colour)
    head = (f'<div><p class="title">{safe(result["course"])}</p></div>'
            f'<div class="side">{label}</div>')
    if result["status"] == "NO DATA":
        return (f'<div class="swa-line">{head}'
                f'<p class="meta wide">No class sessions recorded yet.</p></div>')
    used = result["counted_absences"] / result["allowed"] if result["allowed"] else 1.0
    width = int(min(1.0, max(0.0, used)) * 100)
    lates = result["lates_to_next"]
    details = (f'{result["counted_absences"]} of {result["allowed"]} allowed absences used '
               f'({result["absent"]} absent, {result["late"]} late, {result["early"]} left early, '
               f'{result["excused"]} excused). {lates} more {"late arrival" if lates == 1 else "late arrivals"} '
               f'until the next one counts as an absence.')
    return (f'<div class="swa-line">{head}'
            f'<p class="wide remain">{safe(miss_text(result))}</p>'
            f'<div class="swa-bar wide" role="img" aria-label="{width}% of allowed absences used">'
            f'<span class="{colour}" style="width:{width}%"></span></div>'
            f'<p class="meta wide">{safe(details)}</p></div>')


def draw_attendance_page():
    st.header("How many classes can I still miss?", anchor=False)
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
    if any(r["status"] == "FAILED" for r in results):
        st.error("A course is over the limit. Talk to your professor as soon as possible.",
                 icon=":material/error:")
    with st.container(key="swa_sheet_attendance"):
        lines = "".join(attendance_line_html(result) for result in results)
        st.markdown(f'<div class="swa-lines">{lines}</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# My data page: getting the data in
# ----------------------------------------------------------------------------

def draw_data_status():
    me = st.session_state.group.get(st.session_state.my_name)
    items = [("Your timetable", me is not None),
             ("Smart LMS calendar", bool(st.session_state.deadlines)),
             ("Attendance", bool(st.session_state.attendance)),
             ("Teammates", len(st.session_state.group) >= 2)]
    checks = "".join(f'<li>{label} {badge("Added", "green") if done else badge("Not yet", "grey")}</li>'
                     for label, done in items)
    st.markdown(f'<ul class="swa-checks">{checks}</ul>', unsafe_allow_html=True)


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
    with st.container(key="swa_sheet_login"):
        st.subheader("Option 1: log in once", anchor=False)
        st.caption("Gets your timetable and attendance from att.wsu.ac.kr, and tries your deadlines "
                   "from smart.wsu.ac.kr and nsmart.wsu.ac.kr (until passkey login is required). "
                   "Your password is used for these requests only and is never saved.")
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
        attendance_problem = get_from_attendance_site(student_id, password)
        lms_problems = get_from_smart_lms(student_id, password)
        if attendance_problem:
            show_login_problems([attendance_problem] + lms_problems)
        elif lms_problems:                     # attendance worked; Smart LMS now needs a passkey
            st.info("Deadlines could not be loaded with this login:\n"
                    + "\n".join(f"- {text}" for text in lms_problems)
                    + "\n\nSmart LMS now asks for a passkey, so use the calendar links below.",
                    icon=":material/info:")


LINK_STEPS = ("**smart.wsu.ac.kr:** open **Calendar**, click **Export calendar**, choose *All events* "
              "and *Recent and next 60 days*, click **Get calendar URL** and copy the link.\n\n"
              "**nsmart.wsu.ac.kr:** open **Calendar**, click **Calendar feed** (bottom right) "
              "and copy the link.\n\n"
              "Each link is personal, like a password: never share it.")


def draw_links_box():
    """Deadlines from the Smart LMS calendar links: no password, so it works with passkey login."""
    with st.container(key="swa_sheet_links"):
        st.subheader("Deadlines with passkey login: calendar links", anchor=False)
        st.caption("Smart LMS now asks for a passkey (I-ONE PASS), so this app cannot log in there. "
                   "Paste your personal calendar links instead; they work without a password.")
        with st.expander("Where do I find my calendar links?", icon=":material/help:"):
            st.markdown(LINK_STEPS)
        with st.form("links_form", border=False):
            # password fields: each link works like a password, so keep it off the screen
            smart_link = st.text_input("smart.wsu.ac.kr calendar link", type="password", autocomplete="off")
            nsmart_link = st.text_input("nsmart.wsu.ac.kr calendar link", type="password", autocomplete="off")
            pressed = st.form_submit_button("Get my deadlines", icon=":material/event:", type="primary")
        if not pressed:
            return
        if not smart_link.strip() and not nsmart_link.strip():
            st.error("Paste at least one calendar link.")
            return
        if st.session_state.demo:              # never mix the demo students with real data
            clear_everything()
            st.session_state.page = "data"
        with st.spinner("Getting your deadlines from the calendar links..."):
            deadlines, problems = core.fetch_deadlines_from_links([smart_link, nsmart_link])
        if deadlines or not problems:
            st.session_state.deadlines = deadlines
            st.success(f"Deadlines loaded from your calendar links: {len(deadlines)} entries.")
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
    with st.container(key="swa_sheet_upload"):
        st.subheader("Option 2: upload your files", anchor=False)
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
    st.header("My data", anchor=False)
    draw_data_status()
    st.write("")
    left, right = st.columns(2, gap="large")
    with left:
        draw_login_box()
        st.write("")
        draw_links_box()
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
    st.header("How to use this tool", anchor=False)
    steps = [("Add your data", "In My data, log in once with your student ID (timetable, "
              "attendance and deadlines), or upload a timetable screenshot and the Smart LMS calendar (.ics)."),
             ("Add your team", "Every teammate saves a timetable file or a screenshot and "
              "sends it to you. Upload them in Meet. Share files, never passwords."),
             ("Check your week", "Home shows the best meeting time, the next deadline and "
              "the course closest to the absence limit. Open a line for the details.")]
    with st.container(key="swa_sheet_help"):
        st.markdown(steps_html(steps), unsafe_allow_html=True)
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
draw_styles()
draw_top_bar()
DRAW_PAGE.get(st.session_state.page, draw_home)()
