# 🔢 perfect-numbers-tool

[🇷🇺 Русский](README.md) · 🇬🇧 English

## 📋 Project description

A Python console program that finds **all perfect numbers in a user-defined range** (a perfect number equals the sum of its positive divisors, excluding the number itself: 6 = 1 + 2 + 3), with input and output via console or file. The project includes a **backup and restore subsystem for the history of number-line scans**, user documentation and test cases.

## 🎯 Assignment

1. Create a Python console program that finds all perfect numbers in a user-defined range (input/output via file and console).
2. Develop an algorithm for backing up and restoring the history of mathematical number-line scans.
3. Write user documentation (technical specification, README in Russian and English, maintenance regulations) and commit it together with the project to GitHub.
4. Write test cases and verify that the key modules comply with the specification.

## 🛠️ Technologies

- **Python 3.10+** — main programming language
- **Standard library** — `argparse`, `json`, `hashlib`, `pathlib`, `math`, `array`, `tempfile` (no external dependencies)
- **unittest / pytest** — automated tests
- **Git and GitHub Actions** — version control and automatic test runs (Windows, Linux, macOS)

## 📦 Installation and launch

### 1. Clone the repository

```bash
git clone https://github.com/falquuu/ai.git
cd ai
```

### 2. Install dependencies

The program needs no dependencies. For development (optional):

```bash
pip install -r requirements.txt
```

### 3. Run the program

```bash
python -m perfect_numbers find -i examples/range_small.txt
```

Output (the program messages are in Russian):

```
Диапазон: 1 – 100
Найдено совершенных чисел: 2
Числа: 6, 28
```

> If Python cannot find the module, run from the project root with `PYTHONPATH=src` (Windows PowerShell: `$env:PYTHONPATH="src"`) or install the project with `pip install -e .` — then the short command `perfect-numbers` becomes available.

### 4. Run the tests

```bash
python -m unittest discover -s tests -v
# or
python -m pytest -v
```

## 📁 Project structure

```
perfect-numbers-tool/
├── src/perfect_numbers/
│   ├── core.py          # Range validation, perfect number search
│   ├── io_handlers.py   # Input/output: console, TXT, CSV, JSON
│   ├── backup.py        # History, backup and restore
│   └── cli.py           # Command line
├── tests/               # Automated tests (test_core, test_io, test_backup, test_cli)
├── docs/
│   ├── TZ.md            # Technical specification (Russian)
│   ├── maintenance.md   # Maintenance regulations (Russian)
│   ├── test-cases.md    # Test cases and verification results (Russian)
│   └── GIT.md           # Repository rules (Russian)
├── examples/            # Sample input files
├── .github/workflows/   # CI (GitHub Actions)
├── README.md            # Documentation (Russian)
├── README.en.md         # Documentation (English)
├── pyproject.toml       # Package metadata
├── requirements.txt     # Development dependencies
└── .gitignore           # Git ignore file
```

## 🎮 Usage

### Searching for perfect numbers

```bash
# Console input: the program asks for the start and the end of the range
python -m perfect_numbers find

# Bounds as arguments
python -m perfect_numbers find -s 1 -e 10000

# Input from a file (TXT, CSV or JSON, detected by extension)
python -m perfect_numbers find -i examples/range.csv

# Result to a file (.json — JSON, otherwise text)
python -m perfect_numbers find -i examples/range_small.txt -o result.json

# Save the scan to the history data/history.json
python -m perfect_numbers find -s 1 -e 10000 --save
```

Both bounds are inclusive. Allowed: `1 ≤ start ≤ end ≤ 10¹²`, range length up to 5,000,000 numbers. `-i` and `-s/-e` cannot be combined.

### Input file formats

```
# TXT / CSV — two numbers: start and end (separator: space, comma, ";" or tab)
start,end
1,10000
```

```json
{"start": 1, "end": 10000}
```

JSON may also be a list `[1, 10000]`. Blank lines, lines starting with `#` and the `start,end` header are ignored.

### History and backups

```bash
python -m perfect_numbers history        # show scan history
python -m perfect_numbers backup         # create a history backup in backups/
python -m perfect_numbers list-backups   # list backups with integrity check
python -m perfect_numbers verify         # verify all backups
python -m perfect_numbers restore        # restore from the newest backup
python -m perfect_numbers restore --file backups/history_20261021_022708_491394.json
```

Common options: `--data-file` (default `data/history.json`), `--backup-dir` (`backups`), `--keep` (number of backups to keep, default 10).

### Using as a Python module

```python
from perfect_numbers.core import analyze, find_perfect_numbers, is_perfect, RangeError
from perfect_numbers.io_handlers import read_range_file
from perfect_numbers.backup import HistoryManager

# Calculation
print(analyze(1, 10000))
# {'start': 1, 'end': 10000, 'count': 4, 'numbers': [6, 28, 496, 8128]}

print(is_perfect(28))            # True

# Read a range from a file
start, end = read_range_file("examples/range.csv")   # (1, 10000)

# Invalid range
try:
    analyze(10, 1)
except RangeError as err:
    print(err)                   # the end of the range cannot be less than the start

# History and backups
manager = HistoryManager("data/history.json", "backups", keep=5)
manager.add_record(analyze(1, 100), elapsed=0.01)
backup = manager.create_backup()
manager.restore(backup)
```

## 📊 Main functions

### Module `core`

- `analyze(start, end)` — scan result: bounds, count and the numbers
- `find_perfect_numbers(start, end)` — list of perfect numbers in the range
- `is_perfect(n)` / `divisor_sum(n)` — check one number / sum of its proper divisors
- `divisor_sums(start, end)` — divisor sums for the whole range (segmented sieve)
- `validate_range(start, end)` — integers, `1 ≤ start ≤ end ≤ 10¹²`, length ≤ 5,000,000

### Module `io_handlers`

- `read_range_file(path)` — read a range from TXT / CSV / JSON
- `read_range_console()` — interactive console input
- `parse_range_text(text)` / `parse_range_json(text)` — parse text and JSON
- `format_result(result)` / `write_result_file(path, result)` — format as text / write TXT / JSON

### Class `HistoryManager`

- `add_record(result, elapsed)` / `load_history()` — work with the history
- `create_backup()` — create a backup with a SHA-256 manifest and rotation
- `list_backups()` / `verify_all()` — list and verify backups
- `verify_backup(path)` — verify the integrity of one backup
- `restore(path=None)` — restore (from the newest backup by default)

## 🔍 Search algorithm

A segmented divisor-sum sieve: for a range `[a; b]` an array of `b − a + 1` ones is created; for every `d` from 2 to `⌊√b⌋` and every multiple `m = d·q ≥ d²` in the range, `d` and `q` are added to `m` (only once if `q = d`). A number is perfect when its accumulated sum equals the number. Complexity: O(L·ln √b) time and O(L) memory, where L is the range length. The range `1…1,000,000` takes about 1 second.

## 🔄 Backup algorithm

1. The history storage is validated and copied to `backups/history_<date>_<time>.json`; corrupted data is never copied.
2. A manifest `*.manifest` is written next to it: SHA-256, record count, size, creation date.
3. Writes are atomic (temporary file → replace); a crash never leaves a half-written file.
4. Rotation: only the last N backups are kept (`--keep`).
5. Restore: verify the backup → save the current state as a separate backup → atomic replace. A corrupted backup is rejected and the storage stays untouched.

## 🧪 Testing

The project includes **67 automated tests** and **41 test cases**:

**Unit tests:**

- Calculation: known numbers (6, 28, 496, 8128, 33,550,336), boundaries, ranges with no result, sieve cross-checked against brute force
- Invalid ranges: start < 1, end < start, range too long, non-integer values
- TXT / CSV / JSON parsing, separators, BOM, input errors with line numbers
- Backups: manifest, rotation, corrupted backup, restore, atomicity

**Integration tests:**

- Full command-line scenarios and exit codes
- The cycle "save → backup → change → restore"

The test case table and verification results are in [docs/test-cases.md](docs/test-cases.md) (Russian).

## 💡 Examples

### Example 1: Range from a file

```bash
python -m perfect_numbers find -i examples/range_small.txt
# Found: 2 numbers — 6, 28
```

### Example 2: The first four perfect numbers

```bash
python -m perfect_numbers find -i examples/range.csv
# Numbers: 6, 28, 496, 8128
```

### Example 3: The fifth perfect number

```bash
python -m perfect_numbers find -i examples/range_mersenne.txt
# Numbers: 33550336
```

### Example 4: Invalid range

```bash
python -m perfect_numbers find -i examples/range_invalid.txt
# Error: the end of the range cannot be less than the start.
# Exit code: 1
```

### Example 5: Backup and restore

```bash
python -m perfect_numbers find -s 1 -e 100 --save
python -m perfect_numbers backup
python -m perfect_numbers find -s 1 -e 10000 --save   # history changed
python -m perfect_numbers restore                      # back to the single-record state
```

## ⚠️ Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Data error (invalid input, file not found, invalid range) |
| 2 | Invalid command-line arguments |
| 3 | Storage or backup error |

## 📚 Documentation

- [Technical specification](docs/TZ.md) (Russian)
- [Maintenance regulations](docs/maintenance.md) (Russian)
- [Test cases and results](docs/test-cases.md) (Russian)
- [Repository rules](docs/GIT.md) (Russian)
