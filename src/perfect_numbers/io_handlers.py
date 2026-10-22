"""Ввод и вывод данных: консоль, TXT, CSV, JSON."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Callable

SUPPORTED_INPUT = (".txt", ".csv", ".json")
_SEPARATORS = re.compile(r"[\s,;]+")
_INT = re.compile(r"[+-]?\d+")


class InputError(ValueError):
    """Некорректные входные данные или файл."""


def _to_int(token, where: str) -> int:
    if isinstance(token, bool):
        raise InputError(f"{where}: ожидалось целое число.")
    if isinstance(token, int):
        return token
    text = str(token).strip()
    if not _INT.fullmatch(text):
        raise InputError(f"{where}: «{text}» не является целым числом.")
    return int(text)


def parse_range_text(text: str) -> tuple[int, int]:
    """Разбор текста TXT/CSV: два целых числа (начало и конец диапазона).

    Допустимы разделители: пробел, запятая, «;», табуляция, перевод строки.
    Пустые строки, строки-комментарии (#) и заголовок «start,end» игнорируются.
    """
    values: list[int] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip().lstrip("\ufeff")
        if not line or line.startswith("#"):
            continue
        tokens = [t for t in _SEPARATORS.split(line) if t]
        if not values and [t.lower() for t in tokens] in (
            ["start", "end"], ["начало", "конец"], ["from", "to"],
        ):
            continue
        for token in tokens:
            values.append(_to_int(token, f"Строка {number}"))
    if len(values) != 2:
        raise InputError(
            f"Ожидалось ровно два числа (начало и конец диапазона), найдено: {len(values)}."
        )
    return values[0], values[1]


def parse_range_json(text: str) -> tuple[int, int]:
    """JSON: {"start": 1, "end": 100} или [1, 100]."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise InputError(f"Некорректный JSON: {err}") from err
    if isinstance(data, dict):
        if "start" not in data or "end" not in data:
            raise InputError('В JSON должны быть поля "start" и "end".')
        return _to_int(data["start"], "Поле start"), _to_int(data["end"], "Поле end")
    if isinstance(data, list) and len(data) == 2:
        return _to_int(data[0], "Элемент 1"), _to_int(data[1], "Элемент 2")
    raise InputError('JSON должен быть объектом {"start", "end"} или списком из двух чисел.')


def read_range_file(path: str | Path) -> tuple[int, int]:
    """Чтение диапазона из файла TXT / CSV / JSON (формат — по расширению)."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_INPUT:
        raise InputError(
            f"Неподдерживаемый формат «{path.suffix}». Допустимо: {', '.join(SUPPORTED_INPUT)}."
        )
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise InputError(f"Файл не найден: {path}") from None
    except (OSError, UnicodeDecodeError) as err:
        raise InputError(f"Не удалось прочитать файл {path}: {err}") from err
    if suffix == ".json":
        return parse_range_json(text)
    return parse_range_text(text)


def read_range_console(
    input_func: Callable[[str], str] | None = None, attempts: int = 3
) -> tuple[int, int]:
    """Интерактивный ввод границ диапазона (до `attempts` попыток на каждое число)."""
    input_func = input_func or input
    values = []
    for label in ("начало", "конец"):
        for attempt in range(attempts):
            raw = input_func(f"Введите {label} диапазона: ")
            try:
                values.append(_to_int(raw, "Ввод"))
                break
            except InputError as err:
                print(f"Ошибка: {err}", file=sys.stderr)
        else:
            raise InputError(f"Превышено число попыток ввода ({attempts}).")
    return values[0], values[1]


def format_result(result: dict) -> str:
    """Текстовое представление результата сканирования."""
    numbers = ", ".join(str(n) for n in result["numbers"]) or "—"
    return (
        f"Диапазон: {result['start']} – {result['end']}\n"
        f"Найдено совершенных чисел: {result['count']}\n"
        f"Числа: {numbers}"
    )


def write_result_file(path: str | Path, result: dict) -> None:
    """Запись результата: .json — JSON, иначе — текст."""
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".json":
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            path.write_text(format_result(result) + "\n", encoding="utf-8")
    except OSError as err:
        raise InputError(f"Не удалось записать файл {path}: {err}") from err
