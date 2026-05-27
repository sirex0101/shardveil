"""Compatibility exports for legacy entity imports."""

from sv.entities.base import Entity
from sv.entities.enemy import Enemy, Skeleton
from sv.entities.player import Player

__all__ = ["Enemy", "Entity", "Player", "Skeleton"]
