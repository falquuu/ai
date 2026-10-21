import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from perfect_numbers.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.storage = ["--data-file", str(self.dir / "history.json"),
                        "--backup-dir", str(self.dir / "backups")]

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *args, stdin=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            if stdin is not None:
                with mock.patch("builtins.input", side_effect=stdin):
                    code = main(list(args))
            else:
                code = main(list(args))
        return code, out.getvalue(), err.getvalue()


class TestFind(CliTestCase):
    def test_find_with_arguments(self):
        code, out, _ = self.run_cli("find", "-s", "1", "-e", "10000")
        self.assertEqual(code, 0)
        self.assertIn("Найдено совершенных чисел: 4", out)
        self.assertIn("6, 28, 496, 8128", out)

    def test_find_from_each_file_format(self):
        for name in ("range_small.txt", "range.csv", "range.json"):
            with self.subTest(name=name):
                code, out, _ = self.run_cli("find", "-i", str(EXAMPLES / name))
                self.assertEqual(code, 0)
                self.assertIn("6, 28", out)

    def test_find_from_console(self):
        code, out, _ = self.run_cli("find", stdin=["1", "100"])
        self.assertEqual(code, 0)
        self.assertIn("Числа: 6, 28", out)

    def test_find_output_files(self):
        txt, js = self.dir / "r.txt", self.dir / "r.json"
        self.assertEqual(self.run_cli("find", "-s", "1", "-e", "100", "-o", str(txt))[0], 0)
        self.assertEqual(self.run_cli("find", "-s", "1", "-e", "100", "-o", str(js))[0], 0)
        self.assertIn("6, 28", txt.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(js.read_text(encoding="utf-8"))["numbers"], [6, 28])

    def test_invalid_range_exit_1(self):
        code, _, err = self.run_cli("find", "-i", str(EXAMPLES / "range_invalid.txt"))
        self.assertEqual(code, 1)
        self.assertIn("Ошибка", err)

    def test_missing_file_exit_1(self):
        self.assertEqual(self.run_cli("find", "-i", str(self.dir / "no.txt"))[0], 1)

    def test_conflicting_sources_exit_1(self):
        code, *_ = self.run_cli("find", "-i", str(EXAMPLES / "range.csv"), "-s", "1", "-e", "5")
        self.assertEqual(code, 1)

    def test_only_one_bound_exit_1(self):
        self.assertEqual(self.run_cli("find", "-s", "1")[0], 1)

    def test_bad_arguments_exit_2(self):
        self.assertEqual(self.run_cli("find", "-s", "abc", "-e", "5")[0], 2)
        self.assertEqual(self.run_cli("unknown")[0], 2)
        self.assertEqual(self.run_cli()[0], 2)


class TestHistoryCommands(CliTestCase):
    def test_save_and_history(self):
        code, out, _ = self.run_cli("find", "-s", "1", "-e", "100", "--save", *self.storage)
        self.assertEqual(code, 0)
        self.assertIn("Запись №1", out)
        _, out, _ = self.run_cli("history", *self.storage)
        self.assertIn("[1; 100]", out)

    def test_history_empty(self):
        _, out, _ = self.run_cli("history", *self.storage)
        self.assertIn("История пуста", out)

    def test_full_cycle_save_backup_change_restore(self):
        self.run_cli("find", "-s", "1", "-e", "100", "--save", *self.storage)
        self.assertEqual(self.run_cli("backup", *self.storage)[0], 0)
        self.run_cli("find", "-s", "1", "-e", "10000", "--save", *self.storage)
        self.assertEqual(self.run_cli("restore", *self.storage)[0], 0)
        _, out, _ = self.run_cli("history", *self.storage)
        self.assertIn("[1; 100]", out)
        self.assertNotIn("[1; 10000]", out)

    def test_list_and_verify(self):
        self.run_cli("find", "-s", "1", "-e", "100", "--save", *self.storage)
        self.run_cli("backup", *self.storage)
        code, out, _ = self.run_cli("list-backups", *self.storage)
        self.assertEqual(code, 0)
        self.assertIn("OK", out)
        code, out, _ = self.run_cli("verify", *self.storage)
        self.assertEqual(code, 0)
        self.assertIn("повреждено: 0", out)

    def test_verify_corrupt_exit_3(self):
        self.run_cli("find", "-s", "1", "-e", "100", "--save", *self.storage)
        self.run_cli("backup", *self.storage)
        next((self.dir / "backups").glob("history_*.json")).write_text("x", encoding="utf-8")
        code, out, _ = self.run_cli("verify", *self.storage)
        self.assertEqual(code, 3)
        self.assertIn("повреждено: 1", out)

    def test_backup_without_storage_exit_3(self):
        self.assertEqual(self.run_cli("backup", *self.storage)[0], 3)

    def test_restore_without_backups_exit_3(self):
        self.assertEqual(self.run_cli("restore", *self.storage)[0], 3)

    def test_restore_corrupt_file_exit_3(self):
        bad = self.dir / "history_bad.json"
        bad.write_text("x", encoding="utf-8")
        self.assertEqual(self.run_cli("restore", "--file", str(bad), *self.storage)[0], 3)

    def test_save_into_corrupt_storage_exit_3(self):
        (self.dir / "history.json").write_text("мусор", encoding="utf-8")
        code, *_ = self.run_cli("find", "-s", "1", "-e", "100", "--save", *self.storage)
        self.assertEqual(code, 3)


if __name__ == "__main__":
    unittest.main()
