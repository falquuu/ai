"""Командная строка: find, history, backup, list-backups, verify, restore."""

from __future__ import annotations

import argparse
import sys
import time

from . import __version__
from .backup import (
    DEFAULT_BACKUP_DIR, DEFAULT_DATA_FILE, DEFAULT_KEEP,
    BackupError, HistoryManager, StorageError,
)
from .core import RangeError, analyze, validate_range
from .io_handlers import (
    InputError, format_result, read_range_console, read_range_file, write_result_file,
)

EXIT_OK, EXIT_DATA, EXIT_USAGE, EXIT_STORAGE = 0, 1, 2, 3


def _storage_options() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data-file", default=DEFAULT_DATA_FILE,
                        help=f"файл истории (по умолчанию {DEFAULT_DATA_FILE})")
    common.add_argument("--backup-dir", default=DEFAULT_BACKUP_DIR,
                        help=f"каталог копий (по умолчанию {DEFAULT_BACKUP_DIR})")
    common.add_argument("--keep", type=int, default=DEFAULT_KEEP,
                        help=f"число хранимых копий (по умолчанию {DEFAULT_KEEP})")
    return common


def build_parser() -> argparse.ArgumentParser:
    common = _storage_options()
    parser = argparse.ArgumentParser(
        prog="perfect_numbers",
        description="Поиск совершенных чисел в диапазоне и резервное копирование истории сканирований.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    find = sub.add_parser("find", parents=[common], help="найти совершенные числа в диапазоне")
    find.add_argument("-i", "--input", help="входной файл (TXT, CSV или JSON)")
    find.add_argument("-s", "--start", type=int, help="начало диапазона")
    find.add_argument("-e", "--end", type=int, help="конец диапазона")
    find.add_argument("-o", "--output", help="выходной файл (.json — JSON, иначе текст)")
    find.add_argument("--save", action="store_true", help="сохранить результат в историю")

    hist = sub.add_parser("history", parents=[common], help="показать историю сканирований")
    hist.add_argument("--limit", type=int, default=0, help="показать последние N записей")

    sub.add_parser("backup", parents=[common], help="создать резервную копию истории")
    sub.add_parser("list-backups", parents=[common], help="список копий с проверкой целостности")
    sub.add_parser("verify", parents=[common], help="проверить целостность всех копий")
    rest = sub.add_parser("restore", parents=[common], help="восстановить историю из копии")
    rest.add_argument("--file", help="файл копии (по умолчанию — самая свежая)")
    return parser


def _manager(args) -> HistoryManager:
    return HistoryManager(args.data_file, args.backup_dir, args.keep)


def _cmd_find(args) -> int:
    if args.input and (args.start is not None or args.end is not None):
        raise InputError("Укажите либо --input, либо --start/--end, но не одновременно.")
    if args.input:
        start, end = read_range_file(args.input)
    elif args.start is not None or args.end is not None:
        if args.start is None or args.end is None:
            raise InputError("Для --start/--end необходимо указать обе границы.")
        start, end = args.start, args.end
    else:
        start, end = read_range_console()
    validate_range(start, end)

    began = time.perf_counter()
    result = analyze(start, end)
    elapsed = time.perf_counter() - began

    print(format_result(result))
    if args.output:
        write_result_file(args.output, result)
        print(f"Результат записан в {args.output}")
    if args.save:
        record = _manager(args).add_record(result, elapsed)
        print(f"Запись №{record['id']} сохранена в {args.data_file}")
    return EXIT_OK


def _cmd_history(args) -> int:
    records = _manager(args).load_history()
    if not records:
        print("История пуста.")
        return EXIT_OK
    if args.limit > 0:
        records = records[-args.limit:]
    for r in records:
        nums = ", ".join(map(str, r["numbers"])) or "—"
        print(f"#{r['id']} {r['timestamp']} [{r['start']}; {r['end']}] "
              f"найдено: {r['count']} ({nums}), {r['elapsed']} с")
    return EXIT_OK


def _cmd_backup(args) -> int:
    path = _manager(args).create_backup()
    print(f"Копия создана: {path}")
    return EXIT_OK


def _cmd_list(args) -> int:
    items = _manager(args).list_backups()
    if not items:
        print("Резервные копии отсутствуют.")
        return EXIT_OK
    for item in items:
        if item["ok"]:
            print(f"OK       {item['path']}  записей: {item['records']}  создана: {item['created_at']}")
        else:
            print(f"ПОВРЕЖДЕНА {item['path']}  ({item['error']})")
    return EXIT_OK


def _cmd_verify(args) -> int:
    items = _manager(args).verify_all()
    if not items:
        print("Резервные копии отсутствуют.")
        return EXIT_OK
    bad = [i for i in items if not i["ok"]]
    for item in items:
        print(("OK        " if item["ok"] else "ПОВРЕЖДЕНА ") + str(item["path"]))
    print(f"Проверено копий: {len(items)}, повреждено: {len(bad)}")
    return EXIT_STORAGE if bad else EXIT_OK


def _cmd_restore(args) -> int:
    path = _manager(args).restore(args.file)
    print(f"История восстановлена из {path}")
    return EXIT_OK


_COMMANDS = {
    "find": _cmd_find, "history": _cmd_history, "backup": _cmd_backup,
    "list-backups": _cmd_list, "verify": _cmd_verify, "restore": _cmd_restore,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse: --help → 0, ошибка аргументов → 2
        return int(exc.code or 0)
    try:
        return _COMMANDS[args.command](args)
    except (InputError, RangeError) as err:
        print(f"Ошибка: {err}", file=sys.stderr)
        return EXIT_DATA
    except StorageError as err:  # включает BackupError
        print(f"Ошибка хранилища: {err}", file=sys.stderr)
        return EXIT_STORAGE
