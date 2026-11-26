# Study Week Assistant: team presentation script

Python Programming for Business, Final Group Project (2026 Fall)

The app is finished (version 1.5.0). What is left is the presentation, the slides, a live demo, and a short update to the README. This file splits that work among four people. If your group has three people, Speaker 3 also takes Part 4.

**Total time: about 12 minutes plus questions.** Times are a guide. Practise once with a timer.

---

## Who does what before the presentation

| Person | Presents | Prepares |
|---|---|---|
| Speaker 1 | Part 1: The problem and the idea (2 min) | Slides 1-3, opening and closing |
| Speaker 2 | Part 2: Live demo (4 min) | Installs the app, runs the demo twice before the day, makes backup screenshots |
| Speaker 3 | Part 3: How the code works (3 min) | Slides 6-9, reads Parts 4-6 of `project_code.py` |
| Speaker 4 | Part 4: Testing, safety and limits (2 min), then leads Q&A | Slides 10-12, runs the tests, updates the README (see the end of this file) |

Everyone reads the "Questions we may get" section.

### Before the day (checklist)

- [ ] Speaker 2: install `StudyWeekAssistant-Setup-1.5.0.exe` on the laptop used for the presentation. Open the app once and press **Try the demo week**.
- [ ] Speaker 2: take screenshots of Home, Meet, Deadlines and Attendance (demo week). Put them in the slides as a backup if the live demo fails.
- [ ] Speaker 4: run `python project_code.py --test` and take a screenshot of the result (9 passed, 0 failed).
- [ ] Speaker 4: update the "HOW TO GET YOUR OWN DATA IN" part of README.txt (see the end of this file).
- [ ] Everyone: one full practice run with a timer.
- [ ] Never show a real student ID, password or calendar link on the screen. Use the demo week only.

---

## Part 1: The problem and the idea (Speaker 1, about 2 minutes)

**Slide 1: Title.** "Study Week Assistant", group members' names, course name.

**Slide 2: The problem.**

> "Every week, a Woosong student checks three places by hand: the timetable app, the attendance site, and Smart LMS. And Smart LMS is now two sites: smart and nsmart. In a group project, it is even worse: to find a meeting time, everyone sends screenshots of their timetable to the group chat, and someone compares them by eye."

**Slide 3: Our idea, three questions in one place.**

> "Our tool answers the three questions behind those checks:
> 1. **Meet:** When can my group meet?
> 2. **Deadlines:** What is due next, and how much free time do I really have before it?
> 3. **Attendance:** How many classes can I still miss before I fail a course?
>
> It is written in Python. It runs on your own computer, and it opens in the browser. My teammate will show you how it works."

---

## Part 2: Live demo (Speaker 2, about 4 minutes)

Use the demo week only (invented students, no password). Open the app before the presentation starts.

1. **Home.** Press **Try the demo week**.
   > "This is Home: this week on one screen. Every day shows its deadlines, with how many days are left, and the best group meeting times. Today is marked in yellow. Deadlines outside this week are listed under the week, so nothing is hidden."

2. **Meet** (left sidebar).
   > "Four members uploaded their timetables. One of them only sent a screenshot of the timetable app, and the tool read the class blocks from the picture. Here are the times when everyone is free, longest first. If no time works for everyone, it shows plan B: times when only one person has class. You can change the earliest start, the latest end and the meeting length. And at the bottom is a ready message for the group chat, with a copy button."

3. **Deadlines.**
   > "Every deadline from both Smart LMS sites, in one list, sorted by date. The big number is how many days are left. Red means 48 hours or less. Next to it is how many free hours you have before the deadline, outside your classes. Overdue work is hidden. With this switch you can show it again."

   Turn on **Show overdue entries**, then turn it off.

4. **Attendance.**
   > "For each course: how many classes you can still miss. The rule is from the Woosong academic regulations: more than one third absent means the course is failed. Three lates count as one absence. The colour tells you the status: safe, warning, danger or failed."

5. **My data.**
   > "Real students get their own data here. Option 1 is to log in once with your student ID to get your timetable and attendance. Since December, Smart LMS asks for a passkey, so for deadlines you paste your personal calendar links. No password is needed for those. You can also upload a screenshot or a file."

   Do not type anything into the fields.

6. Optional, 20 seconds: switch the computer to dark mode to show that the app follows it.

**If the demo fails:** go to the backup screenshots and say the same lines.

---

## Part 3: How the code works (Speaker 3, about 3 minutes)

**Slide 6: Two files.**

> "The project has two main files. `project_code.py` does all the calculations: about 1,300 lines in nine parts. `app_browser.py` only draws the screens, with the Streamlit library. That way, the same logic is used by the browser app, the test runner and the terminal menu."

**Slide 7: Meeting finder** (`find_meeting_slots`, Part 4).

> "Every start or end of a class is a moment where 'who is busy' can change. So we cut each day at those moments. Between two cuts, the same people are busy the whole time. If nobody is busy and the piece is long enough, it is a meeting slot. If exactly one person is busy, it is plan B. Then we sort: the longest slot first."

**Slide 8: Deadlines** (Part 5).

> "Smart LMS gives a calendar file in the iCalendar format. We read each event's title, course and due time, in Korean time. Then we rate each deadline: overdue, urgent (48 hours or less), soon (this week) or later. The free-hours number goes day by day from now until the deadline. It counts the hours between 9:00 and 21:00 and subtracts your classes."

**Slide 9: Attendance** (`check_attendance`, Part 6).

> "Counted absences are absences plus lates divided by three. Leaving early counts like a late: that is our own assumption. The limit is one third of all sessions. From half of the limit, the status is WARNING. From three quarters, it is DANGER. Over the limit, it is FAILED. All these rules are settings at the top of the file, Part 1, so they are easy to change."

Optional, if there is time: the screenshot reader (`timetable_from_screenshot`) finds the dark day bar and the hour lines, then looks for coloured blocks in each day column. It does not read text, so course names stay unknown.

---

## Part 4: Testing, safety and limits (Speaker 4, about 2 minutes)

**Slide 10: Tests.**

> "We have nine test cases. Each case has input files and the output we expect. One command runs them all and prints PASS or FAIL. They cover a normal week, a week with no common time, wrong files, login problems, unusual but valid data, both Smart LMS sites, odd inputs, and the new calendar links. All 9 pass."

Show the screenshot of the test result.

**Slide 11: Privacy and safety.**

> "The app runs only on your own computer. The password is used for one login request and is never saved. Calendar links are hidden like passwords. The app only opens https links to the two Smart LMS sites. All the students in our demo and tests are invented."

**Slide 12: Limits and what we learned.**

> "Our limits: if the university changes its websites, the login may stop working. Uploading files still works then. The screenshot reader needs a full, uncropped screenshot. And in December, Smart LMS started asking for a passkey. Our login could not do that, so we added calendar links. That taught us not to depend on one way of getting data."

**Closing (Speaker 1, 15 seconds):**

> "Three places, three questions, one tool. Thank you. We are happy to answer your questions."

---

## Questions we may get (everyone reads this)

**Why Streamlit and not a website with a server?**
Streamlit lets us build the screens in Python only, the language of this course. And everything stays on the student's own computer.

**How do you know the attendance rule is right?**
It is from the Woosong academic regulations, article 10: more than one third absent means fail. The "3 lates = 1 absence" rule is how the attendance site counts. "Leaving early = late" is our own assumption, and the README says so.

**What happens if the website changes?**
The login stops working, and the app shows a clear message. Screenshots, timetable files and calendar files still work.

**Is it safe to give the app my password?**
The password is sent only to the university site, over https, for one request. It is never written to a file. For the presentation we use the demo week, so no password is used.

**Why calendar links and not the login for deadlines?**
Since December 2026, Smart LMS needs a passkey (I-ONE PASS), which a program cannot use. Every student has a personal calendar link that works without logging in.

**How did you test the code that talks to the websites?**
We saved real site answers (with invented data) as files. The tests read those files instead of the live site, so no real password is needed.

**How did you share the app?**
There is a Windows installer, and the versions are published as GitHub releases. On a Mac, you run it with Python (HOW_TO_RUN.md).

---

## Small task: update README.txt (Speaker 4)

README.txt still says the login gets deadlines from Smart LMS. Since the passkey change, that is no longer true. In the section "HOW TO GET YOUR OWN DATA IN", replace "Deadlines - choose one: a) ..." with:

```
  Deadlines - choose one:
    a) Paste your Smart LMS calendar links (My data page). They work
       without a password, also with passkey login.
       smart.wsu.ac.kr:  Calendar > Export calendar > All events,
                         Recent and next 60 days > Get calendar URL
       nsmart.wsu.ac.kr: Calendar > Calendar feed (bottom right)
       Each link is personal, like a password: never share it.
    b) Or upload the calendar file (.ics) by hand.
```

Under "KNOWN LIMITS", also change the "Deadlines by login" line to say that the Smart LMS login needs a passkey since December 2026, so calendar links are used.
