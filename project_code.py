"""
STUDY WEEK ASSISTANT  -  Python Programming for Business, Final Group Project
==============================================================================

The problem
    Every week students check three different places by hand to answer three
    questions:
        1. When can my group meet?            (timetable app)
        2. What is due next?                  (Smart LMS calendar)
        3. How many classes can I still miss? (electronic attendance site)

What this file does
    This file holds all the "thinking" of the tool. The screens (browser app and
    desktop window) only show the results that the functions here calculate.

    Part 1  Settings
    Part 2  Small helpers for times and days
    Part 3  Loading a timetable (file, screenshot, attendance site)
    Part 4  Meeting finder
    Part 5  Deadlines
    Part 6  Attendance checker
    Part 7  Talking to the Woosong attendance site
    Part 8  Text reports
    Part 9  Test runner and start menu

How to run
    python project_code.py          -> start menu
    python project_code.py --test   -> run every test case in test_cases/
"""

import csv
import html
import io
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

# ----------------------------------------------------------------------------
# PART 1 - SETTINGS (change the rules here, not inside the functions)
# ----------------------------------------------------------------------------

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Woosong rule: a course is failed when absences are MORE than 1/3 of all
# class hours (academic regulations, article 10).
ABSENCE_LIMIT_FRACTION = 1 / 3
# The attendance site counts 3 lates as 1 absence.
LATES_PER_ABSENCE = 3
# Our assumption: leaving early is counted the same way as being late.
EARLY_LEAVE_COUNTS_AS_LATE = True

# Korea has no summer time, so Korean time is always UTC+9.
KOREA_TIME = timezone(timedelta(hours=9))

ATTENDANCE_SITE = "https://att.wsu.ac.kr"
SMART_LMS_SITE = "https://smart.wsu.ac.kr"
# Deadlines asked from Smart LMS: from one week ago (to show overdue work)
# until 60 days ahead (the same period as the calendar export).
DEADLINE_DAYS_BACK = 7
DEADLINE_DAYS_AHEAD = 60
SMART_LMS_MAX_EVENTS = 50          # the most Smart LMS sends in one answer

# Status codes used by the attendance site (taken from the site's own code).
SITE_ABSENT_CODES = {"0", "1", "11", "21", "31"}
SITE_PRESENT_CODES = {"2", "12", "22", "32", "5", "6"}
SITE_LATE_CODES = {"3", "13", "23", "35", "36"}
SITE_EARLY_CODES = {"4", "14", "24"}
SITE_EXCUSED_CODES = {"92"}


class InputError(ValueError):
    """Raised when a file or value given by the user cannot be used.

    The message is always written for a student to read, not a programmer.
    """


class LoginError(InputError):
    """Raised when the attendance site refuses the login."""


# ----------------------------------------------------------------------------
# PART 2 - SMALL HELPERS FOR TIMES AND DAYS
# ----------------------------------------------------------------------------

def parse_time(text):
    """Turn "13:30" (or "1330") into minutes after midnight (810)."""
    cleaned = str(text).strip().replace(".", ":")
    if ":" not in cleaned and cleaned.isdigit() and len(cleaned) in (3, 4):
        cleaned = cleaned[:-2] + ":" + cleaned[-2:]
    parts = cleaned.split(":")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise InputError(f'"{text}" is not a time. Write times like 13:30.')
    hours, minutes = int(parts[0]), int(parts[1])
    if hours > 24 or minutes > 59 or (hours == 24 and minutes > 0):
        raise InputError(f'"{text}" is not a real time of day.')
    return hours * 60 + minutes


def format_time(minutes):
    """Turn minutes after midnight (810) back into "13:30"."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def format_duration(minutes):
    """Turn 150 into "2h 30min"."""
    hours, rest = divmod(int(minutes), 60)
    if hours and rest:
        return f"{hours}h {rest}min"
    if hours:
        return f"{hours}h"
    return f"{rest}min"


def parse_day(text):
    """Accept "Mon", "monday", "MON", "1" ... and return "Mon"."""
    cleaned = str(text).strip().lower()
    for number, day in enumerate(DAYS, start=1):
        if cleaned == str(number) or (len(cleaned) >= 3 and day.lower() == cleaned[:3]):
            return day
    raise InputError(f'"{text}" is not a day. Use Mon, Tue, Wed, Thu, Fri, Sat or Sun.')


def merge_blocks(blocks, max_gap=10):
    """Join blocks of the same course that touch each other on the same day.

    The attendance site stores one long class as several short pieces. This
    turns them back into one block per class.
    """
    ordered = sorted(blocks, key=lambda b: (DAYS.index(b["day"]), b["course"], b["start"]))
    merged = []
    for block in ordered:
        last = merged[-1] if merged else None
        if (last and last["day"] == block["day"] and last["course"] == block["course"]
                and block["start"] - last["end"] <= max_gap):
            last["end"] = max(last["end"], block["end"])
        else:
            merged.append(dict(block))
    return sorted(merged, key=lambda b: (DAYS.index(b["day"]), b["start"]))


# ----------------------------------------------------------------------------
# PART 3 - LOADING A TIMETABLE
# A timetable is a list of blocks: {"day": "Mon", "start": 600, "end": 720,
#                                   "course": "Marketing"}
# ----------------------------------------------------------------------------

def read_text_file(source):
    """Read text from a path, from uploaded bytes or from an open file."""
    if isinstance(source, bytes):
        raw = source
    elif hasattr(source, "read"):
        raw = source.read()
    else:
        with open(source, "rb") as handle:
            raw = handle.read()
    if isinstance(raw, str):
        return raw
    for encoding in ("utf-8-sig", "cp949", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise InputError("The file could not be read as text.")


def load_timetable_csv(source):
    """Read a timetable file with the columns: day,start,end,course.

    Every wrong line is collected, so the student sees all problems at once.
    """
    text = read_text_file(source)
    if not text.strip():
        raise InputError("The timetable file is empty.")
    reader = csv.DictReader(io.StringIO(text))
    columns = [name.strip().lower() for name in (reader.fieldnames or [])]
    missing = [name for name in ("day", "start", "end") if name not in columns]
    if missing:
        raise InputError("The timetable file needs the columns day,start,end,course. "
                         f"Missing: {', '.join(missing)}.")
    blocks, problems = [], []
    for line_number, row in enumerate(reader, start=2):
        row = {(key or "").strip().lower(): (value or "").strip() for key, value in row.items()}
        if not any(row.values()):
            continue  # skip blank lines
        try:
            day = parse_day(row["day"])
            start, end = parse_time(row["start"]), parse_time(row["end"])
            if end <= start:
                raise InputError(f'the class ends ({row["end"]}) before it starts ({row["start"]}).')
            blocks.append({"day": day, "start": start, "end": end,
                           "course": row.get("course") or "Class"})
        except InputError as problem:
            problems.append(f"line {line_number}: {problem}")
    if problems:
        raise InputError("The timetable file has mistakes:\n  " + "\n  ".join(problems))
    return merge_blocks(blocks)


def timetable_to_csv(blocks):
    """Write a timetable as text so it can be saved and shared with the group."""
    lines = ["day,start,end,course"]
    for block in blocks:
        course = block["course"].replace(",", " ")
        lines.append(f'{block["day"]},{format_time(block["start"])},{format_time(block["end"])},{course}')
    return "\n".join(lines) + "\n"


def typical_colour(colours):
    """The middle (median) colour of a list of (red, green, blue) colours."""
    return tuple(sorted(colour[channel] for colour in colours)[len(colours) // 2]
                 for channel in range(3))


def colour_difference(first, second):
    """How far apart two colours are (0 = the same colour)."""
    return max(abs(a - b) for a, b in zip(first, second))


def timetable_from_screenshot(image_source, first_hour=9, day_count=5):
    """Find the busy times in a screenshot of the Woosong timetable app.

    How it works (no text reading is needed):
      1. find the dark bar with the day names,
      2. find the grey hour lines on the left to learn how many pixels = 1 hour,
      3. split the area into day columns and look for coloured class blocks,
      4. turn the top and bottom of every block into a time.
    Course names are not read, so every block is called "Class".
    """
    try:
        from PIL import Image
    except ImportError:
        raise InputError("Reading screenshots needs the Pillow library. Run: pip install pillow")
    try:
        image = Image.open(image_source).convert("RGB")
    except Exception:
        raise InputError("This file is not a picture that can be opened.")

    width, height = image.size
    pixels = image.load()
    not_a_timetable = InputError(
        "This picture does not look like a Woosong timetable screenshot. "
        "Use a full screenshot of the Timetable page in the attendance app.")

    # 1. The header is the tallest band of dark rows in the top half.
    def row_is_dark(y):
        samples = [pixels[x, y] for x in range(0, width, max(1, width // 40))]
        return sum(max(colour) < 125 for colour in samples) >= 0.6 * len(samples)

    best_start, best_end, run_start = None, None, None
    for y in range(height // 2):
        if row_is_dark(y):
            run_start = y if run_start is None else run_start
        elif run_start is not None:
            if best_start is None or y - run_start > best_end - best_start:
                best_start, best_end = run_start, y
            run_start = None
    if best_start is None or best_end - best_start < height * 0.01:
        raise not_a_timetable
    header_bottom = best_end

    # 2. The hour labels sit in a narrow strip on the left. Its right edge is a
    #    thin grey vertical line.
    def is_grey_line(colour):
        return (140 < colour[0] < 232 and abs(colour[0] - colour[1]) < 14
                and abs(colour[1] - colour[2]) < 14)

    sample_rows = range(header_bottom + 5, height, 4)
    gutter, best_score = int(width * 0.053), 0
    for x in range(int(width * 0.02), int(width * 0.15)):
        score = sum(is_grey_line(pixels[x, y]) for y in sample_rows)
        if score > best_score:
            gutter, best_score = x, score
    if best_score < 0.5 * len(sample_rows):
        gutter = int(width * 0.053)

    # 3. Hour lines: rows where the whole strip is grey (label text is not).
    strip_xs = list(range(3, max(gutter - 3, 4), max(1, gutter // 10)))
    hour_lines, previous = [], None
    for y in range(header_bottom + 3, height):
        if all(140 < pixels[x, y][0] < 228 for x in strip_xs):
            if previous is not None and y - previous <= 2:
                hour_lines[-1] = y           # same line, keep its last row
            else:
                hour_lines.append(y)
            previous = y
    gaps = sorted(b - a for a, b in zip(hour_lines, hour_lines[1:]))
    if len(hour_lines) < 4:
        raise not_a_timetable
    pixels_per_hour = gaps[len(gaps) // 2]
    if pixels_per_hour < 10 or any(abs(gap - pixels_per_hour) > 0.15 * pixels_per_hour for gap in gaps):
        raise not_a_timetable

    def y_to_minutes(y):
        exact = first_hour * 60 + (y - hour_lines[0]) / pixels_per_hour * 60
        return int(round(exact / 5) * 5)      # round to the nearest 5 minutes

    # 4. Look for coloured blocks in every day column.
    column_width = (width - gutter) / day_count
    blocks = []
    for day_index in range(day_count):
        left = gutter + day_index * column_width
        xs = [int(left + column_width * (0.08 + 0.84 * step / 19)) for step in range(20)]
        row_colours = {}                      # y -> background colour of that row
        for y in range(header_bottom, height):
            row = [pixels[x, y] for x in xs]
            coloured = [c for c in row if min(c) < 232]
            if len(coloured) >= 0.55 * len(row):
                # Text is darker than the block, so look only at the lightest pixels.
                lightest = sorted(coloured, key=sum)[-max(3, len(coloured) // 3):]
                row_colours[y] = typical_colour(lightest)

        # Rows that follow each other form a run. One run can hold two classes
        # of different colours, so each run is cut where the colour changes.
        runs = []
        for y in sorted(row_colours):
            if runs and y - runs[-1][-1] <= 3:
                runs[-1].append(y)
            else:
                runs.append([y])
        window = max(4, int(pixels_per_hour / 8))
        found = []
        for run in runs:
            pieces = []
            start = 0
            position = window
            while position <= len(run) - window:
                reference = typical_colour([row_colours[y] for y in run[start + 2:start + 2 + window]])
                ahead = typical_colour([row_colours[y] for y in run[position:position + window]])
                if colour_difference(reference, ahead) > 38:
                    # The change is somewhere inside the window: step forward
                    # to the first row that looks like the new colour.
                    cut = position
                    while cut < len(run) - 1 and (colour_difference(row_colours[run[cut]], reference)
                                                  <= colour_difference(row_colours[run[cut]], ahead)):
                        cut += 1
                    pieces.append(run[start:cut])
                    start, position = cut, cut + window
                else:
                    position += 1
            pieces.append(run[start:])
            # Text can fool the step above. Glue pieces back together when
            # their overall colour is really the same.
            for piece in pieces:
                colour = typical_colour([row_colours[y] for y in piece])
                if found and found[-1][1] + 4 >= piece[0] and colour_difference(found[-1][2], colour) <= 30:
                    found[-1] = (found[-1][0], piece[-1], found[-1][2])
                else:
                    found.append((piece[0], piece[-1], colour))

        for first_row, last_row, _ in found:
            if last_row - first_row < pixels_per_hour * 0.2:
                continue                      # too small to be a class
            start, end = y_to_minutes(first_row), y_to_minutes(last_row + 1)
            if end > start:
                blocks.append({"day": DAYS[day_index], "start": start, "end": end, "course": "Class"})
    return blocks


def member_name_from_file(file_name):
    """ "mina_screenshot.png" -> "Mina" (the part before the first _ or dot)."""
    base = os.path.splitext(os.path.basename(file_name))[0]
    return base.split("_")[0].strip().capitalize() or "Member"


def load_timetable(source, file_name):
    """Pick the right loader from the file name (.csv or a picture)."""
    lower_name = file_name.lower()
    if lower_name.endswith(".csv") or lower_name.endswith(".txt"):
        return load_timetable_csv(source)
    if lower_name.endswith((".png", ".jpg", ".jpeg")):
        return timetable_from_screenshot(source)
    raise InputError(f"{file_name}: use a .csv timetable file or a .png/.jpg screenshot.")


# ----------------------------------------------------------------------------
# PART 4 - MEETING FINDER
# ----------------------------------------------------------------------------

def find_meeting_slots(timetables, earliest="09:00", latest="18:00",
                       min_minutes=60, days=("Mon", "Tue", "Wed", "Thu", "Fri")):
    """Find the times when the group can meet.

    timetables : {"Aziz": [blocks], "Mina": [blocks], ...}
    Returns two lists of slots, both sorted with the best slot first:
        everyone   - times when nobody has class
        almost     - times when exactly one person has class (plan B)
    A slot looks like {"day", "start", "end", "minutes", "busy": [names]}.
    """
    if len(timetables) < 2:
        raise InputError("Add at least two timetables to find a meeting time.")
    window_start, window_end = parse_time(earliest), parse_time(latest)
    if window_end <= window_start:
        raise InputError("The latest time must be after the earliest time.")
    if min_minutes <= 0:
        raise InputError("The meeting length must be more than 0 minutes.")

    everyone, almost = [], []
    for day in days:
        # Every start or end of a class is a moment where "who is busy" can change.
        cut_points = {window_start, window_end}
        for blocks in timetables.values():
            for block in blocks:
                if block["day"] == day:
                    cut_points.add(min(max(block["start"], window_start), window_end))
                    cut_points.add(min(max(block["end"], window_start), window_end))
        cut_points = sorted(cut_points)

        # Between two cut points the same people are busy the whole time.
        pieces = []
        for piece_start, piece_end in zip(cut_points, cut_points[1:]):
            busy = sorted(name for name, blocks in timetables.items()
                          if any(b["day"] == day and b["start"] < piece_end and b["end"] > piece_start
                                 for b in blocks))
            if pieces and pieces[-1]["busy"] == busy:
                pieces[-1]["end"] = piece_end          # same people -> grow the piece
            else:
                pieces.append({"day": day, "start": piece_start, "end": piece_end, "busy": busy})

        for piece in pieces:
            piece["minutes"] = piece["end"] - piece["start"]
            if piece["minutes"] < min_minutes:
                continue
            if not piece["busy"]:
                everyone.append(piece)
            elif len(piece["busy"]) == 1:
                almost.append(piece)

    def best_first(slot):
        return (-slot["minutes"], DAYS.index(slot["day"]), slot["start"])

    return sorted(everyone, key=best_first), sorted(almost, key=best_first)


def group_message(slots, how_many=3):
    """Write a short message that can be pasted into the group chat."""
    if not slots:
        return "No time works for everyone this week. Can someone move a class or meet online?"
    lines = ["We are all free at these times:"]
    for slot in slots[:how_many]:
        lines.append(f'- {slot["day"]} {format_time(slot["start"])}-{format_time(slot["end"])} '
                     f'({format_duration(slot["minutes"])})')
    lines.append("Which one works best?")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# PART 5 - DEADLINES (from the Smart LMS calendar export, an .ics file)
# ----------------------------------------------------------------------------

def parse_calendar_time(value, parameters):
    """Turn a calendar time such as 20261118T150000Z into Korean time."""
    value = value.strip()
    try:
        if "VALUE=DATE" in parameters and "T" not in value:
            return datetime.strptime(value, "%Y%m%d")
        if value.endswith("Z"):                # Z means world time (UTC)
            moment = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            return moment.astimezone(KOREA_TIME).replace(tzinfo=None)
        return datetime.strptime(value, "%Y%m%dT%H%M%S")
    except ValueError:
        return None


def clean_deadline_title(title):
    """ "Essay is due" -> "Essay" (Smart LMS adds these endings to every deadline)."""
    for ending in (" is due", " closes", " 마감"):
        if title.endswith(ending):
            title = title[: -len(ending)]
    return title


def load_deadlines(source):
    """Read the calendar file exported from Smart LMS.

    Returns a list of {"title", "course", "due"} sorted by due date.
    """
    text = read_text_file(source)
    if "BEGIN:VCALENDAR" not in text:
        raise InputError("This is not a calendar file. In Smart LMS open Calendar, "
                         "choose Export calendar and upload the .ics file you get.")
    # Long lines are folded in .ics files: a line starting with a space
    # continues the line before it.
    lines = []
    for raw_line in text.replace("\r\n", "\n").split("\n"):
        if raw_line[:1] in (" ", "\t") and lines:
            lines[-1] += raw_line[1:]
        else:
            lines.append(raw_line)

    deadlines, event = [], None
    for line in lines:
        if line == "BEGIN:VEVENT":
            event = {}
        elif line == "END:VEVENT" and event is not None:
            if event.get("due") and event.get("title"):
                deadlines.append({"title": event["title"], "course": event.get("course", "General"),
                                  "due": event["due"]})
            event = None
        elif event is not None and ":" in line:
            name_part, value = line.split(":", 1)
            name, _, parameters = name_part.partition(";")
            value = value.replace("\\n", " ").replace("\\,", ",").replace("\\;", ";").strip()
            if name == "SUMMARY":
                event["title"] = clean_deadline_title(value)
            elif name == "CATEGORIES":
                event["course"] = value
            elif name == "DTSTART":
                event["due"] = parse_calendar_time(value, parameters)
    return sorted(deadlines, key=lambda item: item["due"])


def free_hours_before(due, timetable, now, earliest="09:00", latest="21:00"):
    """Count the free daytime hours between now and a deadline.

    Free means: between earliest and latest, and not in class.
    """
    window_start, window_end = parse_time(earliest), parse_time(latest)
    total_minutes = 0
    day = now.date()
    while day <= due.date():
        start, end = window_start, window_end
        if day == now.date():
            start = max(start, now.hour * 60 + now.minute)
        if day == due.date():
            end = min(end, due.hour * 60 + due.minute)
        if end > start:
            free = end - start
            for block in timetable:
                if block["day"] == DAYS[day.weekday()]:
                    overlap = min(end, block["end"]) - max(start, block["start"])
                    free -= max(0, overlap)
            total_minutes += max(0, free)
        day += timedelta(days=1)
    return round(total_minutes / 60, 1)


def time_left_text(hours_left):
    """Turn 30.5 hours into "1 day left" and 5 hours into "5 hours left"."""
    if hours_left < 24:
        hours = int(hours_left)
        return f"{hours} hour left" if hours == 1 else f"{hours} hours left"
    days = int(hours_left // 24)
    return f"{days} day left" if days == 1 else f"{days} days left"


def rate_deadlines(deadlines, now, timetable=None):
    """Add "days_left", "level" and (with a timetable) "free_hours" to each deadline.

    Levels: OVERDUE, URGENT (48 hours or less), SOON (7 days or less), LATER.
    """
    rated = []
    for item in deadlines:
        hours_left = (item["due"] - now).total_seconds() / 3600
        if hours_left < 0:
            level = "OVERDUE"
        elif hours_left <= 48:
            level = "URGENT"
        elif hours_left <= 24 * 7:
            level = "SOON"
        else:
            level = "LATER"
        entry = dict(item, hours_left=round(hours_left, 1), level=level,
                     days_left=int(hours_left // 24) if hours_left >= 0 else -1)
        # A deadline at 00:00 really means "finish it the evening before".
        entry["midnight"] = item["due"].hour == 0 and item["due"].minute == 0
        if timetable is not None and hours_left >= 0:
            entry["free_hours"] = free_hours_before(item["due"], timetable, now)
        rated.append(entry)
    return rated


# ----------------------------------------------------------------------------
# PART 6 - ATTENDANCE CHECKER
# A course record: {"course", "total", "present", "late", "early", "absent",
#                   "excused", "unchecked"}   (all numbers are class sessions)
# ----------------------------------------------------------------------------

def check_attendance(record):
    """Work out how close one course is to the absence limit.

    Returns the record plus:
        counted_absences - absences + lates turned into absences
        allowed          - most absences possible without failing
        can_still_miss   - sessions you can still miss (negative = already over)
        lates_to_next    - lates left before the next one costs an absence
        status           - NO DATA, SAFE, WARNING, DANGER or FAILED
    """
    total = record["total"]
    late_like = record["late"] + (record["early"] if EARLY_LEAVE_COUNTS_AS_LATE else 0)
    counted = record["absent"] + late_like // LATES_PER_ABSENCE
    allowed = int(total * ABSENCE_LIMIT_FRACTION + 1e-9)   # "more than 1/3" fails
    can_still_miss = allowed - counted

    if total <= 0:
        status = "NO DATA"
    elif counted > allowed:
        status = "FAILED"
    elif can_still_miss == 0 or counted >= 0.75 * allowed:
        status = "DANGER"
    elif counted >= 0.5 * allowed:
        status = "WARNING"
    else:
        status = "SAFE"

    return dict(record, counted_absences=counted, allowed=allowed,
                can_still_miss=can_still_miss,
                lates_to_next=LATES_PER_ABSENCE - late_like % LATES_PER_ABSENCE,
                status=status)


def load_attendance_csv(source):
    """Read an attendance file: course,total,present,late,early,absent,excused,unchecked."""
    text = read_text_file(source)
    reader = csv.DictReader(io.StringIO(text))
    columns = [name.strip().lower() for name in (reader.fieldnames or [])]
    needed = ["course", "total", "present", "late", "early", "absent", "excused", "unchecked"]
    missing = [name for name in needed if name not in columns]
    if missing:
        raise InputError("The attendance file is missing the columns: " + ", ".join(missing) + ".")
    records, problems = [], []
    for line_number, row in enumerate(reader, start=2):
        row = {(key or "").strip().lower(): (value or "").strip() for key, value in row.items()}
        if not any(row.values()):
            continue
        try:
            record = {"course": row["course"] or "Course"}
            for name in needed[1:]:
                if not row[name].isdigit():
                    raise InputError(f'"{row[name]}" in column {name} is not a whole number.')
                record[name] = int(row[name])
            parts = sum(record[name] for name in needed[2:])
            if parts != record["total"]:
                raise InputError(f'the numbers add up to {parts}, but total says {record["total"]}.')
            records.append(record)
        except InputError as problem:
            problems.append(f"line {line_number}: {problem}")
    if problems:
        raise InputError("The attendance file has mistakes:\n  " + "\n  ".join(problems))
    return records


# ----------------------------------------------------------------------------
# PART 7 - TALKING TO THE WOOSONG ATTENDANCE SITE
# The password is used once for the login request and is never saved.
# ----------------------------------------------------------------------------

def read_login_reply(reply):
    """Check the site's answer to a login and return the student's details."""
    result = (reply.get("xidedu") or {}).get("xmsg")
    if result == "NoUser":
        raise LoginError("This student ID is not registered on the attendance site.")
    if result == "NoIdPass":
        raise LoginError("The ID or password is wrong. Please try again.")
    if result != "Ok":
        raise LoginError("The attendance site did not accept the login.")
    user = reply.get("xuser") or {}
    courses = {}
    for entry in reply.get("rollbook") or []:
        key = f'{entry.get("sugang_name")} ({entry.get("sugang_class")})'
        courses.setdefault(key, entry.get("sugang_code"))     # first code of each course
    if not courses:
        raise LoginError("The login worked, but no courses were found for this semester.")
    return {"student_id": user.get("USER_ID", ""), "name": user.get("USER_NM", ""),
            "course_codes": courses}


def read_course_reply(reply):
    """Turn the site's answer for one course into timetable blocks and counts."""
    slots = reply.get("rollbook") or []
    if not slots:
        raise InputError("The attendance site sent no data for this course.")
    course = slots[0].get("sugang_name", "Course")

    blocks = []
    counts = {"present": 0, "late": 0, "early": 0, "absent": 0, "excused": 0, "unchecked": 0}
    for slot in slots:
        start, end = parse_time(slot["sugang_starttime"]), parse_time(slot["sugang_endtime"])
        day_number = str(slot.get("sugang_week", ""))
        day_names = DAYS[:5] if day_number == "0" else [parse_day(day_number)]   # 0 = Mon to Fri
        for day in day_names:
            blocks.append({"day": day, "start": start, "end": end, "course": course})
        for week in slot.get("sugangWeekInfoForJspList") or []:
            logs = week.get("sugangAttendLogList") or [{}]
            code = str(logs[0].get("sugang_attend_kind", "NONE"))
            if code in SITE_PRESENT_CODES:
                counts["present"] += 1
            elif code in SITE_LATE_CODES:
                counts["late"] += 1
            elif code in SITE_EARLY_CODES:
                counts["early"] += 1
            elif code in SITE_EXCUSED_CODES:
                counts["excused"] += 1
            elif code in SITE_ABSENT_CODES:
                counts["absent"] += 1
            else:
                counts["unchecked"] += 1

    # The site also sends its own totals. When they are there we trust them,
    # because they are the numbers the student sees on the site.
    site_totals = ((reply.get("rollbookuser") or [{}])[0] or {}).get("attendCountResultList") or []
    if site_totals:
        total = sum(counts.values())
        counts["late"] = sum(item.get("late_count", 0) for item in site_totals)
        counts["early"] = sum(item.get("early_count", 0) for item in site_totals)
        counts["absent"] = sum(item.get("absent_count", 0) for item in site_totals)
        counts["unchecked"] = sum(item.get("none_count", 0) for item in site_totals)
        counts["present"] = max(0, total - counts["late"] - counts["early"] - counts["absent"]
                                - counts["unchecked"] - counts["excused"])

    record = dict(counts, course=course, total=sum(counts.values()))
    return merge_blocks(blocks), record


def fetch_from_site(student_id, password):
    """Log in to the attendance site and collect timetable and attendance.

    Returns {"name", "timetable": [blocks], "attendance": [records]}.
    """
    try:
        import requests
    except ImportError:
        raise InputError("Logging in needs the requests library. Run: pip install requests")
    if not student_id.strip() or not password:
        raise LoginError("Type both your student ID and your password.")

    session = requests.Session()           # keeps the login cookie for the next requests

    def ask(page, question):
        try:
            answer = session.post(f"{ATTENDANCE_SITE}/attend/{page}",
                                  data={"ikey": json.dumps(question, separators=(",", ":"))},
                                  headers={"Referer": f"{ATTENDANCE_SITE}/wsu/student/index.html",
                                           "X-Requested-With": "XMLHttpRequest"},
                                  timeout=20)
            answer.raise_for_status()
            return answer.json()
        except (requests.RequestException, ValueError):
            raise InputError("The attendance site could not be reached. Check your internet "
                             "connection and try again, or use a screenshot instead.")

    login = read_login_reply(ask("iwin_sin", {"duser_id": student_id.strip(), "duser_pw": password}))
    timetable, attendance = [], []
    for course_code in login["course_codes"].values():
        reply = ask("iwin_st_chulseokbu", {"dclass": course_code, "duser_id": login["student_id"]})
        blocks, record = read_course_reply(reply)
        timetable.extend(blocks)
        attendance.append(record)
    return {"name": login["name"], "timetable": merge_blocks(timetable), "attendance": attendance}


# ----------------------------------------------------------------------------
# PART 7B - TALKING TO SMART LMS (deadlines)
# Smart LMS is a Moodle site. We log in on its normal login page with the
# same ID and password, then ask for the upcoming activities, the same list
# the "Timeline" block on the Smart LMS dashboard shows.
# The password is used once for the login request and is never saved.
# ----------------------------------------------------------------------------

def read_lms_login_token(page_html):
    """Find the hidden logintoken that the Smart LMS login form needs."""
    match = re.search(r'name="logintoken" value="([^"]*)"', page_html)
    if not match:
        raise InputError("The Smart LMS login page could not be read right now. "
                         "Upload the calendar file instead.")
    return match.group(1)


def read_lms_sesskey(page_html):
    """After a good login every Smart LMS page has a logout link with the session key."""
    match = re.search(r"logout\.php\?sesskey=([A-Za-z0-9]+)", page_html)
    if not match:
        raise LoginError("Smart LMS did not accept this ID and password. If your Smart LMS "
                         "password is different, upload the calendar file instead.")
    return match.group(1)


def read_lms_events_reply(reply):
    """Turn Smart LMS's list of upcoming activities into deadlines.

    Returns a list of {"title", "course", "due"} sorted by due date, the same
    shape as load_deadlines().
    """
    answer = reply[0] if isinstance(reply, list) and reply else {}
    if answer.get("error") or "data" not in answer:
        raise InputError("Smart LMS did not send the deadlines. Upload the calendar file instead.")
    deadlines = []
    for event in (answer["data"] or {}).get("events") or []:
        moment = event.get("timesort") or event.get("timestart")
        if not moment or not event.get("name"):
            continue                       # not a deadline we can place in time
        due = datetime.fromtimestamp(int(moment), KOREA_TIME).replace(tzinfo=None)
        course = (event.get("course") or {}).get("fullname") or "General"
        deadlines.append({"title": clean_deadline_title(html.unescape(event["name"])),
                          "course": html.unescape(course), "due": due})
    return sorted(deadlines, key=lambda item: item["due"])


def fetch_deadlines_from_lms(student_id, password):
    """Log in to Smart LMS and collect the deadlines of the coming weeks."""
    try:
        import requests
    except ImportError:
        raise InputError("Logging in needs the requests library. Run: pip install requests")
    if not student_id.strip() or not password:
        raise LoginError("Type both your student ID and your password.")

    session = requests.Session()           # keeps the login cookie for the next requests
    try:
        page = session.get(f"{SMART_LMS_SITE}/login/index.php", timeout=20)
        token = read_lms_login_token(page.text)
        page = session.post(f"{SMART_LMS_SITE}/login/index.php", timeout=20,
                            data={"anchor": "", "logintoken": token,
                                  "username": student_id.strip(), "password": password})
        sesskey = read_lms_sesskey(page.text)

        now = datetime.now(KOREA_TIME)
        method = "core_calendar_get_action_events_by_timesort"
        question = [{"index": 0, "methodname": method, "args": {
            "timesortfrom": int((now - timedelta(days=DEADLINE_DAYS_BACK)).timestamp()),
            "timesortto": int((now + timedelta(days=DEADLINE_DAYS_AHEAD)).timestamp()),
            "limitnum": SMART_LMS_MAX_EVENTS}}]
        answer = session.post(f"{SMART_LMS_SITE}/lib/ajax/service.php", timeout=20,
                              params={"sesskey": sesskey, "info": method}, json=question)
        answer.raise_for_status()
        return read_lms_events_reply(answer.json())
    except InputError:
        raise                              # already a message for the student
    except (requests.RequestException, ValueError):
        raise InputError("Smart LMS could not be reached. Check your internet connection, "
                         "or upload the calendar file instead.")


# ----------------------------------------------------------------------------
# PART 8 - TEXT REPORTS (used by the test cases and the start menu)
# ----------------------------------------------------------------------------

def report_timetable(name, blocks):
    lines = [f"Timetable of {name}: {len(blocks)} class blocks"]
    for block in blocks:
        lines.append(f'  {block["day"]} {format_time(block["start"])}-{format_time(block["end"])}  {block["course"]}')
    return "\n".join(lines)


def report_meeting(everyone, almost, how_many=5):
    lines = ["MEETING FINDER"]
    if everyone:
        lines.append(f"  {len(everyone)} time slots work for everyone. Best first:")
        for slot in everyone[:how_many]:
            lines.append(f'    {slot["day"]} {format_time(slot["start"])}-{format_time(slot["end"])}'
                         f'  ({format_duration(slot["minutes"])})')
    else:
        lines.append("  No time slot works for everyone.")
        if almost:
            lines.append("  Plan B - only one person is busy:")
            for slot in almost[:how_many]:
                lines.append(f'    {slot["day"]} {format_time(slot["start"])}-{format_time(slot["end"])}'
                             f'  ({format_duration(slot["minutes"])}, busy: {slot["busy"][0]})')
        else:
            lines.append("  Try a shorter meeting or a longer day.")
    return "\n".join(lines)


def report_deadlines(rated):
    lines = ["DEADLINES"]
    if not rated:
        lines.append("  No deadlines found in the calendar.")
    for item in rated:
        when = item["due"].strftime("%a %d %b %H:%M")
        left = "overdue" if item["level"] == "OVERDUE" else time_left_text(item["hours_left"])
        extra = f', {item["free_hours"]} free hours before' if "free_hours" in item else ""
        lines.append(f'  [{item["level"]:<7}] {when}  {item["course"]}: {item["title"]}  ({left}{extra})')
    return "\n".join(lines)


def report_attendance(records):
    lines = ["ATTENDANCE"]
    for record in records:
        result = check_attendance(record)
        if result["status"] == "NO DATA":
            detail = "no class sessions recorded"
        elif result["status"] == "FAILED":
            detail = (f'{result["counted_absences"]} absences counted, limit is {result["allowed"]} '
                      f'- over the limit by {-result["can_still_miss"]}')
        else:
            detail = (f'{result["counted_absences"]} of {result["allowed"]} allowed absences used, '
                      f'can still miss {result["can_still_miss"]}')
        lines.append(f'  [{result["status"]:<7}] {result["course"]}: {detail}')
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# PART 9 - TEST RUNNER AND START MENU
# ----------------------------------------------------------------------------

def run_case(folder):
    """Run one test case folder and return everything it prints as text.

    Each folder has a case.json that lists the input files to use.
    Mistakes in the input must become friendly messages, never a crash.
    """
    with open(os.path.join(folder, "case.json"), encoding="utf-8") as handle:
        case = json.load(handle)
    now = datetime.strptime(case.get("today", "2026-11-16 09:00"), "%Y-%m-%d %H:%M")
    output = [f'CASE: {case["description"]}', ""]

    def attempt(label, action):
        """Run one step; turn input mistakes into a readable line."""
        try:
            return action()
        except InputError as problem:
            output.append(f"{label}: ERROR - {problem}")
            return None

    timetables = {}
    for file_name in case.get("timetables", []):
        name = member_name_from_file(file_name)
        blocks = attempt(file_name, lambda: load_timetable(os.path.join(folder, file_name), file_name))
        if blocks is not None:
            timetables[name] = blocks
            output.append(report_timetable(name, blocks))
    if case.get("timetables"):
        output.append("")
        slots = attempt("Meeting finder", lambda: find_meeting_slots(
            timetables, case.get("earliest", "09:00"), case.get("latest", "18:00"),
            case.get("min_minutes", 60)))
        if slots:
            output.extend([report_meeting(*slots), "", "Message for the group chat:",
                           group_message(slots[0]), ""])

    for file_name in case.get("calendars", []):
        deadlines = attempt(file_name, lambda: load_deadlines(os.path.join(folder, file_name)))
        if deadlines is not None:
            mine = timetables.get(case.get("my_name", ""))
            output.extend([report_deadlines(rate_deadlines(deadlines, now, mine)), ""])

    for file_name in case.get("attendance_files", []):
        records = attempt(file_name, lambda: load_attendance_csv(os.path.join(folder, file_name)))
        if records is not None:
            output.extend([report_attendance(records), ""])

    for file_name in case.get("site_course_replies", []):
        def read_reply():
            with open(os.path.join(folder, file_name), encoding="utf-8") as handle:
                return read_course_reply(json.load(handle))
        result = attempt(file_name, read_reply)
        if result is not None:
            blocks, record = result
            output.extend([f"{file_name}:", report_timetable(record["course"], blocks),
                           report_attendance([record]), ""])

    for file_name in case.get("login_replies", []):
        def read_login():
            with open(os.path.join(folder, file_name), encoding="utf-8") as handle:
                return read_login_reply(json.load(handle))
        login = attempt(file_name, read_login)
        if login is not None:
            output.append(f'{file_name}: login accepted for {login["name"]}, '
                          f'{len(login["course_codes"])} courses found')

    for file_name in case.get("lms_pages", []):
        def read_page():
            return read_lms_sesskey(read_text_file(os.path.join(folder, file_name)))
        if attempt(file_name, read_page) is not None:
            output.append(f"{file_name}: logged in to Smart LMS")

    for file_name in case.get("lms_event_replies", []):
        def read_events():
            with open(os.path.join(folder, file_name), encoding="utf-8") as handle:
                return read_lms_events_reply(json.load(handle))
        deadlines = attempt(file_name, read_events)
        if deadlines is not None:
            output.extend([f"{file_name}:", report_deadlines(rate_deadlines(deadlines, now)), ""])

    return "\n".join(output).rstrip() + "\n"


def run_all_tests(test_folder):
    """Run every case and compare the result with expected_output.txt."""
    passed = failed = 0
    for case_name in sorted(os.listdir(test_folder)):
        folder = os.path.join(test_folder, case_name)
        if not os.path.isfile(os.path.join(folder, "case.json")):
            continue
        actual = run_case(folder)
        with open(os.path.join(folder, "actual_output.txt"), "w", encoding="utf-8") as handle:
            handle.write(actual)
        expected_path = os.path.join(folder, "expected_output.txt")
        expected = read_text_file(expected_path) if os.path.exists(expected_path) else ""
        same = actual.split() == expected.split()      # ignore spacing differences
        passed, failed = passed + same, failed + (not same)
        print(f'{"PASS" if same else "FAIL"}  {case_name}')
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if "--test" in sys.argv:
        sys.exit(0 if run_all_tests(os.path.join(here, "test_cases")) else 1)

    print("STUDY WEEK ASSISTANT")
    print("  1  Open the browser app")
    print("  2  Run the test cases")
    print("  3  Show the demo week here in the terminal")
    choice = input("Choose 1, 2 or 3: ").strip()
    if choice == "1":
        import subprocess
        try:
            import streamlit  # noqa: F401  (only checking that it is installed)
        except ImportError:
            print("The browser app needs Streamlit. Run:  pip install streamlit")
            return
        # cwd=here so Streamlit finds the colour theme in .streamlit/config.toml
        subprocess.run([sys.executable, "-m", "streamlit", "run", os.path.join(here, "app_browser.py")],
                       cwd=here)
    elif choice == "2":
        run_all_tests(os.path.join(here, "test_cases"))
    elif choice == "3":
        print()
        print(run_case(os.path.join(here, "test_cases", "case1_normal_week")))
    else:
        print("Please start again and type 1, 2 or 3.")


if __name__ == "__main__":
    main()
