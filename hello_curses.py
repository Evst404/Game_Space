import asyncio
import curses
import itertools
import random
import time

from curses_tools import draw_frame, get_frame_size, read_controls

FRAMES_DIR = "frames"
ROCKET_FRAME_1 = f"{FRAMES_DIR}/rocket_frame_1.txt"
STAR_COUNT = 100
STAR_SYMBOLS = "+*.:"
TIC_TIMEOUT = 0.1


async def blink(canvas, row, column, symbol="*"):
    dim_ticks = int(2 / TIC_TIMEOUT)
    normal_ticks = int(0.3 / TIC_TIMEOUT)
    bold_ticks = int(0.5 / TIC_TIMEOUT)
    start_delay = random.randint(0, 20)
    for _ in range(start_delay):
        await asyncio.sleep(0)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(dim_ticks):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(normal_ticks):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(bold_ticks):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(normal_ticks):
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), "*")
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), "O")
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), " ")

    row += rows_speed
    column += columns_speed

    symbol = "-" if columns_speed else "|"

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), " ")
        row += rows_speed
        column += columns_speed


async def animate_spaceship(
    canvas,
    start_row,
    start_column,
    frames,
    max_rows,
    max_columns,
    frame_rows,
    frame_columns,
):
    row, column = start_row, start_column
    current_frame = frames[0]
    previous_frame = current_frame
    previous_row, previous_column = row, column
    frame_cycle = itertools.cycle(frames)
    frame_ticks = 0

    while True:
        draw_frame(canvas, previous_row, previous_column, previous_frame, negative=True)

        rows_direction, columns_direction, _ = read_controls(canvas)
        row += rows_direction
        column += columns_direction

        min_row, min_column = 1, 1
        max_row = max_rows - frame_rows - 1
        max_column = max_columns - frame_columns - 1
        row = max(min_row, min(row, max_row))
        column = max(min_column, min(column, max_column))

        if frame_ticks % 2 == 0:
            current_frame = next(frame_cycle)

        draw_frame(canvas, row, column, current_frame)
        await asyncio.sleep(0)

        previous_row, previous_column = row, column
        previous_frame = current_frame
        frame_ticks += 1


def draw(canvas):
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas.border()
    max_rows, max_columns = canvas.getmaxyx()
    stars = [
        (
            random.randint(1, max_rows - 2),
            random.randint(1, max_columns - 2),
            random.choice(STAR_SYMBOLS),
        )
        for _ in range(STAR_COUNT)
    ]
    with open(ROCKET_FRAME_1, "r") as frame_file:
        spaceship_frame = frame_file.read()
    frames = [spaceship_frame]
    frame_rows, frame_columns = get_frame_size(spaceship_frame)
    start_row = max_rows // 2 - frame_rows // 2
    start_column = max_columns // 2 - frame_columns // 2

    coroutines = [blink(canvas, row, column, symbol) for row, column, symbol in stars]
    coroutines.append(
        animate_spaceship(
            canvas,
            start_row,
            start_column,
            frames,
            max_rows,
            max_columns,
            frame_rows,
            frame_columns,
        )
    )
    coroutines.append(fire(canvas, max_rows // 2, max_columns // 2))
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
