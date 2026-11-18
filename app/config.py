"""Settings for the seller app, read from config.toml (copy config.example.toml).

With no config.toml the app runs the ACME example on the claude command, as before.
An API key is never stored in the file: the file names the environment variable that holds it.
"""
import os
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "acme-saas"

DEFAULTS = {
    "app": {"mode": "demo"},
    "demo": {"ai_approvers": True, "silent_titles": [], "delegating_titles": [], "delay_seconds": 0},
    "matrix": {"folder": str(EXAMPLE / "doa-matrix")},
    "contracts": {
        "standard_text": str(EXAMPLE / "contracts" / "ACME_SaaS_Agreement_v1.0.txt"),
        "standard_download": str(EXAMPLE / "contracts" / "ACME_SaaS_Agreement_v1.0.docx"),
    },
    "model": {"backend": "claude-cli", "name": "", "base_url": "", "api_key_env": "",
              "command": "", "max_tokens": 32000, "reasoning_effort": "", "timeout_seconds": 900},
    "auth": {"provider": "none", "users_file": "users.csv", "proxy_header": "X-Forwarded-Email", "session_hours": 12},
    "portal": {"base_url": "http://localhost:8765", "send_mode": "auto", "allow_delegation": True},
    "reminders": {"enabled": True, "first_after_days": 2, "second_after_days": 4, "escalate_after_days": 7,
                  "holidays": [], "check_minutes": 15},
    "ledger": {"path": "ledger.db", "min_requests": 20, "viewers": []},
    "mail": {"backend": "file", "host": "", "port": 587, "starttls": True, "user": "", "password_env": "", "from_address": ""},
    "environment": {"stand_in_data_only": True, "name": "", "approved_by": "", "approved_on": "",
                    "zero_data_retention": False, "private_instance": False},
}
BACKENDS = ("claude-cli", "anthropic-api", "openai-compatible", "command")
PROVIDERS = ("none", "local", "proxy-header")


class ConfigError(Exception):
    pass


def load(path=None):
    path = Path(path or os.environ.get("DOA_CONFIG") or ROOT / "config.toml")
    cfg = {k: dict(v) for k, v in DEFAULTS.items()}
    base = path.parent
    if path.is_file():
        try:
            user = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"{path.name} is not valid TOML: {e}")
        for sec, vals in user.items():
            if sec not in cfg:
                raise ConfigError(f"Unknown section [{sec}] in {path.name}. Allowed: {', '.join(cfg)}.")
            for k, v in vals.items():
                if k not in cfg[sec]:
                    raise ConfigError(f"Unknown setting '{k}' in [{sec}]. Allowed: {', '.join(cfg[sec])}.")
                cfg[sec][k] = v
        for sec, k in (("ledger", "path"), ("auth", "users_file"), ("matrix", "folder"), ("contracts", "standard_text"), ("contracts", "standard_download")):
            if k in user.get(sec, {}):
                cfg[sec][k] = str((base / cfg[sec][k]).resolve())
    lp = Path(cfg["ledger"]["path"])
    cfg["ledger"]["path"] = str(lp if lp.is_absolute() else (base if path.is_file() else ROOT) / lp)
    uf = Path(cfg["auth"]["users_file"])
    cfg["auth"]["users_file"] = str(uf if uf.is_absolute() else (base if path.is_file() else ROOT) / uf)
    cfg["_path"] = str(path) if path.is_file() else ""
    return validate(cfg)


def validate(cfg):
    m = cfg["model"]
    if m["backend"] not in BACKENDS:
        raise ConfigError(f"[model] backend must be one of: {', '.join(BACKENDS)}.")
    if m["backend"] in ("anthropic-api", "openai-compatible") and not m["name"]:
        raise ConfigError("[model] name is required for this backend (the model to call).")
    if m["backend"] == "openai-compatible" and not m["base_url"]:
        raise ConfigError("[model] base_url is required for openai-compatible, "
                          "for example http://localhost:11434/v1 for Ollama.")
    if m["backend"] == "command" and not m["command"]:
        raise ConfigError("[model] command is required for the command backend.")
    if m["backend"] == "anthropic-api" and not m["api_key_env"]:
        raise ConfigError("[model] api_key_env is required: the NAME of the variable holding your key.")
    if m["api_key_env"] and not m["api_key_env"].isidentifier():
        raise ConfigError("[model] api_key_env must be a variable name such as ANTHROPIC_API_KEY, not the key itself.")
    if m.get("reasoning_effort", "") not in ("", "off", "minimal", "low", "medium", "high"):
        raise ConfigError('[model] reasoning_effort must be blank, "off", "minimal", "low", "medium" or "high".')
    if cfg["auth"]["provider"] not in PROVIDERS:
        raise ConfigError(f"[auth] provider must be one of: {', '.join(PROVIDERS)}.")
    if cfg["app"]["mode"] not in ("demo", "live"):
        raise ConfigError('[app] mode must be "demo" or "live".')
    if cfg["app"]["mode"] == "demo":
        if cfg["mail"]["backend"] != "file":
            raise ConfigError('Demo mode never sends email: set [mail] backend to "file", or set [app] mode to "live".')
        if not cfg["environment"]["stand_in_data_only"]:
            raise ConfigError("Demo mode is for fictional data only: set [environment] stand_in_data_only to true, or set [app] mode to \"live\".")
    if cfg["app"]["mode"] == "live" and cfg["auth"]["provider"] == "none":
        raise ConfigError('Live mode needs a sign-in method: set [auth] provider to "local" or "proxy-header". '
                          '"none" lets anyone who can reach the app use it.')
    d = cfg["demo"]
    if not all(isinstance(d[k], list) for k in ("silent_titles", "delegating_titles")) or not isinstance(d["delay_seconds"], (int, float)):
        raise ConfigError("[demo] silent_titles and delegating_titles must be lists of titles, and delay_seconds a number.")
    r = cfg["reminders"]
    ints = (r["first_after_days"], r["second_after_days"], r["escalate_after_days"], r["check_minutes"])
    if not all(isinstance(x, int) and x >= 1 for x in ints) or not (r["first_after_days"] < r["second_after_days"] < r["escalate_after_days"]):
        raise ConfigError("[reminders] needs whole numbers with first_after_days < second_after_days < escalate_after_days, and check_minutes of 1 or more.")
    if not isinstance(r["holidays"], list) or not all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(h)) for h in r["holidays"]):
        raise ConfigError("[reminders] holidays must be a list of dates such as \"2026-12-25\".")
    if not isinstance(cfg["ledger"]["viewers"], list) or not isinstance(cfg["ledger"]["min_requests"], int):
        raise ConfigError("[ledger] viewers must be a list of emails and min_requests a whole number.")
    if cfg["portal"]["send_mode"] not in ("auto", "confirm"):
        raise ConfigError('[portal] send_mode must be "auto" or "confirm".')
    if cfg["mail"]["backend"] not in ("file", "smtp"):
        raise ConfigError('[mail] backend must be "file" (write messages to the run folder) or "smtp".')
    if cfg["mail"]["backend"] == "smtp" and not (cfg["mail"]["host"] and cfg["mail"]["from_address"]):
        raise ConfigError("[mail] host and from_address are required for the smtp backend.")
    if cfg["mail"]["password_env"] and not cfg["mail"]["password_env"].isidentifier():
        raise ConfigError("[mail] password_env must be a variable name, not the password itself.")
    if not Path(cfg["matrix"]["folder"]).is_dir():
        raise ConfigError(f"Matrix folder not found: {cfg['matrix']['folder']}")
    for k in ("standard_text",):
        if not Path(cfg["contracts"][k]).is_file():
            raise ConfigError(f"Standard agreement text not found: {cfg['contracts'][k]}")
    return cfg


def gate_problem(cfg):
    """Why a real deal may not run here yet, or '' if it may."""
    e = cfg["environment"]
    if e["stand_in_data_only"]:
        return ""
    miss = [k for k in ("name", "approved_by", "approved_on") if not e[k]]
    if miss:
        return "Real-deal mode needs the AI environment record: fill in " + ", ".join(miss) + " under [environment]."
    if not (e["zero_data_retention"] or e["private_instance"]):
        return "Real-deal mode needs zero_data_retention or private_instance set to true (setup gate, requirement 1)."
    return ""
