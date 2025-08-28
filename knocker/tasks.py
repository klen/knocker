"""Utility functions for managing background tasks."""

from asyncio import Task
from asyncio import create_task as aio_create_task
from collections.abc import Coroutine

BACKGROUND_TASKS = set()


def register_task(task: Task) -> None:
    """Register a background task to keep track of it."""
    BACKGROUND_TASKS.add(task)
    task.add_done_callback(BACKGROUND_TASKS.discard)


def create_task(coro: Coroutine) -> Task:
    """Create and register a background task."""
    task = aio_create_task(coro)
    register_task(task)
    return task
