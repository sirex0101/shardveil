# Standalone-сборка через Nuitka

Shardveil можно собрать в standalone-версию через Nuitka. Сборка создаёт папку с executable, Python runtime, native-зависимостями и игровыми assets.

Nuitka-сборки платформозависимы: Windows-билд - на Windows, macOS-билд собирается на macOS, Linux-билд - на Linux.

## Подготовка окружения

Создайте виртуальное окружение и установите зависимости проекта:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install nuitka
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
  --enable-plugin=numpy \
  --include-data-dir=assets=assets \
  --output-dir=build/nuitka \
  --output-filename=shardveil
```

Ожидаемый результат:

- build-артефакты: `build/nuitka/main.build/`
- standalone-папка: `build/nuitka/main.dist/`
- executable: `build/nuitka/main.dist/shardveil`
- bundled assets: `build/nuitka/main.dist/assets/`

Запуск собранной игры:

```bash
build/nuitka/main.dist/shardveil
```

## Windows

Подготовка окружения в PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install nuitka
```

Запуск из корня репозитория:

```powershell
scripts\build_nuitka_windows.ps1
```

Скрипт использует команду:

```powershell
.venv\Scripts\python.exe -m nuitka src/main.py `
    --standalone `
    --enable-plugin=numpy `
    --include-data-dir=assets=assets `
    --output-dir=build\nuitka `
    --output-filename=shardveil
```

Ожидаемый layout такой же под `build\nuitka`, executable будет лежать в `build\nuitka\main.dist\`.

## Проверка сборки

Перед сборкой или после изменений полезно запустить тесты:

```bash
.venv/bin/python -m pytest
```

После сборки запустите executable из `main.dist`. Окно игры должно открыться, а спрайты игрока, тайлов, врагов, сундуков и предметов должны загружаться из bundled `assets`.

Локально проверенная macOS-сборка:

- Python 3.11.9
- Arcade 3.3.3
- pyglet 2.1.13
- tcod 20.1.0
- numpy 2.4.2
- Nuitka 4.1.2
