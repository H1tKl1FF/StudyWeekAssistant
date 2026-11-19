# How to run Study Week Assistant on your own computer

A step-by-step guide for the team. It takes about 10 minutes the first time,
and about 1 minute every time after that.

- [Part 1: Get the project files](#part-1-get-the-project-files)
- [Part 2A: Mac](#part-2a-mac)
- [Part 2B: Windows laptop](#part-2b-windows-laptop)
- [Part 3: Using the app](#part-3-using-the-app)
- [Part 4: Next time (quick start)](#part-4-next-time-quick-start)
- [Problems and fixes](#problems-and-fixes)

---

## Part 1: Get the project files

Choose **A** if a teammate sent you the zip file (most of you), or **B** if you
were invited to the GitHub repository.

### A. You got `StudyWeekAssistant.zip` from a teammate

1. **Save the zip to your computer.**
   - **KakaoTalk / Telegram / other chat app:** click the file, then
     **Save** (or **Save as**). It usually lands in your **Downloads** folder.
   - **Email:** click the attachment's download arrow.
   - Do not open the files inside the zip directly from the chat app. Save the
     zip first.
2. **Unzip it.**
   - **Mac:** open **Finder**, go to **Downloads** and double-click
     `StudyWeekAssistant.zip`. A folder `StudyWeekAssistant` appears next to it.
   - **Windows:** open **Downloads**, right-click `StudyWeekAssistant.zip`,
     choose **Extract All...**, then **Extract**.
     (Do not just double-click into the zip and run things from there.
     Windows only shows a preview, and Python cannot install inside it.)
3. **Move the folder to your Desktop.** Drag the `StudyWeekAssistant` folder
   onto your **Desktop**. The rest of this guide assumes it is there.
4. **Check the folder.** Open it. You should see `app_browser.py`,
   `project_code.py`, `requirements.txt`, `HOW_TO_RUN.md` and a `test_cases`
   folder. If you see only one more folder with the same name inside, open
   that one: that is the project folder.

> Got a newer zip later? Delete the old `StudyWeekAssistant` folder first,
> then unzip the new one. On Mac, you need to repeat Part 2A, Step 3 once.

### B. You were invited on GitHub

1. Accept the invitation email from GitHub.
2. Open <https://github.com/H1tKl1FF/StudyWeekAssistant>.
3. Click the green **Code** button, then **Download ZIP**.
4. Unzip it as in A, step 2. The folder is called `StudyWeekAssistant-main`.
   You can rename it to `StudyWeekAssistant`.
5. Move it to your **Desktop**.

---

## Part 2A: Mac

### Step 1. Install Python (once)

1. Open **Terminal**: press `Cmd + Space`, type `Terminal`, press `Return`.
2. Type this and press `Return`:

   ```bash
   python3 --version
   ```

3. If it shows **Python 3.11** or higher (3.12, 3.13, 3.14 ...), go to Step 2.
4. Otherwise, or if a pop-up asks to install "command line developer tools":
   - Go to <https://www.python.org/downloads/> and click the yellow
     **Download Python** button.
   - Open the downloaded `.pkg` file and click through the installer.
   - Close Terminal completely (`Cmd + Q`), open it again and repeat the
     `python3 --version` check.

### Step 2. Open the project folder in Terminal

1. In Terminal, type `cd` followed by **one space** (do not press `Return` yet).
2. Drag the project folder from Finder into the Terminal window.
   The folder path appears after `cd `.
3. Press `Return`.
4. Check you are in the right place:

   ```bash
   ls
   ```

   You should see `app_browser.py`, `project_code.py` and `requirements.txt`.

### Step 3. Install the libraries (once)

Run these three commands one after another:

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

- The first makes a private Python box (`.venv`) just for this project.
- The second switches it on. Your prompt now starts with `(.venv)`.
- The third downloads Streamlit and the other libraries (1-3 minutes).

### Step 4. Check that everything works (optional, 10 seconds)

```bash
python project_code.py --test
```

The last line should say **6 passed, 0 failed**.

### Step 5. Start the app

```bash
python project_code.py
```

Type `1` and press `Return`. The app opens in your browser at
<http://localhost:8501>. If the browser does not open by itself, copy that
address into Safari or Chrome.

The first time, Streamlit may ask for your email in Terminal.
Just press `Return` to skip it.

---

## Part 2B: Windows laptop

### Step 1. Install Python (once)

1. Go to <https://www.python.org/downloads/> and click the yellow
   **Download Python** button.
2. Open the downloaded file.
3. **Important:** on the first screen, tick
   **"Add python.exe to PATH"** at the bottom. Then click **Install Now**.
4. When it says "Setup was successful", click **Close**.

### Step 2. Open the project folder in a terminal

1. Open the project folder in **File Explorer**.
2. Click the address bar at the top, type `cmd` and press `Enter`.
   A black Command Prompt window opens, already inside the project folder.
3. Check that Python works:

   ```bash
   py --version
   ```

   It should show **Python 3.11** or higher.

### Step 3. Install the libraries (once)

```bash
py -m pip install -r requirements.txt
```

This downloads Streamlit and the other libraries (1-3 minutes).
Yellow "WARNING" lines are normal. Red "ERROR" lines are not (see
[Problems and fixes](#problems-and-fixes)).

### Step 4. Check that everything works (optional, 10 seconds)

```bash
py project_code.py --test
```

The last line should say **6 passed, 0 failed**.

### Step 5. Start the app

```bash
py project_code.py
```

Type `1` and press `Enter`. The app opens in your browser at
<http://localhost:8501>. If it does not open by itself, copy that address into
your browser.

If Windows Firewall asks about Python, click **Allow** (Private networks).

---

## Part 3: Using the app

1. On the **Home** page, click **Try the demo week** to see everything with
   invented students. No password needed.
2. Click **Exit demo** when you are done looking around.
3. To use your own data, go to **My data**:
   - **Option 1:** log in with your own student ID and password. The app reads
     your timetable, attendance and Smart LMS deadlines. The password is only
     used for that one request and is never saved.
   - **Option 2:** upload a timetable screenshot and the Smart LMS calendar
     file (`.ics`) instead.
4. **Group meeting:** on **My data**, click **Save my timetable file** and send
   that file to the group. Upload everyone's files on the **Meet** page.
   Share files, never passwords.
5. **Light or dark mode:** the `⋮` menu at the top right, then **Settings**.

**To stop the app:** go back to the Terminal / Command Prompt window and press
`Ctrl + C`. Closing the browser tab alone does not stop it.

---

## Part 4: Next time (quick start)

**Mac** (open Terminal, then):

```bash
cd ~/Desktop/StudyWeekAssistant
```

```bash
source .venv/bin/activate
```

```bash
python project_code.py
```

**Windows** (open the folder, type `cmd` in the address bar, then):

```bash
py project_code.py
```

Then type `1`. Change the `cd` path if you put the folder somewhere else.

---

## Problems and fixes

| What you see | What to do |
| --- | --- |
| Mac: `command not found: python3` | Install Python from python.org (Part 2A, Step 1), then reopen Terminal. |
| Mac: `externally-managed-environment` | You skipped the `.venv` commands. Run Part 2A, Step 3 in order. |
| Mac: prompt does not start with `(.venv)` | Run `source .venv/bin/activate` again from inside the project folder. |
| Windows: `'py' is not recognized` | Reinstall Python and tick **Add python.exe to PATH**. Then open a new Command Prompt. |
| `No module named streamlit` | The libraries are not installed yet. Run Step 3 again. On Mac, check for `(.venv)` first. |
| `No such file or directory: requirements.txt` | The terminal is in the wrong folder. Repeat Step 2. |
| `Port 8501 is already in use` | The app is already running in another window. Use that one, or close it with `Ctrl + C`. |
| The app looks plain or shows a sidebar | You have an old copy. Ask for the newest zip, delete the old folder and unzip again. |
| Mac: "cannot be opened because it is from an unidentified developer" | Do not double-click the `.py` files. Always start the app from Terminal as in Step 5. |
| Windows: the folder has a zipper icon / "file is read-only" | You are inside the zip, not the unzipped folder. Use **Extract All...** (Part 1, A step 2). |
| "Smart LMS did not accept this ID and password" | Your Smart LMS password may differ. Upload the calendar `.ics` file on **My data** instead. |
| Browser shows "This site can't be reached" | The app is not running. Check the Terminal window for errors and start it again. |

Still stuck? Send a screenshot of the Terminal / Command Prompt window to the
group chat. Never send your password.
