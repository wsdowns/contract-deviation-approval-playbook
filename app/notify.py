"""Email notifications that carry a link. Nobody reads email replies: decisions are made in the portal.

Backends: file (write each message to the run's notifications folder, for demos and testing) and smtp
(send it). The SMTP password comes from the environment variable named in config, never from the file.
"""
import os
import smtplib
import re
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path


def send(cfg_mail, run_dir, to, cc, subject, body):
    """to and cc are lists of addresses. Returns where it went."""
    cc = [c for c in dict.fromkeys(cc) if c and c not in to]
    if cfg_mail["backend"] == "smtp":
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = cfg_mail["from_address"], ", ".join(to), subject
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg.set_content(body)
        with smtplib.SMTP(cfg_mail["host"], cfg_mail["port"], timeout=30) as s:
            if cfg_mail["starttls"]:
                s.starttls()
            if cfg_mail["user"]:
                s.login(cfg_mail["user"], os.environ.get(cfg_mail["password_env"], ""))
            s.send_message(msg, to_addrs=to + cc)
        return "sent by smtp"
    d = Path(run_dir) / "notifications"
    d.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")[:40]
    f = d / f"{datetime.now().strftime('%H%M%S%f')}-{slug}.txt"
    f.write_text(f"To: {', '.join(to)}\nCc: {', '.join(cc)}\nSubject: {subject}\n\n{body}\n", encoding="utf-8")
    return f"written to {f.name}"
