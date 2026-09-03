import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY_ROOT / "scripts" / "expire_reports.py"


class ExpireReportsTests(unittest.TestCase):
    def make_report(self, docs: Path, name: str, expiry: str) -> Path:
        report = docs / "2026-09-03" / "example" / name
        report.mkdir(parents=True)
        (report / "index.html").write_text("report", encoding="utf-8")
        (report / "report.json").write_text(
            json.dumps({"published_at": "2026-09-03T12:00:00+03:00", "expires_at": expiry}),
            encoding="utf-8",
        )
        return report

    def test_removes_only_expired_report_directories(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            docs = Path(raw_directory) / "docs"
            expired = self.make_report(docs, "expired", "2026-09-10")
            active = self.make_report(docs, "active", "2026-09-11")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--root", str(docs), "--today", "2026-09-10"],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(expired.exists())
            self.assertTrue(active.exists())
            self.assertIn("expired", result.stdout)
            self.assertNotIn("active", result.stdout)

    def test_dry_run_does_not_remove_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            docs = Path(raw_directory) / "docs"
            expired = self.make_report(docs, "expired", "2026-09-10")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(docs),
                    "--today",
                    "2026-09-10",
                    "--dry-run",
                ],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(expired.exists())
            self.assertIn("Would remove", result.stdout)


if __name__ == "__main__":
    unittest.main()
