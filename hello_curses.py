import asyncio
import curses
import itertools
import random
import time

from curses_tools import draw_frame, get_frame_size, read_controls
from explosion import explode
from game_scenario import PHRASES, get_garbage_delay_tics
from obstacles import Obstacle
from physics import update_speed

FRAMES_DIR = "frames"
ROCKET_FRAME_1 = f"{FRAMES_DIR}/rocket_frame_1.txt"
GARBAGE_FRAMES_DIR = f"{FRAMES_DIR}/garbage"
GARBAGE_FRAME_FILES = (
    f"{GARBAGE_FRAMES_DIR}/duck.txt",
    f"{GARBAGE_FRAMES_DIR}/hubble.txt",
    f"{GARBAGE_FRAMES_DIR}/lamp.txt",
    f"{GARBAGE_FRAMES_DIR}/trash_large.txt",
    f"{GARBAGE_FRAMES_DIR}/trash_small.txt",
    f"{GARBAGE_FRAMES_DIR}/trash_xl.txt",
)
STAR_COUNT = 100
STAR_SYMBOLS = "+*.:"
TIC_TIMEOUT = 0.1
MAX_START_DELAY_TICS = 20
BORDER_THICKNESS = 1
SHIP_SPEED_LIMIT = 1.0
SHIP_SPEED_FADING = 0.1
STOP_SPEED_THRESHOLD = 0.5
YEAR_START = 1957
YEAR_TICS = round(1.5 / TIC_TIMEOUT)
GUN_ENABLED_YEAR = 2020
GAME_OVER_FRAME = """\
  _____                        ____                 
 / ____|                      / __ \\                
| |  __  __ _ _ __ ___   ___ | |  | |_   _____ _ __ 
| | |_ |/ _` | '_ ` _ \\ / _ \\| |  | \\ \\ / / _ \\ '__|
| |__| | (_| | | | | | |  __/| |__| |\\ V /  __/ |   
 \\_____|\\__,_|_| |_| |_|\\___| \\____/  \\_/ \\___|_|   
"""

coroutines = []
obstacles = []
obstacles_in_last_collisions = []
year = YEAR_START


async def blink(canvas, row, column, offset_tics, symbol="*"):
    dim_ticks = round(2 / TIC_TIMEOUT)
    normal_ticks = round(0.3 / TIC_TIMEOUT)
    bold_ticks = round(0.5 / TIC_TIMEOUT)
    await sleep(offset_tics)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(dim_ticks)

        canvas.addstr(row, column, symbol)
        await sleep(normal_ticks)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(bold_ticks)

        canvas.addstr(row, column, symbol)
        await sleep(normal_ticks)


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
        for obstacle in obstacles:
            if obstacle.has_collision(round(row), round(column)):
                obstacles_in_last_collisions.append(obstacle)
                return


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom."""
    rows_number, columns_number = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(garbage_frame)

    min_column = BORDER_THICKNESS
    max_column = max(
        min_column, columns_number - frame_columns - BORDER_THICKNESS
    )
    column = max(column, min_column)
    column = min(column, max_column)

    row = BORDER_THICKNESS
    max_row = rows_number - frame_rows - BORDER_THICKNESS

    obstacle = Obstacle(row, column, frame_rows, frame_columns)
    obstacles.append(obstacle)
    try:
        while row < max_row:
            if obstacle in obstacles_in_last_collisions:
                obstacles_in_last_collisions.remove(obstacle)
                draw_frame(
                    canvas, round(row), column, garbage_frame, negative=True
                )
                coroutines.append(
                    explode(
                        canvas,
                        obstacle.row + obstacle.rows_size // 2,
                        obstacle.column + obstacle.columns_size // 2,
                    )
                )
                return
            obstacle.row = round(row)
            draw_frame(canvas, round(row), column, garbage_frame)
            await sleep()
            draw_frame(canvas, round(row), column, garbage_frame, negative=True)
            row += speed
    finally:
        obstacles.remove(obstacle)


async def fill_orbit_with_garbage(canvas, garbage_frames):
    rows_number, columns_number = canvas.getmaxyx()
    while True:
        delay = get_garbage_delay_tics(year)
        if delay is None:
            await sleep(1)
            continue
        garbage_frame = random.choice(garbage_frames)
        _, garbage_columns = get_frame_size(garbage_frame)
        min_column = BORDER_THICKNESS
        max_column = max(
            min_column, columns_number - garbage_columns - BORDER_THICKNESS
        )
        column = random.randint(min_column, max_column)
        coroutines.append(fly_garbage(canvas, column, garbage_frame))
        await sleep(delay)


async def run_spaceship(
    canvas,
    start_row,
    start_column,
    frames,
    max_rows,
    max_columns,
    frame_rows,
    frame_columns,
):
    global coroutines
    row, column = start_row, start_column
    row_speed = 0
    column_speed = 0
    current_frame = frames[0]
    previous_frame = current_frame
    previous_row, previous_column = row, column
    frame_cycle = itertools.cycle(frames)
    frame_ticks = 0

    while True:
        draw_frame(
            canvas,
            round(previous_row),
            round(previous_column),
            previous_frame,
            negative=True,
        )

        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(
            row_speed,
            column_speed,
            rows_direction,
            columns_direction,
            row_speed_limit=SHIP_SPEED_LIMIT,
            column_speed_limit=SHIP_SPEED_LIMIT,
            fading=SHIP_SPEED_FADING,
        )
        if rows_direction == 0 and abs(row_speed) < STOP_SPEED_THRESHOLD:
            row_speed = 0
        if columns_direction == 0 and abs(column_speed) < STOP_SPEED_THRESHOLD:
            column_speed = 0
        row += row_speed
        column += column_speed

        min_row, min_column = 1, 1
        max_row = max_rows - frame_rows - 1
        max_column = max_columns - frame_columns - 1
        row = max(min_row, min(row, max_row))
        column = max(min_column, min(column, max_column))

        if space_pressed and year >= GUN_ENABLED_YEAR:
            gun_row = round(row)
            gun_column = round(column + frame_columns // 2)
            coroutines.append(fire(canvas, gun_row, gun_column))

        if frame_ticks % 2 == 0:
            current_frame = next(frame_cycle)

        draw_frame(canvas, round(row), round(column), current_frame)
        await sleep()

        previous_row, previous_column = row, column
        previous_frame = current_frame
        frame_ticks += 1

        for obstacle in obstacles:
            if obstacle.has_collision(
                round(row), round(column), frame_rows, frame_columns
            ):
                draw_frame(
                    canvas,
                    round(row),
                    round(column),
                    current_frame,
                    negative=True,
                )
                return "game_over"


async def show_gameover(canvas):
    rows_number, columns_number = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(GAME_OVER_FRAME)
    start_row = rows_number // 2 - frame_rows // 2
    start_column = columns_number // 2 - frame_columns // 2
    while True:
        draw_frame(canvas, start_row, start_column, GAME_OVER_FRAME)
        await sleep()


async def count_years():
    global year
    while True:
        await sleep(YEAR_TICS)
        year += 1


async def show_year(canvas):
    max_rows, max_columns = canvas.getmaxyx()
    status_window = canvas.derwin(1, max_columns - 2, max_rows - 2, 1)
    while True:
        status_window.erase()
        phrase = PHRASES.get(year, "")
        status = f"Year: {year} {phrase}".strip()
        try:
            status_window.addstr(0, 0, status[: max_columns - 2])
        except curses.error:
            pass
        await sleep()


def draw(canvas):
    global coroutines
    global year
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas.border()
    year = YEAR_START
    max_rows, max_columns = canvas.getmaxyx()
    min_star_row = BORDER_THICKNESS
    max_star_row = max_rows - BORDER_THICKNESS - 1
    min_star_column = BORDER_THICKNESS
    max_star_column = max_columns - BORDER_THICKNESS - 1
    stars = [
        (
            random.randint(min_star_row, max_star_row),
            random.randint(min_star_column, max_star_column),
            random.choice(STAR_SYMBOLS),
        )
        for _ in range(STAR_COUNT)
    ]
    with open(ROCKET_FRAME_1, "r") as frame_file:
        spaceship_frame = frame_file.read()
    garbage_frames = []
    for garbage_path in GARBAGE_FRAME_FILES:
        with open(garbage_path, "r") as garbage_file:
            garbage_frames.append(garbage_file.read())
    frames = [spaceship_frame]
    frame_rows, frame_columns = get_frame_size(spaceship_frame)
    start_row = max_rows // 2 - frame_rows // 2
    start_column = max_columns // 2 - frame_columns // 2
    coroutines = [
        blink(
            canvas,
            row,
            column,
            random.randint(0, MAX_START_DELAY_TICS),
            symbol,
        )
        for row, column, symbol in stars
    ]
    coroutines.append(
        run_spaceship(
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
    coroutines.append(fill_orbit_with_garbage(canvas, garbage_frames))
    coroutines.append(count_years())
    coroutines.append(show_year(canvas))
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration as exc:
                if exc.value == "game_over":
                    coroutines.clear()
                    coroutines.append(show_gameover(canvas))
                    break
                if coroutine in coroutines:
                    coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
