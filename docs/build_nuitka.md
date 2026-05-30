# Standalone-сборка через Nuitka

Shardveil можно собрать в standalone-версию через Nuitka. Сборка создаёт папку с executable, Python runtime, native-зависимостями и игровыми assets.

Nuitka-сборки платформозависимы: Windows-билд - на Windows, macOS-билд собирается на macOS, Linux-билд - на Linux.

Платформенные форматы иконки приложения лежат в `packaging/icons/`.

## Подготовка окружения

Создайте виртуальное окружение и установите зависимости проекта:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r requirements-build.txt
```

Build-скрипты не устанавливают зависимости автоматически. Перед сборкой они проверяют `.venv`, Nuitka и runtime-пакеты `arcade`, `pyglet`, `tcod`, `numpy`.

По умолчанию скрипты выставляют `NUITKA_CACHE_DIR=.nuitka-cache/`, чтобы кэш Nuitka оставался внутри рабочей папки проекта.

## macOS и Linux

Запуск из корня репозитория:

```bash
scripts/build_nuitka_unix.sh
```

Скрипт использует команду:

```bash
.venv/bin/python -m nuitka src/main.py \
  --standalone \
  --include-data-dir=assets=assets \
  --output-dir=build/nuitka \
  --output-filename=shardveil \
  --output-folder-name=Shardveil
```

На macOS скрипт дополнительно создаёт `Shardveil.app` bundle и добавляет `packaging/icons/shardveil.icns`.

Ожидаемый результат:

- build-артефакты: `build/nuitka/Shardveil.build/`
- Linux standalone-папка: `build/nuitka/Shardveil.dist/`
- Linux executable: `build/nuitka/Shardveil.dist/shardveil`
- macOS app bundle: `build/nuitka/Shardveil.app/`

Запуск собранной игры на Linux:

```bash
build/nuitka/Shardveil.dist/shardveil
```

Запуск собранной игры на macOS:

```bash
open build/nuitka/Shardveil.app
```

## Windows

Подготовка окружения в PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
```

Запуск из корня репозитория:

```powershell
scripts\build_nuitka_windows.ps1
```

Скрипт использует команду:

```powershell
.venv\Scripts\python.exe -m nuitka src/main.py `
    --standalone `
    --include-data-dir=assets=assets `
    --output-dir=build\nuitka `
    --output-filename=shardveil `
    --output-folder-name=Shardveil `
    --windows-console-mode=disable `
    --force-stderr-spec="{PROGRAM_BASE}.err.txt" `
    --windows-icon-from-ico=packaging/icons/shardveil.ico
```

Executable будет лежать в `build\nuitka\Shardveil.dist\`.

## Проверка сборки

Перед сборкой или после изменений полезно запустить тесты:

```bash
.venv/bin/python -m pytest
```

После сборки запустите executable из `Shardveil.dist`. Окно игры должно открыться, а спрайты игрока, тайлов, врагов, сундуков и предметов должны загружаться из bundled `assets`.

## GitHub Releases

При push тега вида `v0.1.0` GitHub Actions собирает portable archives для Windows и Linux:

- `Shardveil-windows-x64.zip`
- `Shardveil-linux-x64.tar.gz`

Внутри каждого архива находится папка `Shardveil/` с executable, assets и runtime-зависимостями. Тег должен указывать на commit из ветки `main`.

macOS app bundle пока собирается только локально и не публикуется автоматически.

Release workflow использует Python 3.12 и Nuitka 4.1.2.

Локально проверенная macOS-сборка:

- Python 3.11.9
- Arcade 3.3.3
- pyglet 2.1.13
- tcod 20.1.0
- numpy 2.4.2
- Nuitka 4.1.2
