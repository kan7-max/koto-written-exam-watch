"""Watch Koto written-exam slots and notify via Gmail.

Runs with Python's standard library on GitHub Actions. No personal booking data
is sent to the reservation site. GitHub issue #1-like state is created on first run.
"""

import datetime as dt
import json
import os
import smtplib
import ssl
import sys
import urllib.parse
import urllib.request
from email.message import EmailMessage
from zoneinfo import ZoneInfo


JST = ZoneInfo("Asia/Tokyo")
API = "https://license-test-tokyo-prd-police-pref-api.tokyo-madoguchi-yoyaku.com/calgetres"
ENTRY = "https://license-renew.tokyo-madoguchi-yoyaku.com/police-pref-tokyo/index_000.html"
STATE_TITLE = "江東学科試験ボットの通知状態"
TIME_OF_DAY = os.getenv("TIME_OF_DAY", "all")


def request_json(url, *, method="GET", payload=None, headers=None):
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            **(headers or {}),
        },
    )
    if body is not None:
        request.add_header("Content-Type", "application/json; charset=utf-8")
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read()
    return json.loads(data) if data else {}


def months_between(start, end):
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        yield f"{year:04d}{month:02d}"
        month += 1
        if month == 13:
            year, month = year + 1, 1


def get_open_slots(start, end):
    now = dt.datetime.now(JST)
    slots = {}
    for month in months_between(start, end):
        query = urllib.parse.urlencode(
            {"date": month, "coursecode": "11", "placecode": "250", "user": "pub"}
        )
        result = request_json(f"{API}?{query}")
        if result.get("code") != "A0001":
            raise RuntimeError(f"Calendar returned code {result.get('code')}")
        for row in result.get("body", []):
            day = dt.datetime.strptime(row["date"], "%Y%m%d").date()
            if not start <= day <= end:
                continue
            label = row.get("displaytime", "")
            is_afternoon = "午後" in label
            if TIME_OF_DAY == "morning" and is_afternoon:
                continue
            if TIME_OF_DAY == "afternoon" and not is_afternoon:
                continue
            if int(row["capacity"]) <= int(row["reservation"]):
                continue
            hour, minute = int(row["starttime"][:2]), int(row["starttime"][2:])
            start_at = dt.datetime.combine(day, dt.time(hour, minute), JST)
            if start_at <= now:
                continue
            key = f"{row['date']}-{row['starttime']}-{row['endtime']}-{label}"
            slots[key] = {
                "date": day.isoformat(),
                "time": f"{hour:02d}:{minute:02d}",
                "label": label,
                "available": int(row["capacity"]) - int(row["reservation"]),
            }
    return slots


def github(method, path, payload=None):
    repository = os.environ["GITHUB_REPOSITORY"]
    return request_json(
        f"https://api.github.com/repos/{repository}/{path}",
        method=method,
        payload=payload,
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )


def load_state():
    for issue in github("GET", "issues?state=open&per_page=100"):
        if "pull_request" not in issue and issue["title"] == STATE_TITLE:
            try:
                state = json.loads(issue["body"] or "{}")
            except json.JSONDecodeError:
                raise RuntimeError("Notification state issue has invalid JSON")
            return issue["number"], state
    state = {"email_sent": []}
    issue = github("POST", "issues", {"title": STATE_TITLE, "body": json.dumps(state)})
    return issue["number"], state


def save_state(number, state):
    github("PATCH", f"issues/{number}", {"body": json.dumps(state, ensure_ascii=False)})


def message_for(slots, keys):
    lines = ["江東運転免許試験場の本免学科試験に空きが出ました。"]
    for key in sorted(keys)[:10]:
        slot = slots[key]
        lines.append(
            f"{slot['date']} {slot['time']} 残り{slot['available']}枠 {slot['label']}"
        )
    if len(keys) > 10:
        lines.append(f"ほか{len(keys) - 10}件")
    lines.append(f"予約入口: {ENTRY}")
    return "\n".join(lines)


def send_email(message):
    mail = EmailMessage()
    mail["Subject"] = "江東・学科試験の空き枠"
    mail["From"] = os.environ["GMAIL_ADDRESS"]
    mail["To"] = os.environ["MAIL_TO"]
    mail.set_content(message)
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
        smtp.send_message(mail)


def run():
    if "--probe" in sys.argv:
        today = dt.datetime.now(JST).date()
        slots = get_open_slots(today, today + dt.timedelta(days=7))
        print(f"Probe succeeded. Open slots in the next 7 days: {len(slots)}")
        return

    required = (
        "GITHUB_REPOSITORY", "GH_TOKEN", "GMAIL_ADDRESS", "GMAIL_APP_PASSWORD",
        "MAIL_TO",
    )
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError("Missing configuration: " + ", ".join(missing))
    if TIME_OF_DAY not in ("all", "morning", "afternoon"):
        raise RuntimeError("TIME_OF_DAY must be all, morning, or afternoon")

    today = dt.datetime.now(JST).date()
    start = max(today, dt.date.fromisoformat(os.getenv("START_DATE") or today.isoformat()))
    end = dt.date.fromisoformat(os.getenv("END_DATE") or (today + dt.timedelta(days=90)).isoformat())
    if end < start or end > today + dt.timedelta(days=90):
        raise RuntimeError("END_DATE must be within the next 90 days and after START_DATE")

    slots = get_open_slots(start, end)
    issue_number, state = load_state()
    current = set(slots)
    print(f"Open slots: {len(current)}")

    previous = set(state.get("email_sent", [])) & current
    pending = current - previous
    if pending:
        send_email(message_for(slots, pending))
        previous.update(pending)
        print(f"Email: notified {len(pending)} slots")
    state = {"email_sent": sorted(previous)}
    save_state(issue_number, state)


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        # Avoid logging exception URLs/headers, which might contain secrets.
        print(f"Watch failed: {type(exc).__name__}: {exc if isinstance(exc, RuntimeError) else 'external request or delivery failed'}", file=sys.stderr)
        raise SystemExit(1)
