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


class MessageLogTests(unittest.TestCase):
    def setUp(self):
        FakeText.created = []

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
            "sv.ui.message_log.arcade.draw_lrbt_rectangle_filled"
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
            "sv.ui.message_log.arcade.draw_lrbt_rectangle_filled"
        ):
            log.draw()

        self.assertEqual(FakeText.created, [])


if __name__ == "__main__":
    unittest.main()
