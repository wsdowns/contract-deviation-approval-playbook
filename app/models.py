"""One function, ask(), that sends a prompt to whichever model the config names.

Standard library only. The prompts are plain text in and text out, so any model that can hold the
whole input and follow the stage instructions can be used. Qualify it on Case 1 before real use.
"""
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request

SYSTEM = "You are a careful contract operations assistant."
CUT_OFF = ("The model ran out of room before it finished its answer, so the answer was not used. "
           "Raise max_tokens in the [model] section of config.toml. Models that think before they answer "
           "(Haiku 5.5, for example) spend part of this limit on thinking you do not see.")


def _post(url, headers, body, timeout):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"The model server answered {e.code}: {e.read().decode(errors='replace')[:400]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not reach the model server: {e.reason}")


def _reasoning(cfg):
    """Optional: how much a thinking model may think before it answers (OpenRouter's `reasoning` setting).
    Blank leaves the model's own default. Lower is faster and cheaper; higher is slower and more careful."""
    e = cfg.get("reasoning_effort", "")
    if not e:
        return {}
    return {"reasoning": {"enabled": False} if e == "off" else {"effort": e}}


def _key(cfg):
    env = cfg["api_key_env"]
    if not env:
        return ""
    key = os.environ.get(env, "")
    if not key:
        raise RuntimeError(f"The environment variable {env} is empty. Set it in your shell, not in config.toml.")
    return key


def ask(prompt, cfg):
    """cfg is the [model] section of the config."""
    b, t = cfg["backend"], cfg["timeout_seconds"]
    if b == "claude-cli":
        cmd = ["claude", "-p", "--tools", "", "--no-session-persistence", "--disable-slash-commands",
               "--system-prompt", SYSTEM, "--setting-sources", "project"]
        if cfg["name"]:
            cmd += ["--model", cfg["name"]]
        return _run(cmd, prompt, t)
    if b == "command":
        import shlex
        return _run(shlex.split(cfg["command"]), prompt, t)
    if b == "anthropic-api":
        out = _post("https://api.anthropic.com/v1/messages",
                    {"x-api-key": _key(cfg), "anthropic-version": "2023-06-01"},
                    {"model": cfg["name"], "max_tokens": cfg["max_tokens"], "temperature": 0, "system": SYSTEM,
                     "messages": [{"role": "user", "content": prompt}]}, t)
        text = "".join(p.get("text", "") for p in out.get("content", [])).strip()
        if out.get("stop_reason") == "max_tokens" or not text:
            raise RuntimeError(CUT_OFF)
        return text
    if b == "openai-compatible":
        key = _key(cfg)
        out = _post(cfg["base_url"].rstrip("/") + "/chat/completions",
                    {"Authorization": f"Bearer {key}"} if key else {},
                    {"model": cfg["name"], "max_tokens": cfg["max_tokens"], "temperature": 0,
                     "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
                     **_reasoning(cfg)}, t)
        try:
            choice = out["choices"][0]
            text = (choice["message"].get("content") or "").strip()
        except (KeyError, IndexError, AttributeError):
            raise RuntimeError(f"Unexpected reply from the model server: {str(out)[:300]}")
        if choice.get("finish_reason") == "length" or not text:
            raise RuntimeError(CUT_OFF)
        return text
    raise RuntimeError(f"Unknown backend {b}")


def _run(cmd, prompt, timeout):
    with tempfile.TemporaryDirectory() as cwd:  # no project files or CLAUDE.md to leak in
        done = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    if done.returncode != 0:
        raise RuntimeError((done.stderr or done.stdout or "the model call failed").strip()[:500])
    return done.stdout.strip()
