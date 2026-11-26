"""i-ONE PASS sign-in against a faked university site: python test_passkey.py"""
import json
import os

import requests

import project_code as core

HERE = os.path.dirname(os.path.abspath(__file__))
SMART, SSO = core.SMART_SITE, core.SSO_SITE
CALENDAR = open(os.path.join(HERE, "test_cases", "case1_normal_week", "smart_lms_calendar.ics"), "rb").read()
HAND_OVER = ('<form id="idpLoginFrm" method="post" action="https://sso.wsu.ac.kr/svc/tk/Auth.eps">'
             '<input type="hidden" name="id" value="lms" /><input type="hidden" name="RelayState" value="r" /></form>')
SSO_PAGE = ('<form name="loginFrm" id="loginFrm" action="&#x2f;Login.eps" method="POST">'
            '<input type="hidden" name="l_token" value="L1"><input type="hidden" name="c_token" value="C1">'
            '<input type="hidden" name="user_timezone_offset"><input type="hidden" name="ssoOption" value="01">'
            '</form><form id="smartFrm"><input type="text" name="suser_id"></form>')
EXPORT_PAGE = ('<form action="https://smart.wsu.ac.kr/calendar/export.php" method="post">'
               '<input name="sesskey" type="hidden" value="S1" />'
               '<input name="_qf__core_calendar_export_form" type="hidden" value="1" />'
               '<input type="radio" name="events[exportevents]" value="all" /></form>')


class Answer:
    def __init__(self, url, text="", content=None, go_to=None):
        self.url, self.text = url, text
        self.content = content if content is not None else text.encode()
        self.is_redirect, self.headers = go_to is not None, {"Location": go_to}

    def raise_for_status(self):
        pass

    def json(self):
        return json.loads(self.text)


class FakeSite:
    """Answers like the university sites; `pages` maps (method, url) to a list of answers."""
    def __init__(self, pages):
        self.pages, self.sent, self.headers = pages, [], {}

    def request(self, method, url, **options):
        self.sent.append((method, url, options.get("data")))
        answers = self.pages[(method, url)]
        return answers.pop(0) if len(answers) > 1 else answers[0]


def site(push='{"returnCode":"0000","tId":"T1"}', checks=('{"returnCode":"0000"}',), export=EXPORT_PAGE):
    return FakeSite({
        ("GET", f"{SMART}/exsignon/sso/sso_index.php"): [Answer(f"{SMART}/exsignon/sso/sso_idp_login.php", HAND_OVER)],
        ("POST", f"{SSO}/svc/tk/Auth.eps"): [Answer(f"{SSO}/svc/tk/Auth.eps", SSO_PAGE)],
        ("POST", f"{SSO}/wsu/IOnePassPush.eps"): [Answer("", push)],
        ("POST", f"{SSO}/wsu/IOnePassChkAuth.eps"): [Answer("", c) for c in checks],
        ("POST", f"{SSO}/Login.eps"): [Answer(f"{SMART}/", "<html>My courses</html>")],
        ("GET", f"{SMART}/calendar/export.php"): [Answer(f"{SMART}/calendar/export.php", export)],
        ("POST", f"{SMART}/calendar/export.php"): [Answer(f"{SMART}/calendar/export.php", content=CALENDAR)],
    })


def use(fake):
    requests.Session = lambda: fake      # the code builds its own Session; hand it the fake one
    return fake


def fails(action, message_part, error=core.InputError):
    try:
        action()
    except error as problem:
        assert message_part in str(problem), problem
        return
    raise AssertionError(f"expected an error with {message_part!r}")


# Happy path: phone not approved on the first OK, approved on the second
fake = use(site(checks=('{"returnCode":"1012","resultMsg":"Not approved yet"}', '{"returnCode":"0000"}')))
started = core.passkey_start(" 20260001 ")
assert ("POST", f"{SSO}/wsu/IOnePassPush.eps", {"user_id": "20260001"}) in fake.sent
fails(lambda: core.passkey_finish(started), "Not approved yet", core.PasskeyWaiting)
deadlines = core.passkey_finish(started)
assert deadlines == core.load_deadlines(CALENDAR) and deadlines, deadlines
login = next(data for method, url, data in fake.sent if url == f"{SSO}/Login.eps")
assert login["l_token"] == "L1" and login["c_token"] == "C1" and login["ssoOption"] == "01", login
export = fake.sent[-1][2]
assert export["sesskey"] == "S1" and export["export"] == "Export", export
assert fake.headers["User-Agent"] == core.BROWSER_AGENT

# Problems become messages, never crashes
fails(lambda: core.passkey_start("2026 0001"), "student ID")
use(site(push='{"returnCode":"2001","resultMsg":"i-ONE PASS is not registered"}'))
fails(lambda: core.passkey_start("20260001"), "not registered")
use(site(push="<html>error page</html>"))
fails(lambda: core.passkey_start("20260001"), "sign-in page has changed")
use(site(checks=('{"returnCode":"9999","resultMsg":"Request expired"}',)))
fails(lambda: core.passkey_finish(core.passkey_start("20260001")), "Request expired")
use(site(export="<html>Please log in</html>"))
fails(lambda: core.passkey_finish(core.passkey_start("20260001")), "did not finish")
fails(lambda: core._sign_in_request(fake, "GET", "https://evil.example/x"), "sign-in page has changed")

# Redirects are followed only inside the two university sites
hop = FakeSite({("GET", f"{SSO}/a"): [Answer(f"{SSO}/a", go_to="/b")],
                ("GET", f"{SSO}/b"): [Answer(f"{SSO}/b", "arrived")],
                ("GET", f"{SSO}/out"): [Answer(f"{SSO}/out", go_to="https://evil.example/x")]})
assert core._sign_in_request(hop, "GET", f"{SSO}/a").text == "arrived"
fails(lambda: core._sign_in_request(hop, "GET", f"{SSO}/out"), "sign-in page has changed")
assert ("GET", "https://evil.example/x", None) not in hop.sent

# Smart LMS course codes are dropped from course names; ordinary brackets stay
assert core.short_course("ProgrammingforBusiness (2026-20, 0013837_001_120_1200500410040)") == "ProgrammingforBusiness"
assert core.short_course("Data Analysis (2)") == "Data Analysis (2)"
assert core.clean_deadline_title("**Final Project ** is due") == "Final Project"
print("PASSKEY OK")
