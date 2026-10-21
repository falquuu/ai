import json
import tempfile
import unittest
from pathlib import Path

from perfect_numbers.io_handlers import (
    InputError, format_result, parse_range_json, parse_range_text,
    read_range_console, read_range_file, write_result_file,
)


class TestParsing(unittest.TestCase):
    def test_text_separators(self):
        for text in ("1 100", "1,100", "1;100", "1\t100", "1\n100", "  1 ,  100  "):
            with self.subTest(text=text):
                self.assertEqual(parse_range_text(text), (1, 100))

    def test_text_header_comments_blank_lines(self):
        self.assertEqual(parse_range_text("# комментарий\n\nstart,end\n5,50\n"), (5, 50))

    def test_text_wrong_count(self):
        for text in ("", "1", "1 2 3"):
            with self.assertRaises(InputError):
                parse_range_text(text)

    def test_text_not_integer_has_line_number(self):
        with self.assertRaises(InputError) as ctx:
            parse_range_text("1 2\n3 abc")
        self.assertIn("Строка 2", str(ctx.exception))

    def test_float_rejected(self):
        with self.assertRaises(InputError):
            parse_range_text("1.5 10")

    def test_json_formats(self):
        self.assertEqual(parse_range_json('{"start": 1, "end": 9}'), (1, 9))
        self.assertEqual(parse_range_json("[3, 30]"), (3, 30))

    def test_json_errors(self):
        for text in ("{bad", '{"start": 1}', "[1]", '"x"', '{"start": "a", "end": 2}',
                     '{"start": true, "end": 2}'):
            with self.subTest(text=text):
                with self.assertRaises(InputError):
                    parse_range_json(text)


class TestFiles(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, name, text):
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_read_txt_csv_json(self):
        self.assertEqual(read_range_file(self._write("a.txt", "1 100")), (1, 100))
        self.assertEqual(read_range_file(self._write("a.csv", "start,end\n2,20")), (2, 20))
        self.assertEqual(read_range_file(self._write("a.json", '{"start":3,"end":30}')), (3, 30))

    def test_read_with_bom(self):
        path = self.dir / "bom.txt"
        path.write_bytes("\ufeff1 100".encode("utf-8"))
        self.assertEqual(read_range_file(path), (1, 100))

    def test_missing_file(self):
        with self.assertRaises(InputError):
            read_range_file(self.dir / "nope.txt")

    def test_unsupported_extension(self):
        with self.assertRaises(InputError):
            read_range_file(self._write("a.xml", "<a/>"))

    def test_write_result_text_and_json(self):
        result = {"start": 1, "end": 100, "count": 2, "numbers": [6, 28]}
        txt, js = self.dir / "sub" / "r.txt", self.dir / "r.json"
        write_result_file(txt, result)
        write_result_file(js, result)
        self.assertIn("Найдено совершенных чисел: 2", txt.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(js.read_text(encoding="utf-8")), result)

    def test_format_result_empty(self):
        text = format_result({"start": 1, "end": 5, "count": 0, "numbers": []})
        self.assertIn("Числа: —", text)


class TestConsole(unittest.TestCase):
    def test_console_ok(self):
        answers = iter(["1", "100"])
        self.assertEqual(read_range_console(lambda _: next(answers)), (1, 100))

    def test_console_retry_after_bad_input(self):
        answers = iter(["abc", "1", "100"])
        self.assertEqual(read_range_console(lambda _: next(answers)), (1, 100))

    def test_console_attempts_exceeded(self):
        with self.assertRaises(InputError):
            read_range_console(lambda _: "x", attempts=2)


if __name__ == "__main__":
    unittest.main()
