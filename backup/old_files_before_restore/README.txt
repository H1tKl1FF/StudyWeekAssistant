STUDY WEEK ASSISTANT
Python Programming for Business - Final Group Project (2026 Fall)
==================================================================

WHAT IT DOES
------------
Every week students check three places by hand: the timetable app, the
attendance site and Smart LMS. This tool answers the three questions behind
that in one place:

  1. MEET        When can my group meet?
  2. DEADLINES   What is due next, and how much free time do I have before it?
  3. ATTENDANCE  How many classes can I still miss before I fail a course?


FILES
-----
  project_code.py    All calculations, the test runner and the start menu
  app_browser.py     The browser app (screens only, uses project_code.py)
  requirements.txt   The libraries to install
  test_cases/        Five test cases with input files and expected output
  README.txt         This file


INSTALL (once)
--------------
  1. Install Python 3.9 or newer from python.org
  2. Open a terminal in this folder and run:

       pip install -r requirements.txt

     (On Mac, use pip3 and python3 if pip and python are not found.)


RUN
---
  python project_code.py

  Then choose:
    1  Open the browser app
    2  Run the test cases
    3  Show the demo week in the terminal (no extra libraries needed)

  The browser app can also be started directly:

    streamlit run app_browser.py

  In the app, press "Try the demo week" to see everything with invented
  students. No password is needed for the demo.


HOW TO GET YOUR OWN DATA IN
---------------------------
  Timetable and attendance - choose one:
    a) Log in (sidebar, "Log in to the attendance site") with your own
       student ID and password. The tool reads your timetable and attendance
       from att.wsu.ac.kr.
    b) Upload a screenshot of the Timetable page of the attendance app.
       The tool finds the coloured class blocks and turns them into busy
       times. Course names are not read, and attendance is not included.
    c) Upload a timetable file (.csv) with these columns:
         day,start,end,course
         Mon,10:00,12:00,Marketing Principles

  Deadlines:
    1. Open smart.wsu.ac.kr and go to Calendar.
    2. Click "Export calendar", choose "All events" and
       "Recent and next 60 days", then click "Export".
    3. Upload the downloaded .ics file in the sidebar.

  Group meeting:
    Every member sends a screenshot or presses "Save my timetable file" and
    sends that file. Upload the files in the Meet tab. The file name becomes
    the member's name (mina.png -> Mina). Share files, never passwords.


RULES THE TOOL USES
-------------------
  - A course is failed when absences are MORE than 1/3 of all class sessions
    (Woosong academic regulations, article 10).
  - 3 lates count as 1 absence (this is how the attendance site counts).
  - Leaving early is counted like a late. This is our assumption.
  - Excused absences do not count.
  - Warning levels: WARNING from half of the allowed absences, DANGER from
    three quarters or when no absence is left, FAILED when over the limit.
  All of these are settings at the top of project_code.py (Part 1).


TEST CASES
----------
  Run them all:   python project_code.py --test

  Each folder in test_cases/ contains the input files, case.json (which files
  to use) and expected_output.txt. The test runner writes actual_output.txt
  next to it and prints PASS or FAIL.

  case1_normal_week        Normal: four members (one by screenshot), a real
                           calendar export layout, attendance from a file and
                           from a saved site answer
  case2_no_common_time     Edge: no slot works for everyone, the tool offers
                           plan B (only one person busy)
  case3_wrong_files        Errors: wrong times, missing columns, empty file,
                           a photo that is not a timetable, wrong file type,
                           a file that is not a calendar, wrong numbers
  case4_login_problems     Errors: wrong password, unknown ID, site error,
                           no courses (saved site answers, no real password)
  case5_unusual_but_valid  Edge: member with no classes, classes outside the
                           day, attendance exactly at the limit and one over,
                           lates turning into absences, empty calendar

  All students and courses in the test cases are invented.


PRIVACY AND SAFETY
------------------
  - The app runs on your own computer. Nothing is sent anywhere except the
    login request to the university attendance site (over https).
  - The password is used for that one request and is never written to a file.
  - Each student logs in only to their own account.


KNOWN LIMITS
------------
  - The screenshot reader expects a full, uncropped screenshot of the
    Timetable page (Monday to Friday, starting at 9:00). Times are rounded to
    5 minutes. Heavily compressed pictures can be a few minutes off.
  - Smart LMS uses the university single sign-on, so deadlines come from the
    exported calendar file instead of a login.
  - If the attendance site changes its pages, the login option may stop
    working. The screenshot and file options keep working.
