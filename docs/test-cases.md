# Тест-кейсы и результаты проверки

Документ подтверждает соответствие `perfect-numbers-tool` техническому заданию ([TZ.md](TZ.md)).
Проверка выполнена 21.10.2026, Python 3.12.3, Linux (1 ядро ЦП).

## 1. Итог

| Показатель | Значение |
|---|---|
| Автоматических тестов | **67** (`test_core` — 12, `test_io` — 16, `test_backup` — 21, `test_cli` — 18) |
| Результат `python -m unittest discover -s tests` | **OK, 67 из 67** |
| Тест-кейсов (TC) | 41 |
| Пройдено | 41 |
| Не пройдено | 0 |
| Покрытие D-требований | 100 % (каждое D-требование имеет ≥ 1 тест-кейс, см. приложение В ТЗ) |

Запуск:

```bash
python -m unittest discover -s tests -v
# или
python -m pytest -v
```

## 2. Тест-кейсы

Обозначения: **Авто** — автоматический тест (`файл::имя`), **Ручн.** — выполнено вручную в консоли.

### 2.1 Ввод данных и расчёт

| TC | Назв. | Предусловия / шаги | Ожидаемый результат | Тип / тест | Требования | Статус |
|---|---|---|---|---|---|---|
| TC-01 | Ввод из TXT | `find -i examples/range_small.txt` (файл: `1 100`) | «Найдено совершенных чисел: 2», «Числа: 6, 28», код 0 | Авто `test_cli::test_find_from_each_file_format`; Ручн. | D-IN-2, D-IN-5, D-CALC-1, D-OUT-1 | ✅ Пройден |
| TC-02 | Ввод из CSV с заголовком | `find -i examples/range.csv` (`start,end` / `1,10000`) | 4 числа: 6, 28, 496, 8128 | Авто `test_cli::test_find_from_each_file_format`; Ручн. | D-IN-5, D-CALC-5 | ✅ Пройден |
| TC-03 | Ввод из JSON | `find -i examples/range.json` | 6, 28, … код 0 | Авто `test_cli::test_find_from_each_file_format`, `test_io::test_json_formats` | D-IN-6 | ✅ Пройден |
| TC-04 | Ввод из консоли | `find`, ввести `1` и `100` | Числа 6, 28 | Авто `test_cli::test_find_from_console`; Ручн. | D-IN-1 | ✅ Пройден |
| TC-05 | Ввод аргументами | `find -s 1 -e 10000` | 6, 28, 496, 8128 | Авто `test_cli::test_find_with_arguments` | D-IN-3 | ✅ Пройден |
| TC-06 | Пятое совершенное число | `find -i examples/range_mersenne.txt` (`33550000 33551000`) | Число 33550336 | Авто `test_core::test_fifth_perfect_number`; Ручн. | D-CALC-1, D-CALC-5 | ✅ Пройден |
| TC-07 | Нет совершенных чисел | диапазон 29…495 | Список пуст, вывод «Числа: —» | Авто `test_core::test_no_perfect_in_range`, `test_io::test_format_result_empty` | D-CALC-3, D-OUT-1 | ✅ Пройден |
| TC-08 | Граничные значения | 6…6 → [6]; 27…27 → []; 1…5 → []; 6…28 → [6, 28] | Границы включены, 1 не совершенное | Авто `test_core::test_single_number_range`, `test_one_is_not_perfect`, `test_boundaries_inclusive` | D-CALC-1, D-CALC-3 | ✅ Пройден |
| TC-09 | Конец меньше начала | `find -i examples/range_invalid.txt` (`100 1`) | «Ошибка: Конец диапазона не может быть меньше начала.» в stderr, код 1 | Авто `test_cli::test_invalid_range_exit_1`; Ручн. | D-CALC-2, D-OUT-3, D-CLI-3 | ✅ Пройден |
| TC-10 | Начало < 1 | `find -s 0 -e 10` | «Ошибка: Начало диапазона должно быть не меньше 1.», код 1 | Авто `test_core::test_invalid_ranges`; Ручн. | D-CALC-2 | ✅ Пройден |
| TC-11 | Слишком длинный диапазон / слишком большой конец | `find -s 1 -e 6000000`; конец = 10¹² + 1 | «Ошибка: Длина диапазона не должна превышать 5000000 чисел (задано 6000000).», код 1 | Авто `test_core::test_invalid_ranges`; Ручн. | D-CALC-2 | ✅ Пройден |
| TC-12 | Файл не найден | `find -i examples/nope.txt` | «Ошибка: Файл не найден: …», код 1 | Авто `test_cli::test_missing_file_exit_1`, `test_io::test_missing_file`; Ручн. | D-IN-2, D-IN-7 | ✅ Пройден |
| TC-13 | Нечисловое значение в файле | файл `1 2\n3 abc` | Ошибка с указанием «Строка 2» | Авто `test_io::test_text_not_integer_has_line_number` | D-IN-7, D-IN-8 | ✅ Пройден |
| TC-14 | Неверные аргументы | `find -s abc -e 5`; неизвестная команда; запуск без команды | Сообщение `argparse`, код 2 | Авто `test_cli::test_bad_arguments_exit_2`; Ручн. | D-CLI-1, D-CLI-3 | ✅ Пройден |
| TC-15 | Вывод в файл | `find -s 1 -e 100 -o r.txt` и `-o r.json` | `.txt` — текст, `.json` — `{start,end,count,numbers}`; каталоги создаются | Авто `test_cli::test_find_output_files`, `test_io::test_write_result_text_and_json`; Ручн. | D-OUT-2 | ✅ Пройден |

### 2.2 История и резервное копирование

| TC | Назв. | Предусловия / шаги | Ожидаемый результат | Тип / тест | Требования | Статус |
|---|---|---|---|---|---|---|
| TC-16 | Сохранение в историю | `find -s 1 -e 100 --save`, затем `history` | «Запись №1 сохранена…»; в истории `[1; 100]`; id растёт | Авто `test_cli::test_save_and_history`, `test_backup::test_add_record_increments_id`; Ручн. | D-HIST-1, D-HIST-2 | ✅ Пройден |
| TC-17 | Создание копии | История из одной записи → `backup` | Файл `history_<…>.json` + `.manifest` (SHA-256 из 64 символов, `records: 1`) | Авто `test_backup::test_create_backup_and_manifest`; Ручн. | D-BKP-1, D-BKP-2 | ✅ Пройден |
| TC-18 | Копия без хранилища | `backup` при отсутствии `history.json` | «Ошибка хранилища: Хранилище истории не найдено…», код 3 | Авто `test_backup::test_backup_without_storage_fails`, `test_cli::test_backup_without_storage_exit_3`; Ручн. | D-BKP-3, D-CLI-3 | ✅ Пройден |
| TC-19 | Копия повреждённого хранилища | `history.json` = «мусор» → `backup` | Ошибка, копия не создаётся | Авто `test_backup::test_corrupt_storage_is_not_backed_up` | D-BKP-3, D-NF-R3 | ✅ Пройден |
| TC-20 | Список копий | `backup` → `list-backups` | Строка «OK … записей: N … создана: …», код 0 | Авто `test_cli::test_list_and_verify`, `test_backup::test_list_backups_newest_first`; Ручн. | D-BKP-6 | ✅ Пройден |
| TC-21 | Проверка повреждённой копии | испортить файл копии → `verify` | «ПОВРЕЖДЕНА …», «повреждено: 1», код 3 | Авто `test_cli::test_verify_corrupt_exit_3`, `test_backup::test_verify_detects_modified_backup`; Ручн. | D-BKP-6, D-NF-R2 | ✅ Пройден |
| TC-22 | Цикл «сохранить → копия → изменить → восстановить» | `find … --save`; `backup`; `find …10000 --save`; `restore`; `history` | После `restore` в истории одна запись `[1; 100]` | Авто `test_cli::test_full_cycle_save_backup_change_restore`, `test_backup::test_save_backup_modify_restore_cycle`; Ручн. | D-RST-1, D-RST-4 | ✅ Пройден |
| TC-23 | Восстановление из указанной копии | `restore --file <старая копия>` | История соответствует выбранной копии | Авто `test_backup::test_restore_specific_file` | D-RST-1 | ✅ Пройден |
| TC-24 | Отказ при повреждённой копии | испортить копию → `restore --file` | «Ошибка хранилища: Контрольная сумма не совпадает…», код 3; `history.json` не изменился (побайтово) | Авто `test_backup::test_corrupt_backup_rejected_storage_untouched`, `test_cli::test_restore_corrupt_file_exit_3`; Ручн. | D-RST-2, D-NF-R3 | ✅ Пройден |
| TC-25 | Сохранение состояния «до» | `restore` при изменённой истории | Появляется новая копия с состоянием до восстановления (2 записи) | Авто `test_backup::test_restore_saves_current_state_first`; Ручн. | D-RST-3, D-NF-R5 | ✅ Пройден |
| TC-26 | Ротация | `keep=3`, создано 5 копий | Остаются 3 последние копии и 3 манифеста | Авто `test_backup::test_rotation_keeps_last_n`, `test_backup::test_invalid_keep` | D-BKP-4, D-CLI-2 | ✅ Пройден |
| TC-27 | Атомарность | после записи истории проверить каталог | Нет `*.tmp`-файлов, только `history.json` | Авто `test_backup::test_no_temp_files_left` | D-HIST-4, D-BKP-5 | ✅ Пройден |
| TC-28 | Производительность | `find -i examples/range_million.txt` | ≤ 10 с (получено 1,13 с); `[1; 5·10⁶]` — 6,2 с; ОЗУ 47 МБ | Ручн. | D-NF-P1…P3 | ✅ Пройден |
| TC-29 | Конфликт источников | `find -i file.csv -s 1 -e 5` | Ошибка, код 1 | Авто `test_cli::test_conflicting_sources_exit_1` | D-IN-4 | ✅ Пройден |
| TC-30 | Нет копий | `restore` без каталога копий | «Ошибка хранилища: Резервные копии не найдены…», код 3 | Авто `test_backup::test_restore_without_backups`, `test_cli::test_restore_without_backups_exit_3` | D-RST-5 | ✅ Пройден |
| TC-31 | Повреждённая история при `--save` | `history.json` = «мусор» → `find … --save` | Ошибка хранилища, код 3 | Авто `test_cli::test_save_into_corrupt_storage_exit_3`, `test_backup::test_corrupt_history_raises`, `test_wrong_structure_raises` | D-HIST-3 | ✅ Пройден |
| TC-32 | Сверка алгоритма | сравнить решето с перебором для диапазонов (2…50), (7…7), (500…9000), (1000…1999) | Результаты совпадают | Авто `test_core::test_range_not_starting_from_one_matches_bruteforce`, `test_divisor_sum` | D-CALC-4 | ✅ Пройден |
| TC-33 | Восстановление поверх повреждённого файла | `history.json` = «битый файл» → `restore --file` | История восстановлена; испорченный файл сохранён как `history.json.corrupt-<время>` | Авто `test_backup::test_restore_over_corrupt_storage_keeps_corrupt_copy`, `test_restore_into_missing_storage` | D-RST-3 | ✅ Пройден |
| TC-34 | Нет манифеста | удалить `.manifest` → `verify_backup` | Ошибка «Манифест копии не найден» | Авто `test_backup::test_verify_detects_missing_manifest`, `test_verify_missing_backup` | D-BKP-6, D-NF-R2 | ✅ Пройден |

### 2.3 Дополнительные проверки ввода

| TC | Назв. | Шаги | Ожидаемый результат | Тип / тест | Требования | Статус |
|---|---|---|---|---|---|---|
| TC-35 | Разделители, BOM, комментарии | `1 100`, `1,100`, `1;100`, `1⇥100`, `1⏎100`, файл с BOM, строки `#…` | Везде диапазон (1, 100) | Авто `test_io::test_text_separators`, `test_text_header_comments_blank_lines`, `test_read_with_bom` | D-IN-5 | ✅ Пройден |
| TC-36 | Повтор и исчерпание попыток в консоли | ввод `abc`, затем `1`; ввод `x` каждый раз | Повторный запрос; после лимита — ошибка | Авто `test_io::test_console_retry_after_bad_input`, `test_console_attempts_exceeded` | D-IN-1 | ✅ Пройден |
| TC-37 | Неподдерживаемое расширение | `find -i data.xml` | Ошибка «Неподдерживаемый формат», код 1 | Авто `test_io::test_unsupported_extension` | D-IN-2 | ✅ Пройден |
| TC-38 | Одна граница | `find -s 1` | Ошибка, код 1 | Авто `test_cli::test_only_one_bound_exit_1` | D-IN-3 | ✅ Пройден |
| TC-39 | Некорректный JSON | `{bad`, `{"start": 1}`, `[1]`, `"x"` | Ошибка `InputError` во всех случаях | Авто `test_io::test_json_errors`, `test_json_formats` | D-IN-6 | ✅ Пройден |
| TC-40 | Нецелые значения | `1.5 10`; границы `1.5`, `"10"`, `True` | Отклоняются | Авто `test_io::test_float_rejected`, `test_core::test_non_integer_bounds` | D-IN-8 | ✅ Пройден |
| TC-41 | Пустая история | `history` без файла | «История пуста.», код 0 | Авто `test_cli::test_history_empty`, `test_backup::test_empty_history_when_no_file` | D-HIST-2 | ✅ Пройден |

## 3. Протокол ручной проверки (фрагменты вывода)

```text
$ python -m perfect_numbers find -i examples/range_small.txt
Диапазон: 1 – 100
Найдено совершенных чисел: 2
Числа: 6, 28
[код возврата: 0]

$ python -m perfect_numbers find -i examples/range_invalid.txt
Ошибка: Конец диапазона не может быть меньше начала.
[код возврата: 1]

$ python -m perfect_numbers find -s 1 -e 6000000
Ошибка: Длина диапазона не должна превышать 5000000 чисел (задано 6000000).
[код возврата: 1]

$ python -m perfect_numbers find -s 1 -e 100 --save
Запись №1 сохранена в data/history.json
$ python -m perfect_numbers backup
Копия создана: backups/history_20261021_022708_491394.json
$ python -m perfect_numbers find -s 1 -e 10000 --save
Запись №2 сохранена в data/history.json
$ python -m perfect_numbers restore
История восстановлена из backups/history_20261021_022708_491394.json
$ python -m perfect_numbers history
#1 2026-10-21T02:27:08 [1; 100] найдено: 2 (6, 28), 0.0 с

$ python -m perfect_numbers verify          # одна копия намеренно испорчена
OK         backups/history_20261021_022708_681669.json
ПОВРЕЖДЕНА backups/history_20261021_022708_491394.json
Проверено копий: 2, повреждено: 1
[код возврата: 3]

$ python -m perfect_numbers restore --file backups/history_20261021_022708_491394.json
Ошибка хранилища: Контрольная сумма не совпадает: history_20261021_022708_491394.json
[код возврата: 3]
```

Производительность (1 ядро):

| Диапазон | Время | Пик ОЗУ |
|---|---|---|
| 1 … 10 000 | 0,013 с | — |
| 1 … 1 000 000 | 1,13 с | — |
| 1 … 5 000 000 | 6,2 с | 47 МБ |
| 10¹² − 4 999 999 … 10¹² (худший случай) | 20,8 с | — |

## 4. Заключение

Все 41 тест-кейс пройдены, 67 автоматических тестов завершились успешно. Ключевые модули (`core`, `io_handlers`, `backup`, `cli`) соответствуют техническому заданию; замечаний и отклонений нет.

Ограничение проверки: тесты выполнялись на Linux; для Windows и macOS проверка запускается автоматически через GitHub Actions (`.github/workflows/tests.yml`, матрица ОС и версий Python).
