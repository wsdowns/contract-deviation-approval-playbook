"""The page's JavaScript must at least parse. The other tests read the page as text and cannot tell a broken script from a good one."""
import re
import shutil
import subprocess

import pytest

import server


@pytest.mark.skipif(not shutil.which("node"), reason="node is not installed")
def test_the_page_script_has_no_syntax_errors(tmp_path):
    js = re.search(r"<script>(.*)</script>", (server.STATIC / "index.html").read_text(), re.S).group(1)
    f = tmp_path / "page.js"
    f.write_text(js)
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
