"""Tests for the PawPal+ core classes."""

import os
import sys
from datetime import time

# Make the project root importable so `import pawpal_system` works when pytest
# runs this file from inside the tests/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    """Task Completion: mark_complete() should flip the task's status to done."""
    task = Task("Morning walk", "walk", time(8, 0), priority=5, duration=30)

    assert task.completed is False  # a new task starts as not completed

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet should grow its task list by one."""
    pet = Pet("Biscuit", "dog")

    assert len(pet.tasks) == 0  # a new pet has no tasks

    task = Task("Dental work", "dental", time(9, 30), priority=4, duration=45)
    pet.add_task(task)

    assert len(pet.tasks) == 1
