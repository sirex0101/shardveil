import sys
from pathlib import Path
import unittest
from unittest.mock import patch

import arcade


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sv.ui.message_log import MessageLog


class FakeText:
    created = []

    def __init__(self, text, x, y, color, size, **kwargs):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.kwargs = kwargs
        FakeText.created.append(self)

    def draw(self):
        pass


class DrawRectCalls:
    created = []

    def __call__(self, rect, color):
        self.created.append((rect, color))


class MessageLogTests(unittest.TestCase):
    def setUp(self):
        FakeText.created = []
        DrawRectCalls.created = []

    def test_push_adds_messages_in_order(self):
        log = MessageLog(max_messages=3)

        log.push("first", "info")
        log.push("second", "combat")
        log.push("third", "system")

        self.assertEqual([msg.text for msg in log.messages], ["first", "second", "third"])
        self.assertTrue(log._dirty)

    def test_max_messages_discards_oldest(self):
        log = MessageLog(max_messages=3)

        log.push("first")
        log.push("second")
        log.push("third")
        log.push("fourth")

        self.assertEqual([msg.text for msg in log.messages], ["second", "third", "fourth"])

    def test_clear_empties_messages_and_marks_dirty(self):
        log = MessageLog()
        log.push("first")

        log.clear()

        self.assertEqual(len(log.messages), 0)
        self.assertTrue(log._dirty)

    def test_draw_rebuilds_text_objects_and_uses_type_colors(self):
        log = MessageLog(max_messages=4)
        log.push("first", "info")
        log.push("second", "combat")
        log.push("third", "mystery")

        with patch("sv.ui.message_log.arcade.Text", FakeText), patch(
            "sv.ui.message_log.arcade.draw_rect_filled"
        ):
            log.draw()
            first_pass = len(FakeText.created)
            log.draw()

        self.assertEqual([text.text for text in FakeText.created], ["third", "second", "first"])
        self.assertEqual(
            [text.color for text in FakeText.created],
            [arcade.color.WHITE, MessageLog.COLORS["combat"], MessageLog.COLORS["info"]],
        )
        self.assertEqual(first_pass, 3)
        self.assertEqual(len(FakeText.created), 3)

    def test_draw_on_empty_log_is_safe(self):
        log = MessageLog()

        with patch("sv.ui.message_log.arcade.Text", FakeText), patch(
            "sv.ui.message_log.arcade.draw_rect_filled"
        ):
            log.draw()

        self.assertEqual(FakeText.created, [])

    def test_long_message_is_limited_to_two_lines(self):
        log = MessageLog(width=90, max_messages=3, line_height=22)
        log.push("Глубина 12. Найдите лестницу вниз и не тратьте свет зря", "system")

        draw_rect_calls = DrawRectCalls()
        with patch("sv.ui.message_log.arcade.Text", FakeText), patch(
            "sv.ui.message_log.arcade.draw_rect_filled", draw_rect_calls
        ):
            log.draw()

        self.assertEqual(len(FakeText.created), 1)
        rendered_text = FakeText.created[0].text
        self.assertLessEqual(len(rendered_text.splitlines()), 2)
        self.assertTrue(rendered_text.endswith("..."))
        self.assertEqual(draw_rect_calls.created[0][0].height, 44)

    def test_variable_height_messages_do_not_share_the_same_row(self):
        log = MessageLog(width=90, max_messages=4, line_height=22)
        log.push("short", "info")
        log.push("Очень длинное сообщение журнала боя, которое занимает две строки", "combat")

        draw_rect_calls = DrawRectCalls()
        with patch("sv.ui.message_log.arcade.Text", FakeText), patch(
            "sv.ui.message_log.arcade.draw_rect_filled", draw_rect_calls
        ):
            log.draw()

        first_rect = draw_rect_calls.created[0][0]
        second_rect = draw_rect_calls.created[1][0]
        self.assertEqual(first_rect.height, 44)
        self.assertEqual(second_rect.bottom, first_rect.bottom + first_rect.height)


if __name__ == "__main__":
    unittest.main()
