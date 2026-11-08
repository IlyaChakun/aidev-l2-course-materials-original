"""In stdio mode stdout belongs to the protocol: no print(), logs go to stderr only."""
import ast
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from .helpers import make_db

PKG = Path(__file__).resolve().parents[1]


class NoPrintTest(unittest.TestCase):
    def test_no_print_calls_in_package(self):
        offenders = []
        for path in (PKG / "support").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                    offenders.append(f"{path.relative_to(PKG)}:{node.lineno}")
        self.assertEqual(offenders, [])


class StdoutProtocolOnlyTest(unittest.TestCase):
    def test_every_stdout_line_is_json_rpc(self):
        tmp, db = make_db()
        self.addCleanup(tmp.cleanup)
        env = {**os.environ, "SUPPORT_DB_PATH": str(db), "MCP_TRANSPORT": "stdio", "MCP_LOG_LEVEL": "DEBUG"}
        proc = subprocess.Popen(
            [sys.executable, "-m", "support"], cwd=PKG, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}}
        try:
            out, err = proc.communicate(json.dumps(init) + "\n", timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate()
        lines = [ln for ln in out.splitlines() if ln.strip()]
        self.assertTrue(lines, f"the server did not respond; stderr: {err[-500:]}")
        for ln in lines:
            msg = json.loads(ln)
            self.assertEqual(msg.get("jsonrpc"), "2.0", ln[:200])
        self.assertIn("starting transport=stdio", err)


if __name__ == "__main__":
    unittest.main()
