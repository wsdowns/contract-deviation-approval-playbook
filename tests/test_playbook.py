import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = ROOT / "playbook"
STAGES = ["01-identify.md", "02-locate.md", "03-draft-requests.md", "04-record-decisions.md"]
STATUSES = ["Approved", "Conditional", "Partial", "Unclear", "Missing co-approval",
            "Wrong authority", "Authority unclear", "Not in matrix", "Not approvable", "Denied"]
FINAL_OUTCOMES = ["Conceded as approved", "Not conceded", "Conceded differently"]


def text(name):
    return (PLAYBOOK / name).read_text(encoding="utf-8")


def all_prompts():
    return "\n".join(text(n) for n in ["00-standing-instructions.md", *STAGES])


@pytest.mark.parametrize("name", ["00-standing-instructions.md", *STAGES])
def test_prompt_files_exist_and_have_no_em_dash(name):
    assert "—" not in text(name)


@pytest.mark.parametrize("name", STAGES)
def test_stage_has_required_sections(name):
    body = text(name)
    for heading in ("## Purpose", "## Inputs", "## Output" if name != "03-draft-requests.md" else "## Request format", "## Rules", "## Check before you finish"):
        assert heading in body, f"{name} lacks {heading}"


def test_every_status_is_defined_in_the_docs():
    doc = (ROOT / "docs" / "escalation-path.md").read_text(encoding="utf-8")
    for s in STATUSES:
        assert f"| {s} |" in doc, f"{s} missing from escalation-path.md"


def test_standing_instructions_list_every_status():
    body = text("00-standing-instructions.md")
    for s in STATUSES:
        assert s in body


def test_stage_four_uses_every_status_and_final_outcome():
    body = text("04-record-decisions.md")
    for s in STATUSES:
        assert s in body, f"{s} not used in stage 4"
    for o in FINAL_OUTCOMES:
        assert o in body


def test_no_case_specific_content_in_prompts():
    banned = ["Brightwater", "Lakeshore", "Summit Ridge", "Darla", "Vivian", "Grace Colton",
              "Celeste", "Casey", "ACME", "HITRUST", "willful misconduct"]
    body = all_prompts()
    for word in banned:
        assert word not in body, f"prompts mention {word!r}"


def test_prompts_reference_files_that_exist():
    for path in re.findall(r"`(docs/[a-z\-]+\.md)`", all_prompts()):
        assert (ROOT / path).exists(), path


def test_denials_get_a_seller_note_that_offers_no_concession():
    body = text("03-draft-requests.md")
    assert "## Seller note" in body
    assert "Do not suggest a concession" in body
    assert "internal by default" in body
    four = text("04-record-decisions.md")
    assert "## Seller note" in four and "do not suggest a concession" in four.lower()


def test_requests_are_separable():
    assert "### Request N" in text("03-draft-requests.md")


def test_stage1_keeps_one_cell_as_one_deviation():
    text = (ROOT / "playbook" / "01-identify.md").read_text() if "ROOT" in globals() else Path("playbook/01-identify.md").read_text()
    assert "never separate rows, separate requests or separate record entries" in text


def test_playbook_requires_the_ai_environment_gate():
    base = Path(__file__).resolve().parents[1]
    gate = (base / "docs" / "ai-environment.md").read_text()
    assert "zero data retention" in gate and "private instance" in gate
    assert "ai-environment.md" in (base / "playbook" / "README.md").read_text()
