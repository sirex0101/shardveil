from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import textwrap

import arcade
from arcade import gui


@dataclass(slots=True)
class Message:
    text: str
    kind: str


@dataclass(slots=True)
class RenderedMessage:
    text: arcade.Text
    bottom: float
    height: float


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
        self.max_lines_per_message = 2
        self.line_height = line_height
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.font_size = font_size
        self.messages: deque[Message] = deque()
        self._rendered_messages: list[RenderedMessage] = []
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
        self._rendered_messages.clear()
        next_bottom = self.padding_y
        content_top = self.height - self.padding_y

        for msg in reversed(self.messages):
            wrapped_text, line_count = self._wrap_text(msg.text)
            block_height = line_count * self.line_height
            if next_bottom + block_height > content_top:
                break
            color = self.COLORS.get(msg.kind, arcade.color.WHITE)
            self._rendered_messages.append(
                RenderedMessage(
                    arcade.Text(
                        wrapped_text,
                        self.padding_x,
                        next_bottom + 2,
                        color,
                        self.font_size,
                        width=int(self.width - self.padding_x * 2),
                        multiline=True,
                        anchor_y="bottom",
                    ),
                    bottom=next_bottom,
                    height=block_height,
                ),
            )
            next_bottom += block_height

        self._dirty = False

    def _wrap_text(self, text: str) -> tuple[str, int]:
        available_width = max(1, int(self.width - self.padding_x * 2))
        average_char_width = max(1.0, self.font_size * 0.58)
        max_chars = max(8, int(available_width / average_char_width))
        source_lines = str(text).splitlines() or [""]

        lines: list[str] = []
        for source_line in source_lines:
            wrapped = textwrap.wrap(
                source_line,
                width=max_chars,
                break_long_words=True,
                replace_whitespace=False,
            ) or [""]
            for line in wrapped:
                lines.append(line)
                if len(lines) == self.max_lines_per_message:
                    break
            if len(lines) == self.max_lines_per_message:
                break

        if self._line_count_for_text(text, max_chars) > self.max_lines_per_message:
            lines[-1] = self._ellipsize(lines[-1], max_chars)

        return "\n".join(lines), max(1, len(lines))

    def _line_count_for_text(self, text: str, max_chars: int) -> int:
        count = 0
        for source_line in str(text).splitlines() or [""]:
            count += max(
                1,
                len(
                    textwrap.wrap(
                        source_line,
                        width=max_chars,
                        break_long_words=True,
                        replace_whitespace=False,
                    )
                ),
            )
        return count

    @staticmethod
    def _ellipsize(text: str, max_chars: int) -> str:
        if max_chars <= 3:
            return "..."
        if len(text) <= max_chars - 3:
            return f"{text}..."
        return f"{text[: max_chars - 3]}..."

    def _draw_contents(self) -> None:
        if not self.messages:
            return

        if self._dirty:
            self._rebuild()

        for rendered in self._rendered_messages:
            arcade.draw_rect_filled(
                arcade.LBWH(
                    0,
                    rendered.bottom,
                    self.width,
                    rendered.height,
                ),
                (0, 0, 0, 120),
            )
            rendered.text.draw()

    def do_render(self, surface: gui.Surface) -> None:
        surface.clear()
        self.prepare_render(surface)
        self._draw_contents()

    def draw(self):
        self._draw_contents()
