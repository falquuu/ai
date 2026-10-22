import datetime as real_datetime
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from perfect_numbers.backup import BackupError, HistoryManager, StorageError

RESULT_A = {"start": 1, "end": 100, "count": 2, "numbers": [6, 28]}
RESULT_B = {"start": 1, "end": 10000, "count": 4, "numbers": [6, 28, 496, 8128]}


class BackupTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.manager = HistoryManager(self.dir / "data" / "history.json", self.dir / "backups", keep=3)

    def tearDown(self):
        self._tmp.cleanup()


class TestStorage(BackupTestCase):
    def test_empty_history_when_no_file(self):
        self.assertEqual(self.manager.load_history(), [])

    def test_add_record_increments_id(self):
        r1 = self.manager.add_record(RESULT_A, 0.01)
        r2 = self.manager.add_record(RESULT_B, 0.02)
        self.assertEqual((r1["id"], r2["id"]), (1, 2))
        self.assertEqual(len(self.manager.load_history()), 2)

    def test_corrupt_history_raises(self):
        self.manager.data_file.parent.mkdir(parents=True)
        self.manager.data_file.write_text("{не json", encoding="utf-8")
        with self.assertRaises(StorageError):
            self.manager.load_history()

    def test_wrong_structure_raises(self):
        self.manager.data_file.parent.mkdir(parents=True)
        self.manager.data_file.write_text('{"version": 1, "records": [{"id": 1}]}', encoding="utf-8")
        with self.assertRaises(StorageError):
            self.manager.load_history()

    def test_no_temp_files_left(self):
        self.manager.add_record(RESULT_A)
        names = [p.name for p in self.manager.data_file.parent.iterdir()]
        self.assertEqual(names, ["history.json"])

    def test_invalid_keep(self):
        with self.assertRaises(BackupError):
            HistoryManager(keep=0)


class TestBackup(BackupTestCase):
    def test_create_backup_and_manifest(self):
        self.manager.add_record(RESULT_A)
        backup = self.manager.create_backup()
        manifest = json.loads(self.manager.manifest_path(backup).read_text(encoding="utf-8"))
        self.assertEqual(manifest["records"], 1)
        self.assertEqual(len(manifest["sha256"]), 64)
        self.assertEqual(self.manager.verify_backup(backup)["records"], 1)

    def test_backup_without_storage_fails(self):
        with self.assertRaises(BackupError):
            self.manager.create_backup()

    def test_corrupt_storage_is_not_backed_up(self):
        self.manager.data_file.parent.mkdir(parents=True)
        self.manager.data_file.write_text("мусор", encoding="utf-8")
        with self.assertRaises(BackupError):
            self.manager.create_backup()
        self.assertEqual(self.manager.list_backups(), [])

    def test_rotation_keeps_last_n(self):
        self.manager.add_record(RESULT_A)
        created = [self.manager.create_backup() for _ in range(5)]
        files = sorted(self.manager.backup_dir.glob("history_*.json"))
        self.assertEqual(files, created[-3:])
        self.assertEqual(len(list(self.manager.backup_dir.glob("*.manifest"))), 3)

    def test_list_backups_newest_first(self):
        self.manager.add_record(RESULT_A)
        first, second = self.manager.create_backup(), self.manager.create_backup()
        self.assertEqual([i["path"] for i in self.manager.list_backups()], [second, first])

    def test_verify_detects_modified_backup(self):
        self.manager.add_record(RESULT_A)
        backup = self.manager.create_backup()
        backup.write_text(backup.read_text(encoding="utf-8").replace("28", "29"), encoding="utf-8")
        with self.assertRaises(BackupError):
            self.manager.verify_backup(backup)
        self.assertFalse(self.manager.list_backups()[0]["ok"])

    def test_verify_detects_missing_manifest(self):
        self.manager.add_record(RESULT_A)
        backup = self.manager.create_backup()
        self.manager.manifest_path(backup).unlink()
        with self.assertRaises(BackupError):
            self.manager.verify_backup(backup)

    def test_verify_missing_backup(self):
        with self.assertRaises(BackupError):
            self.manager.verify_backup(self.dir / "none.json")


class TestCoarseClock(BackupTestCase):
    """Windows: системные часы с шагом ≈15 мс — имена копий не должны совпадать."""

    def test_backup_names_unique_with_frozen_clock(self):
        frozen = real_datetime.datetime(2026, 10, 21, 12, 0, 0)

        class FrozenDatetime(real_datetime.datetime):
            @classmethod
            def now(cls, tz=None):
                return frozen

        self.manager.add_record(RESULT_A)
        with mock.patch("perfect_numbers.backup.datetime", FrozenDatetime):
            first = self.manager.create_backup()
            second = self.manager.create_backup()
            third = self.manager.create_backup()
        self.assertEqual(len({first, second, third}), 3)
        self.assertEqual(sorted([first, second, third]), [first, second, third])
        self.assertEqual([i["path"] for i in self.manager.list_backups()], [third, second, first])


class TestRestore(BackupTestCase):
    def test_save_backup_modify_restore_cycle(self):
        self.manager.add_record(RESULT_A)
        self.manager.create_backup()
        self.manager.add_record(RESULT_B)
        self.assertEqual(len(self.manager.load_history()), 2)
        self.manager.restore()
        records = self.manager.load_history()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["end"], 100)

    def test_restore_saves_current_state_first(self):
        self.manager.add_record(RESULT_A)
        self.manager.create_backup()
        self.manager.add_record(RESULT_B)
        self.manager.restore()
        newest = self.manager.list_backups()[0]
        self.assertEqual(newest["records"], 2)  # состояние до восстановления сохранено

    def test_restore_specific_file(self):
        self.manager.add_record(RESULT_A)
        old = self.manager.create_backup()
        self.manager.add_record(RESULT_B)
        self.manager.create_backup()
        self.manager.restore(old)
        self.assertEqual(len(self.manager.load_history()), 1)

    def test_corrupt_backup_rejected_storage_untouched(self):
        self.manager.add_record(RESULT_A)
        backup = self.manager.create_backup()
        self.manager.add_record(RESULT_B)
        before = self.manager.data_file.read_bytes()
        backup.write_text("испорчено", encoding="utf-8")
        with self.assertRaises(BackupError):
            self.manager.restore(backup)
        self.assertEqual(self.manager.data_file.read_bytes(), before)

    def test_restore_without_backups(self):
        with self.assertRaises(BackupError):
            self.manager.restore()

    def test_restore_into_missing_storage(self):
        self.manager.add_record(RESULT_A)
        backup = self.manager.create_backup()
        self.manager.data_file.unlink()
        self.manager.restore(backup)
        self.assertEqual(len(self.manager.load_history()), 1)

    def test_restore_over_corrupt_storage_keeps_corrupt_copy(self):
        self.manager.add_record(RESULT_A)
        backup = self.manager.create_backup()
        self.manager.data_file.write_text("битый файл", encoding="utf-8")
        self.manager.restore(backup)
        self.assertEqual(len(self.manager.load_history()), 1)
        self.assertEqual(len(list(self.manager.data_file.parent.glob("*.corrupt-*"))), 1)


if __name__ == "__main__":
    unittest.main()
