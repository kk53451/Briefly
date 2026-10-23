"""외부 API 호출 없이 대본 검증 CLI의 성공·실패 종료 코드를 확인합니다."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test import generate_integrated_briefing_dryrun as dryrun


class DryrunExitTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.sample = self.root / "sample.json"
        self.sample.write_text('{"articles": []}', encoding="utf-8")
        argv = patch("sys.argv", ["dryrun", "--data-path", str(self.sample)])
        argv.start()
        self.addCleanup(argv.stop)

    def test_missing_sample_fails(self):
        with patch("sys.argv", ["dryrun", "--data-path", str(self.root / "missing.json")]):
            self.assertEqual(dryrun.main(), 1)

    def test_feed_error_fails(self):
        with patch.object(dryrun, "build_category_data", side_effect=RuntimeError("test")):
            self.assertEqual(dryrun.main(), 1)

    def run_with_script(self, script):
        category = {"category_ko": "정치", "topics": []}
        with (
            patch.object(dryrun, "build_category_data", return_value=category),
            patch("app.services.embedding_service.unload_model"),
            patch("app.services.script_service.generate_script", return_value=script),
            patch.object(dryrun, "OUTPUT_DIR", self.root / "results"),
        ):
            return dryrun.main()

    def test_empty_script_fails_without_output(self):
        self.assertEqual(self.run_with_script(""), 1)
        self.assertFalse((self.root / "results").exists())

    def test_success_writes_script(self):
        script = "정치·경제·국제 테스트 대본"
        self.assertEqual(self.run_with_script(script), 0)
        outputs = list((self.root / "results").glob("*.txt"))
        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].read_text(encoding="utf-8"), script)


if __name__ == "__main__":
    unittest.main()
