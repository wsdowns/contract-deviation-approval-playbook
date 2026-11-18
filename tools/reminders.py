"""Run one reminder check now. Handy for cron or a systemd timer if you do not want the app's own clock.

    python tools/reminders.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import config  # noqa: E402
import reminders  # noqa: E402

if __name__ == "__main__":
    cfg = config.load()
    for line in reminders.tick(cfg, ROOT / "runs") or ["nothing due"]:
        print(line)
