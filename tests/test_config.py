"""Config loading, the gate, and the model backends (against a fake OpenAI-style server)."""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import config  # noqa: E402
import models  # noqa: E402

SEEN = {}


class Fake(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN.update(path=self.path, auth=self.headers.get("Authorization"), body=body)
        out = json.dumps({"choices": [{"message": {"content": " hello from open weights "}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


@pytest.fixture
def server():
    s = HTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/v1"
    s.shutdown()


def toml(tmp_path, text):
    p = tmp_path / "config.toml"
    p.write_text(text)
    return p


def test_defaults_match_the_example():
    cfg = config.load(ROOT / "no-such-config.toml")
    assert cfg["model"]["backend"] == "claude-cli" and cfg["environment"]["stand_in_data_only"]


def test_example_config_loads():
    cfg = config.load(ROOT / "config.example.toml")
    assert Path(cfg["matrix"]["folder"]).is_dir()


def test_openai_compatible_needs_no_key_for_local_servers(server):
    m = {**config.DEFAULTS["model"], "backend": "openai-compatible", "name": "llama3.1:70b", "base_url": server}
    assert models.ask("hi", m) == "hello from open weights"
    assert SEEN["path"] == "/v1/chat/completions" and SEEN["auth"] is None
    assert SEEN["body"]["model"] == "llama3.1:70b" and SEEN["body"]["messages"][1]["content"] == "hi"


def test_key_is_read_from_the_named_variable(server, monkeypatch):
    monkeypatch.setenv("MY_KEY", "sekret")
    m = {**config.DEFAULTS["model"], "backend": "openai-compatible", "name": "x", "base_url": server, "api_key_env": "MY_KEY"}
    models.ask("hi", m)
    assert SEEN["auth"] == "Bearer sekret"


def test_empty_key_variable_is_a_clear_error(server, monkeypatch):
    monkeypatch.delenv("MY_KEY", raising=False)
    m = {**config.DEFAULTS["model"], "backend": "openai-compatible", "name": "x", "base_url": server, "api_key_env": "MY_KEY"}
    with pytest.raises(RuntimeError, match="MY_KEY"):
        models.ask("hi", m)


def test_command_backend_pipes_the_prompt():
    m = {**config.DEFAULTS["model"], "backend": "command", "command": "cat"}
    assert models.ask("echo me", m) == "echo me"


def test_unreachable_server_is_a_clear_error():
    m = {**config.DEFAULTS["model"], "backend": "openai-compatible", "name": "x", "base_url": "http://127.0.0.1:9/v1"}
    with pytest.raises(RuntimeError, match="Could not reach"):
        models.ask("hi", m)


@pytest.mark.parametrize("text,msg", [
    ('[model]\nbackend = "nope"', "backend must be"),
    ('[model]\nbackend = "openai-compatible"\nname = "x"', "base_url"),
    ('[model]\nbackend = "anthropic-api"\nname = "x"\napi_key_env = "sk-ant-real-looking-key"', "NAME of the variable|variable name"),
    ('[matrix]\nfolder = "missing"', "Matrix folder not found"),
    ('[model]\nbogus = 1', "Unknown setting"),
    ('[other]\nx = 1', "Unknown section"),
])
def test_bad_config_gives_a_plain_message(tmp_path, text, msg):
    with pytest.raises(config.ConfigError, match=msg):
        config.load(toml(tmp_path, text))


def test_real_deal_mode_is_blocked_until_the_gate_is_recorded(tmp_path):
    cfg = config.load(toml(tmp_path, '[app]\nmode = "live"\n[auth]\nprovider = "proxy-header"\n[environment]\nstand_in_data_only = false\n'))
    assert "environment record" in config.gate_problem(cfg)
    cfg["environment"].update(name="Private vLLM, Model X 1.0", approved_by="GC", approved_on="2026-12-01")
    assert "zero_data_retention" in config.gate_problem(cfg)
    cfg["environment"]["private_instance"] = True
    assert config.gate_problem(cfg) == ""


def test_demo_mode_cannot_send_email_or_touch_real_data(tmp_path):
    with pytest.raises(config.ConfigError, match="never sends email"):
        config.load(toml(tmp_path, '[mail]\nbackend = "smtp"\nhost = "h"\nfrom_address = "a@b.c"\n'))
    with pytest.raises(config.ConfigError, match="fictional data only"):
        config.load(toml(tmp_path, "[environment]\nstand_in_data_only = false\n"))
    cfg = config.load(toml(tmp_path, '[app]\nmode = "live"\n[auth]\nprovider = "local"\n[mail]\nbackend = "smtp"\nhost = "h"\nfrom_address = "a@b.c"\n'))
    assert cfg["app"]["mode"] == "live"
    with pytest.raises(config.ConfigError, match="demo.*live"):
        config.load(toml(tmp_path, '[app]\nmode = "both"\n'))


def test_live_mode_refuses_to_run_open_to_everyone(tmp_path):
    with pytest.raises(config.ConfigError, match="Live mode needs a sign-in method"):
        config.load(toml(tmp_path, '[app]\nmode = "live"\n[environment]\nstand_in_data_only = false\n[mail]\nbackend = "file"\n'))


def test_reasoning_effort_must_be_a_known_value():
    cfg = config.load()
    cfg["model"]["reasoning_effort"] = "low"
    config.validate(cfg)
    cfg["model"]["reasoning_effort"] = "extreme"
    with pytest.raises(config.ConfigError, match="reasoning_effort"):
        config.validate(cfg)
