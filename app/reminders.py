"""Reminders and escalation for requests nobody has answered.

The clock is business days, counted from the day the request was created. Code runs the schedule and
sends fixed-template messages; the AI is not involved. Silence is never approval: after the last
reminder the seller and the matrix owner are told at the same moment, and if people.csv names a standing
fallback contact for the approver, that person is given the request too. Nothing is decided for anyone.
"""
from datetime import date, datetime, timedelta
from pathlib import Path

import ledger
import notify
import portal


def business_days(start, end, holidays):
    """Whole business days from the start date to the end date (weekends and listed holidays skipped)."""
    d, n = start, 0
    while d < end:
        d += timedelta(days=1)
        if d.weekday() < 5 and d.isoformat() not in holidays:
            n += 1
    return n


def _owner_email(matrix):
    owner = portal.settings(matrix).get("Matrix owner", "")
    return next((p["Email"].lower() for p in portal.people(matrix) if p["Title"] == owner), "")


def _holders(q):
    return list(dict.fromkeys(q["assigned"]))


def _fallback(q, matrix):
    p = next((x for x in portal.people(matrix) if x["Email"].lower() == q["to_email"]), {})
    mail = (p.get("Fallback email") or "").strip().lower()
    return (mail, (p.get("Fallback name") or mail).strip()) if mail else ("", "")


def tick(cfg, runs, today=None, now=None):
    """Do whatever is due, at most one step per request per call. Returns a list of what was done."""
    r = cfg["reminders"]
    if not r["enabled"]:
        return []
    today = today or date.today()
    matrix = cfg["matrix"]["folder"]
    mailbox = portal.settings(matrix).get("Approvals mailbox", "")
    owner = _owner_email(matrix)
    done = []
    for run in sorted(Path(runs).glob("app-*")):
        for q in portal.load(run):
            if q["status"] != "open":
                continue
            age = business_days(datetime.fromisoformat(q["created"]).date(), today, set(r["holidays"]))
            sent = len(q.get("reminders", []))
            me = portal.seller_email(run, matrix)
            link = portal._links(cfg, q["id"])
            if age >= r["escalate_after_days"] and sent >= 2 and not q.get("escalated"):
                step = "escalated"
            elif age >= r["second_after_days"] and sent == 1:
                step = "reminder 2"
            elif age >= r["first_after_days"] and sent == 0:
                step = "reminder 1"
            else:
                continue
            with portal.LOCK:  # re-read under the lock so two ticks cannot send the same step twice
                reqs = portal.load(run)
                cur = next(x for x in reqs if x["id"] == q["id"])
                if cur["status"] != "open" or len(cur.get("reminders", [])) != sent or (step == "escalated" and cur.get("escalated")):
                    continue
                at = now or portal.now()
                if step == "escalated":
                    fb, fbname = _fallback(cur, matrix)
                    cur["escalated"] = {"at": at, "fallback": fb}
                    if fb and fb not in cur["assigned"]:
                        cur["assigned"].append(fb)
                        cur["delegations"].append({"by_email": cur["to_email"], "to": fb, "name": fbname, "at": at, "standing": True})
                else:
                    cur.setdefault("reminders", []).append({"at": at, "n": sent + 1})
                portal._save(run, reqs)
            try:
                if step == "escalated":
                    ledger.add_event(cfg, run, cur, "escalated", fb)
                    extra = (f"The standing fallback contact, {fbname}, has been given the request and can decide it.\n" if fb else
                             "There is no fallback contact for this approver. The matrix owner decides who steps in.\n")
                    notify.send(cfg["mail"], run, [x for x in (me, owner) if x], [cur["to_email"], mailbox],
                                f"No answer yet: {cur['subject']}",
                                f"{cur['to_name']} ({cur['to_title']}) has not answered after {age} business days and two reminders.\n\n"
                                f"{cur['subject']}\n{link}\n\n{extra}Silence is not approval. Nothing has been decided.\n")
                    if fb:
                        notify.send(cfg["mail"], run, [fb], [cur["to_email"], me, mailbox], f"Approval needed: {cur['subject']}",
                                    f"{cur['to_name']} ({cur['to_title']}) has not answered. You are their listed fallback contact.\n\n{link}\n")
                else:
                    ledger.add_event(cfg, run, cur, "reminder", step[-1])
                    notify.send(cfg["mail"], run, _holders(cur), [me, mailbox], f"Reminder: {cur['subject']}",
                                f"This request has been waiting {age} business days for your decision.\n\n{cur['subject']}\n{link}\n\n"
                                "Please decide in the portal. Replies to this email are not read.\n")
            except Exception as e:  # one failed message must not stop the rest; it is retried on the next check only for the next step
                done.append(f"{cur['id']}: {step} recorded but the message failed: {e}")
                continue
            done.append(f"{cur['id']}: {step}")
    return done
