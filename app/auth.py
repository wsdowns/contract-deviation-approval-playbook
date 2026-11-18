"""Who is signed in. A login method returns one thing: a verified email address.

What that person may do comes from the matrix folder: an email in people.csv is an approver, one in
sellers.csv is a seller. Providers: none (demo, pick who to act as), local (users file with salted scrypt
hashes) and proxy-header (the company's single sign-on proxy passes the verified email).
Standard library only.
"""
import base64
import csv
import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path

N, R, P = 2 ** 14, 8, 1
FAILS = {}  # email -> (count, locked_until)


def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    h = hashlib.scrypt(password.encode(), salt=salt, n=N, r=R, p=P, dklen=32)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(h).decode()}"


def check_password(password, stored):
    try:
        _, salt, h = stored.split("$")
        got = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=N, r=R, p=P, dklen=32)
        return hmac.compare_digest(got, base64.b64decode(h))
    except (ValueError, TypeError):
        return False


def read_users(path):
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, newline="", encoding="utf-8") as f:
        return {r["Email"].strip().lower(): r for r in csv.DictReader(f)}


def write_users(path, users):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Email", "Name", "Password hash"])
        w.writeheader()
        w.writerows(users.values())
    os.chmod(path, 0o600)


def secret(root):
    env = os.environ.get("DOA_SECRET")
    if env:
        return env.encode()
    f = Path(root) / ".secret"
    if not f.exists():
        f.write_text(secrets.token_hex(32))
        os.chmod(f, 0o600)
    return f.read_text().strip().encode()


def make_token(email, key, hours):
    exp = str(int(time.time() + hours * 3600))
    body = base64.urlsafe_b64encode(f"{email}|{exp}".encode()).decode()
    return f"{body}.{hmac.new(key, body.encode(), hashlib.sha256).hexdigest()}"


def read_token(token, key):
    try:
        body, sig = token.rsplit(".", 1)
        if not hmac.compare_digest(sig, hmac.new(key, body.encode(), hashlib.sha256).hexdigest()):
            return None
        email, exp = base64.urlsafe_b64decode(body.encode()).decode().split("|")
        return email if int(exp) > time.time() else None
    except (ValueError, TypeError):
        return None


def login(users_file, email, password):
    """Return the email on success, else None. Five wrong tries lock that address for a minute."""
    email = email.strip().lower()
    n, until = FAILS.get(email, (0, 0))
    if until > time.time():
        return None
    u = read_users(users_file).get(email)
    ok = bool(u) and check_password(password, u["Password hash"])
    if not u:
        hash_password(password)  # same work whether or not the address exists
    if ok:
        FAILS.pop(email, None)
        return email
    n += 1
    FAILS[email] = (n, time.time() + 60 if n >= 5 else 0)
    return None
