import curses


def draw_frame(canvas, start_row, start_column, text, negative=False):
    for row_index, line in enumerate(text.splitlines()):
        for column_index, char in enumerate(line):
            if char == " " and not negative:
                continue
            draw_char = " " if negative else char
            canvas.addch(start_row + row_index, start_column + column_index, draw_char)


def get_frame_size(text):
    lines = text.splitlines()
    rows = len(lines)
    columns = max((len(line) for line in lines), default=0)
    return rows, columns


def read_controls(canvas):
    rows_direction = 0
    columns_direction = 0
    space_pressed = False

    while True:
        pressed_key = canvas.getch()
        if pressed_key == -1:
            break
        if pressed_key == curses.KEY_UP:
            rows_direction = -1
        elif pressed_key == curses.KEY_DOWN:
            rows_direction = 1
        elif pressed_key == curses.KEY_RIGHT:
            columns_direction = 1
        elif pressed_key == curses.KEY_LEFT:
            columns_direction = -1
        elif pressed_key == ord(" "):
            space_pressed = True

    return rows_direction, columns_direction, space_pressed
