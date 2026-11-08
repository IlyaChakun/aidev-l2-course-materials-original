import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mask_secrets import MASK, mask  # noqa: E402


class MaskSecretsTest(unittest.TestCase):
    def assertMasked(self, line, secret):
        out = mask(line)
        self.assertNotIn(secret, out, out)
        self.assertIn(MASK, out)

    def test_openai_like_key(self):
        self.assertMasked("key is sk-abcdEFGH12345678xyz here", "sk-abcdEFGH12345678xyz")

    def test_langfuse_keys(self):
        self.assertMasked("pk-lf-0123456789abcdef", "pk-lf-0123456789abcdef")
        self.assertMasked("sk-lf-0123456789abcdef", "sk-lf-0123456789abcdef")

    def test_bearer(self):
        self.assertMasked("Authorization: Bearer abc.def-123_XYZ", "abc.def-123_XYZ")

    def test_api_key_assign(self):
        self.assertMasked("api_key=SuperSecretValue99", "SuperSecretValue99")
        self.assertMasked("API-KEY: SuperSecretValue99", "SuperSecretValue99")

    def test_token_assign_json(self):
        self.assertMasked('{"token": "SuperSecretValue99"}', "SuperSecretValue99")

    def test_env_style(self):
        self.assertMasked("LLM_API_KEY=SuperSecretValue99", "SuperSecretValue99")

    def test_github_token(self):
        self.assertMasked("ghp_" + "a" * 36, "a" * 36)

    def test_plain_text_untouched(self):
        line = "update_ticket(ticket_id=7, new_status='answered') OK\n"
        self.assertEqual(mask(line), line)

    def test_keeps_keyword_names(self):
        out = mask("token=abcdef123456")
        self.assertTrue(out.startswith("token="), out)

    def test_runlog_script_end_to_end(self):
        secret = "sk-ENDTOEND123456789"
        res = subprocess.run(
            [str(ROOT / "scripts" / "runlog.sh"), "1", "selftest-mask", f"echo token={secret}; echo Bearer {secret}"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        logs = sorted((ROOT / "m1" / "runs").glob("*selftest-mask.log"))
        self.assertTrue(logs, "лог не создан")
        try:
            body = logs[-1].read_text()
            self.assertNotIn(secret, body)
            self.assertNotIn(secret, res.stdout)
            self.assertIn("command:", body)
            self.assertIn("git:", body)
        finally:
            for p in logs:
                p.unlink()


if __name__ == "__main__":
    unittest.main()
