from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Deque, Dict, List, Optional

EventCallback = Callable[["GameEvent"], None]


class EventType(Enum):
    INFO = auto()
    COMBAT = auto()
    SYSTEM = auto()
    DAMAGE = auto()
    HEAL = auto()
    DEATH = auto()
    ITEM_PICKED = auto()
    FLOOR_CHANGED = auto()


@dataclass(slots=True)
class GameEvent:
    type: EventType
    source: Any = None
    target: Any = None
    value: Any = None
    message: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


class EventQueue:
    """Простая очередь событий, которая может быть использована для хранения событий до их обработки."""

    def __init__(self, maxlen: Optional[int] = None):
        self._events: Deque[GameEvent] = deque(maxlen=maxlen)

    def emit(self, event: GameEvent) -> None:
        self._events.append(event)

    def drain(self) -> List[GameEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    def clear(self) -> None:
        self._events.clear()

    def has_events(self) -> bool:
        return bool(self._events)


class EventBus:
    """Очередь событий с поддержкой подписчиков, которые могут реагировать на определенные типы событий."""

    def __init__(self, maxlen: Optional[int] = None):
        self._queue = EventQueue(maxlen=maxlen)
        self._subscribers: Dict[EventType, List[EventCallback]] = {}

    def emit(self, event: GameEvent) -> None:
        self._queue.emit(event)
        for callback in tuple(self._subscribers.get(event.type, ())):
            callback(event)

    def drain(self) -> List[GameEvent]:
        return self._queue.drain()

    def clear(self) -> None:
        self._queue.clear()

    def has_events(self) -> bool:
        return self._queue.has_events()

    def subscribe(self, event_type: EventType, callback: EventCallback) -> None:
        subscribers = self._subscribers.setdefault(event_type, [])
        if callback not in subscribers:
            subscribers.append(callback)

    def unsubscribe(self, event_type: EventType, callback: EventCallback) -> None:
        subscribers = self._subscribers.get(event_type)
        if not subscribers:
            return
        try:
            subscribers.remove(callback)
        except ValueError:
            return
        if not subscribers:
            del self._subscribers[event_type]


__all__ = ["EventBus", "EventQueue", "EventType", "GameEvent"]
