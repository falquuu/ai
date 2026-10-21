"""История сканирований числовой оси: хранилище, резервное копирование, восстановление.

Файл истории (по умолчанию data/history.json):
    {"version": 1, "records": [{"id", "timestamp", "start", "end",
                                "count", "numbers", "elapsed"}, ...]}

Резервная копия: backups/history_<дата>_<время>.json + манифест
history_<дата>_<время>.json.manifest (SHA-256, число записей, дата создания).
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

HISTORY_VERSION = 1
DEFAULT_DATA_FILE = "data/history.json"
DEFAULT_BACKUP_DIR = "backups"
DEFAULT_KEEP = 10
_RECORD_FIELDS = {"id", "timestamp", "start", "end", "count", "numbers", "elapsed"}


class StorageError(Exception):
    """Ошибка хранилища истории."""


class BackupError(StorageError):
    """Ошибка резервного копирования или восстановления."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Атомарная запись: временный файл в том же каталоге → os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def parse_history(raw: bytes) -> list[dict]:
    """Разбор и проверка структуры истории; при ошибке — StorageError."""
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise StorageError(f"Файл истории повреждён: {err}") from err
    if not isinstance(data, dict) or data.get("version") != HISTORY_VERSION:
        raise StorageError("Неверная структура или версия файла истории.")
    records = data.get("records")
    if not isinstance(records, list):
        raise StorageError('В файле истории отсутствует список "records".')
    for index, rec in enumerate(records, start=1):
        if not isinstance(rec, dict) or not _RECORD_FIELDS <= rec.keys():
            raise StorageError(f"Запись №{index} имеет неверный формат.")
    return records


def dump_history(records: list[dict]) -> bytes:
    payload = {"version": HISTORY_VERSION, "records": records}
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


class HistoryManager:
    """Хранилище истории сканирований с резервным копированием и восстановлением."""

    def __init__(
        self,
        data_file: str | Path = DEFAULT_DATA_FILE,
        backup_dir: str | Path = DEFAULT_BACKUP_DIR,
        keep: int = DEFAULT_KEEP,
    ):
        if keep < 1:
            raise BackupError("Число хранимых копий должно быть не меньше 1.")
        self.data_file = Path(data_file)
        self.backup_dir = Path(backup_dir)
        self.keep = keep

    # ---------- хранилище ----------
    def load_history(self) -> list[dict]:
        """Читает историю; если файла нет — пустая история."""
        try:
            raw = self.data_file.read_bytes()
        except FileNotFoundError:
            return []
        except OSError as err:
            raise StorageError(f"Не удалось прочитать {self.data_file}: {err}") from err
        return parse_history(raw)

    def save_history(self, records: list[dict]) -> None:
        try:
            atomic_write_bytes(self.data_file, dump_history(records))
        except OSError as err:
            raise StorageError(f"Не удалось записать {self.data_file}: {err}") from err

    def add_record(self, result: dict, elapsed: float = 0.0) -> dict:
        """Добавляет результат сканирования в историю и возвращает запись."""
        records = self.load_history()
        record = {
            "id": max((r["id"] for r in records), default=0) + 1,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "start": result["start"],
            "end": result["end"],
            "count": result["count"],
            "numbers": list(result["numbers"]),
            "elapsed": round(float(elapsed), 4),
        }
        records.append(record)
        self.save_history(records)
        return record

    # ---------- резервное копирование ----------
    @staticmethod
    def manifest_path(backup: Path) -> Path:
        return backup.with_name(backup.name + ".manifest")

    def create_backup(self) -> Path:
        """Создаёт копию истории с манифестом и выполняет ротацию."""
        try:
            raw = self.data_file.read_bytes()
        except FileNotFoundError:
            raise BackupError(f"Хранилище истории не найдено: {self.data_file}") from None
        except OSError as err:
            raise BackupError(f"Не удалось прочитать {self.data_file}: {err}") from err
        try:
            records = parse_history(raw)  # повреждённые данные не копируются
        except StorageError as err:
            raise BackupError(f"Копия не создана: {err}") from err

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup = self.backup_dir / f"history_{stamp}.json"
        manifest = {
            "file": backup.name,
            "sha256": sha256_bytes(raw),
            "records": len(records),
            "size": len(raw),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        try:
            atomic_write_bytes(backup, raw)
            atomic_write_bytes(
                self.manifest_path(backup),
                (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
            )
        except OSError as err:
            raise BackupError(f"Не удалось записать копию: {err}") from err
        self._rotate()
        return backup

    def _backup_files(self) -> list[Path]:
        if not self.backup_dir.is_dir():
            return []
        return sorted(self.backup_dir.glob("history_*.json"))  # имя содержит время → по возрастанию

    def _rotate(self) -> None:
        files = self._backup_files()
        for old in files[: max(0, len(files) - self.keep)]:
            for path in (old, self.manifest_path(old)):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass

    def verify_backup(self, path: str | Path) -> dict:
        """Проверяет целостность копии; возвращает манифест или бросает BackupError."""
        backup = Path(path)
        manifest_file = self.manifest_path(backup)
        try:
            raw = backup.read_bytes()
        except FileNotFoundError:
            raise BackupError(f"Копия не найдена: {backup}") from None
        except OSError as err:
            raise BackupError(f"Не удалось прочитать копию {backup}: {err}") from err
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            expected = manifest["sha256"]
            expected_records = manifest["records"]
        except FileNotFoundError:
            raise BackupError(f"Манифест копии не найден: {manifest_file.name}") from None
        except (OSError, ValueError, KeyError, TypeError) as err:
            raise BackupError(f"Манифест копии повреждён: {err}") from err
        if sha256_bytes(raw) != expected:
            raise BackupError(f"Контрольная сумма не совпадает: {backup.name}")
        try:
            records = parse_history(raw)
        except StorageError as err:
            raise BackupError(f"Содержимое копии некорректно: {err}") from err
        if len(records) != expected_records:
            raise BackupError(f"Число записей не совпадает с манифестом: {backup.name}")
        return manifest

    def list_backups(self) -> list[dict]:
        """Список копий (новые первыми) с результатом проверки целостности."""
        items = []
        for path in reversed(self._backup_files()):
            try:
                manifest = self.verify_backup(path)
                items.append({"path": path, "ok": True, "records": manifest["records"],
                              "created_at": manifest["created_at"], "error": None})
            except BackupError as err:
                items.append({"path": path, "ok": False, "records": None,
                              "created_at": None, "error": str(err)})
        return items

    def verify_all(self) -> list[dict]:
        return self.list_backups()

    # ---------- восстановление ----------
    def restore(self, path: str | Path | None = None) -> Path:
        """Восстанавливает историю из копии (по умолчанию — из самой свежей).

        Порядок: проверка копии → сохранение текущего состояния отдельной копией →
        атомарная замена файла истории. Повреждённая копия отклоняется,
        текущее хранилище остаётся нетронутым.
        """
        if path is None:
            files = self._backup_files()
            if not files:
                raise BackupError(f"Резервные копии не найдены в «{self.backup_dir}».")
            backup = files[-1]
        else:
            backup = Path(path)
        self.verify_backup(backup)  # BackupError → хранилище не изменяется
        raw = backup.read_bytes()

        if self.data_file.exists():  # сохраняем текущее состояние
            try:
                self.create_backup()
            except BackupError:
                # текущая история повреждена — сохраняем «как есть» рядом с хранилищем
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                saved = self.data_file.with_name(f"{self.data_file.name}.corrupt-{stamp}")
                try:
                    atomic_write_bytes(saved, self.data_file.read_bytes())
                except OSError as err:
                    raise BackupError(f"Не удалось сохранить текущее состояние: {err}") from err
        try:
            atomic_write_bytes(self.data_file, raw)
        except OSError as err:
            raise BackupError(f"Не удалось восстановить историю: {err}") from err
        return backup
