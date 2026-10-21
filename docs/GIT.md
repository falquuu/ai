# Правила ведения репозитория

## 1. Ветки

| Ветка | Назначение |
|---|---|
| `main` | Стабильная версия; каждое состояние можно выпускать |
| `develop` | Интеграция новых функций |
| `feature/<кратко>` | Новая функциональность (например, `feature/csv-export`) |
| `fix/<кратко>` | Исправление ошибки |
| `docs/<кратко>` | Изменения документации |

Прямые коммиты в `main` запрещены — только через Pull Request с зелёным CI.

## 2. Сообщения коммитов (Conventional Commits)

```
<тип>(<область>): <краткое описание в повелительном наклонении>
```

Типы: `feat` — функция, `fix` — исправление, `docs` — документация, `test` — тесты, `ci` — автоматизация, `refactor` — рефакторинг, `chore` — служебное.

Примеры:

```
feat(core): add segmented divisor-sum sieve for perfect numbers
feat(backup): add SHA-256 manifest and rotation
docs(tz): add detailed requirements section
test(cli): cover restore of corrupted backup
```

## 3. Версионирование

Семантическое версионирование `MAJOR.MINOR.PATCH`; релиз отмечается аннотированным тегом `vX.Y.Z` и GitHub Release.

```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

## 4. Что хранится в репозитории

| Хранить | Не хранить (`.gitignore`) |
|---|---|
| `src/`, `tests/`, `docs/`, `examples/` | `data/`, `backups/` — пользовательские данные |
| `README.md`, `README.en.md`, `pyproject.toml`, `requirements.txt` | `__pycache__/`, `.pytest_cache/`, `*.egg-info/`, `.venv/` |
| `.github/workflows/` | Секреты, локальные настройки IDE |

## 5. Рабочий цикл

```bash
git switch develop
git pull
git switch -c feature/my-change
# ... правки, тесты: python -m unittest discover -s tests
git add -A
git commit -m "feat(core): ..."
git push -u origin feature/my-change
# Pull Request → ревью → зелёный CI → слияние в develop
```

## 6. Pull Request: чек-лист

- [ ] Тесты проходят локально и в CI
- [ ] Добавлены/обновлены тесты для изменений
- [ ] Обновлены README (ru/en), ТЗ и `docs/test-cases.md`, если менялось поведение
- [ ] Сообщения коммитов соответствуют правилам

## 7. Первичная публикация

```bash
git remote add origin https://github.com/<ваш-логин>/perfect-numbers-tool.git
git push -u origin main
git push origin develop
git push origin --tags
```

## 8. CI

`.github/workflows/tests.yml` запускает тесты на Ubuntu, Windows и macOS для Python 3.10–3.13 при каждом push и Pull Request.
