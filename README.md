# Game Space (Curses)

Небольшой прототип космической игры в терминале на базе `curses`.

## Возможности
- Мерцающее звездное небо
- Анимация выстрела
- Управляемый корабль

## Требования
- Python 3.7+
- Терминал с поддержкой `curses`

На Windows требуется пакет `windows-curses` (см. `requirements.txt`).

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```bash
python3 hello_curses.py
```

## Управление
- Стрелки: перемещение корабля

## Примечания
- На macOS и Linux используется встроенный модуль `curses`.
- На Windows используйте Windows Terminal и установленный `windows-curses`.
