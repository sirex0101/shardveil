import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sv.core.events import EventBus, EventQueue, EventType, GameEvent


class EventQueueTests(unittest.TestCase):
    def test_emit_adds_event_and_has_events_returns_true(self):
        queue = EventQueue()
        event = GameEvent(EventType.INFO, message="hello")

        queue.emit(event)

        self.assertTrue(queue.has_events())
        self.assertEqual(queue.drain(), [event])

    def test_drain_returns_fifo_order_and_clears_queue(self):
        queue = EventQueue()
        first = GameEvent(EventType.INFO, message="first")
        second = GameEvent(EventType.COMBAT, message="second")

        queue.emit(first)
        queue.emit(second)

        drained = queue.drain()

        self.assertEqual(drained, [first, second])
        self.assertFalse(queue.has_events())
        self.assertEqual(queue.drain(), [])

    def test_clear_removes_all_events(self):
        queue = EventQueue()
        queue.emit(GameEvent(EventType.SYSTEM, message="one"))

        queue.clear()

        self.assertFalse(queue.has_events())
        self.assertEqual(queue.drain(), [])


class EventBusTests(unittest.TestCase):
    def test_emit_notifies_subscribers_for_matching_event_type(self):
        bus = EventBus()
        seen = []

        def handle(event):
            seen.append(event)

        bus.subscribe(EventType.SYSTEM, handle)
        event = GameEvent(EventType.SYSTEM, message="ready")

        bus.emit(event)

        self.assertEqual(seen, [event])
        self.assertTrue(bus.has_events())
        self.assertEqual(bus.drain(), [event])

    def test_subscribe_does_not_duplicate_callbacks(self):
        bus = EventBus()
        seen = []

        def handle(event):
            seen.append(event)

        bus.subscribe(EventType.INFO, handle)
        bus.subscribe(EventType.INFO, handle)

        bus.emit(GameEvent(EventType.INFO, message="info"))

        self.assertEqual(len(seen), 1)

    def test_unsubscribe_removes_callback(self):
        bus = EventBus()
        seen = []

        def handle(event):
            seen.append(event)

        bus.subscribe(EventType.COMBAT, handle)
        bus.unsubscribe(EventType.COMBAT, handle)

        bus.emit(GameEvent(EventType.COMBAT, message="combat"))

        self.assertEqual(seen, [])
        self.assertTrue(bus.has_events())


if __name__ == "__main__":
    unittest.main()
