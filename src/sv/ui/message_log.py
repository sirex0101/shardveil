from collections import deque
from dataclasses import dataclass

import arcade


@dataclass(slots=True)
class Message:
    text: str
    kind: str


class MessageLog:
    COLORS = {
        "info": arcade.color.LIGHT_GRAY,
        "combat": arcade.color.ORANGE_RED,
        "system": arcade.color.GOLD,
    }

    def __init__(self, x=10, y=70, width=350, line_height=18, max_messages=6):
        self.x = int(x)
        self.y = int(y)
        self.width = max(1, int(width))
        self.line_height = max(1, int(line_height))
        self.max_messages = max(1, int(max_messages))
        self.messages: deque[Message] = deque()
        self._text_objects: list[arcade.Text] = []
        self._dirty = True

    def push(self, text: str, kind: str = "info"):
        self.messages.append(Message(text, kind))

        while len(self.messages) > self.max_messages:
            self.messages.popleft()

        self._dirty = True

    def clear(self):
        self.messages.clear()
        self._dirty = True

    def _rebuild(self):
        self._text_objects.clear()
        y_offset = 0

        for msg in reversed(self.messages):
            color = self.COLORS.get(msg.kind, arcade.color.WHITE)
            text = arcade.Text(
                msg.text,
                self.x,
                self.y + y_offset,
                color,
                14,
                width=self.width,
                multiline=True,
            )
            self._text_objects.append(text)
            y_offset += self.line_height

        self._dirty = False

    def draw(self):
        if not self.messages:
            return

        visible_lines = min(len(self.messages), self.max_messages)
        arcade.draw_lrbt_rectangle_filled(
            self.x - 5,
            self.x + self.width,
            self.y - 5,
            self.y + self.line_height * visible_lines + 5,
            (0, 0, 0, 120),
        )

        if self._dirty:
            self._rebuild()

        for text in self._text_objects:
            text.draw()
