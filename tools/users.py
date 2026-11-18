"""Manage the local users file (provider = "local"). Passwords are stored only as salted hashes.

    python tools/users.py add you@company.com "Your Name"     (prompts for the password)
    python tools/users.py reset you@company.com               (prompts for a new password)
    python tools/users.py list
"""
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import auth  # noqa: E402
import config  # noqa: E402


def main(argv):
    cfg = config.load()
    path = cfg["auth"]["users_file"]
    users = auth.read_users(path)
    if len(argv) >= 2 and argv[0] in ("add", "reset"):
        email = argv[1].strip().lower()
        if argv[0] == "add" and email in users:
            return print(f"{email} already exists. Use reset.") or 1
        if argv[0] == "reset" and email not in users:
            return print(f"{email} is not in the users file.") or 1
        pw = getpass.getpass("Password: ")
        if len(pw) < 12 or pw != getpass.getpass("Again: "):
            return print("Use at least 12 characters, typed the same twice.") or 1
        name = argv[2] if len(argv) > 2 else users.get(email, {}).get("Name", email)
        users[email] = {"Email": email, "Name": name, "Password hash": auth.hash_password(pw)}
        auth.write_users(path, users)
        return print(f"Saved {email} in {path}") or 0
    if argv[:1] == ["list"]:
        for u in users.values():
            print(u["Email"], u["Name"])
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
