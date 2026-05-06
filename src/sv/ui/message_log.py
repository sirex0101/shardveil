from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import arcade
from arcade import gui


@dataclass(slots=True)
class Message:
    text: str
    kind: str


class MessageLog(gui.UIWidget):
    COLORS = {
        "info": arcade.color.LIGHT_GRAY,
        "combat": arcade.color.ORANGE_RED,
        "system": arcade.color.GOLD,
    }

    def __init__(
        self,
        *,
        width: int = 350,
        max_messages: int = 6,
        line_height: int = 22,
        padding_x: int = 10,
        padding_y: int = 8,
        font_size: int = 14,
    ):
        width = max(1, int(width))
        max_messages = max(1, int(max_messages))
        line_height = max(1, int(line_height))
        padding_x = max(0, int(padding_x))
        padding_y = max(0, int(padding_y))
        height = max_messages * line_height + padding_y * 2

        super().__init__(width=width, height=height, size_hint=None)

        self.max_messages = max_messages
        self.line_height = line_height
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.font_size = font_size
        self.messages: deque[Message] = deque()
        self._text_objects: list[arcade.Text] = []
        self._dirty = True

    def push(self, text: str, kind: str = "info"):
        self.messages.append(Message(text, kind))

        while len(self.messages) > self.max_messages:
            self.messages.popleft()

        self._dirty = True
        self.trigger_render()

    def clear(self):
        self.messages.clear()
        self._dirty = True
        self.trigger_render()

    def _rebuild(self) -> None:
        self._text_objects.clear()

        for index, msg in enumerate(reversed(self.messages)):
            row_bottom = self.padding_y + self.line_height * index
            color = self.COLORS.get(msg.kind, arcade.color.WHITE)
            self._text_objects.append(
                arcade.Text(
                    msg.text,
                    self.padding_x,
                    row_bottom + 2,
                    color,
                    self.font_size,
                    width=self.width - self.padding_x * 2,
                    multiline=True,
                    anchor_y="bottom",
                )
            )

        self._dirty = False

    def _draw_contents(self) -> None:
        if not self.messages:
            return

        if self._dirty:
            self._rebuild()

        row_height = self.line_height
        for index, text in enumerate(self._text_objects):
            row_bottom = self.padding_y + row_height * index
            arcade.draw_rect_filled(
                arcade.LBWH(
                    0,
                    row_bottom,
                    self.width,
                    row_height,
                ),
                (0, 0, 0, 120),
            )
            text.draw()

    def do_render(self, surface: gui.Surface) -> None:
        surface.clear()
        self.prepare_render(surface)
        self._draw_contents()

    def draw(self):
        self._draw_contents()
