# pylint: disable=E1101
import curses


class TextEditor:

    def __init__(self):
        self.array = list()
        self.cursor = [0, 0]
        self.stdscr = None
        self.clipboard = None
        self.scroll = 0
        self.rows = 0

    def __call__(self, base_text=""):
        self.array = base_text.split("\n")
        self.cursor = [0, 0]
        self.stdscr = curses.initscr()
        self.rows = self.stdscr.getmaxyx()[0]
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        while True:
            self.draw()
            key = self.stdscr.getch()
            break_loop = self._handle_key(key)
            if break_loop:
                break
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()
        return "\n".join(self.array)

    def _move_cursor_left(self):
        self.cursor[1] = max(0, self.cursor[1] - 1)

    def _move_cursor_right(self):
        self.cursor[1] = min(
            len(self.array[self.cursor[0]]),
            self.cursor[1] + 1
        )

    def _move_cursor_up(self):
        self.cursor[0] = max(0, self.cursor[0] - 1)
        self.cursor[1] = min(self.cursor[1], len(self.array[self.cursor[0]]))
        if self.cursor[0] < self.scroll:
            self.scroll -= 1

    def _move_cursor_down(self):
        self.cursor[0] = min(len(self.array) - 1, self.cursor[0] + 1)
        self.cursor[1] = min(self.cursor[1], len(self.array[self.cursor[0]]))
        if self.cursor[0] >= self.rows + self.scroll:
            self.scroll += 1

    def _handle_key(self, key):  # pylint: disable=R0912,R0915
        if key in {
                3,  # ^C
                4,  # ^D
                17,  # ^Q
                23,  # ^W
                24,  # ^X
                27  # ESC
            }:
            return True
        if key == 260:  # Left
            self._move_cursor_left()
        elif key == 261:  # Right
            self._move_cursor_right()
        elif key == 259:  # Up
            self._move_cursor_up()
        elif key == 258:  # Down
            self._move_cursor_down()
        elif key == 338:  # Page Down
            for _ in range(self.rows):
                self._move_cursor_down()
        elif key == 339:  # Page Up
            for _ in range(self.rows):
                self._move_cursor_up()
        elif key == 443:  # Ctrl+Left
            for i in range(1, self.cursor[1] + 1):
                target = self.cursor[1] - i
                if target == 0 or self.array[self.cursor[0]][target - 1] == " ":
                    self.cursor[1] = target
                    break
        elif key == 444:  # Ctrl+Right
            for target in range(self.cursor[1] + 1, len(self.array[self.cursor[0]]) + 1):
                if target == len(self.array[self.cursor[0]])\
                    or self.array[self.cursor[0]][target - 1] == " ":
                    self.cursor[1] = target
                    break
        elif key == 1:  # ^A
            self.cursor[1] = 0
        elif key == 5:  # ^E
            self.cursor[1] = len(self.array[self.cursor[0]])
        elif key == 10:  # ENTER
            prev_line = self.array[self.cursor[0]][:self.cursor[1]]
            next_line = self.array[self.cursor[0]][self.cursor[1]:]
            self.array[self.cursor[0]] = prev_line
            self.array.insert(self.cursor[0] + 1, next_line)
            self._move_cursor_down()
            self.cursor[1] = 0
        elif key == 8:  # BACKSPACE
            if self.cursor[1] == 0:
                if self.cursor[0] > 0:
                    self.cursor[1] = len(self.array[self.cursor[0] - 1])
                    self.array[self.cursor[0] - 1] =\
                        self.array[self.cursor[0] - 1]\
                        + self.array[self.cursor[0]]
                    self.array.pop(self.cursor[0])
                    self.cursor[0] = self.cursor[0] - 1
            else:
                self.array[self.cursor[0]] =\
                    self.array[self.cursor[0]][:self.cursor[1] - 1]\
                    + self.array[self.cursor[0]][self.cursor[1]:]
                self.cursor[1] = max(0, self.cursor[1] - 1)
        elif key == 330:  # DELETE:
            if self.cursor[1] == len(self.array[self.cursor[0]]):
                if self.cursor[0] < len(self.array) - 1:
                    self.array[self.cursor[0]] += self.array[self.cursor[0] + 1]
                    self.array.pop(self.cursor[0] + 1)
            else:
                self.array[self.cursor[0]] =\
                    self.array[self.cursor[0]][:self.cursor[1]]\
                    + self.array[self.cursor[0]][self.cursor[1] + 1:]
        elif key == 11:  # ^K
            self.clipboard = self.array[self.cursor[0]]
            self.array.pop(self.cursor[0])
            self._move_cursor_up()
            self._move_cursor_down()
        elif key == 21:  # ^U
            self.array.insert(self.cursor[0], self.clipboard)
            self.cursor[1] = len(self.clipboard)
        elif key < 256:
            self.array[self.cursor[0]] =\
                self.array[self.cursor[0]][:self.cursor[1]]\
                + chr(key)\
                + self.array[self.cursor[0]][self.cursor[1]:]
            self._move_cursor_right()
        return False

    def draw(self):
        self.stdscr.clear()
        for i, line in enumerate(self.array[self.scroll:]):
            if i >= self.rows:
                break
            self.stdscr.addstr(i, 0, line)
        self.stdscr.addstr(self.cursor[0] - self.scroll, self.cursor[1], "")
        self.stdscr.refresh()
