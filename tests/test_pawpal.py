"""Tests for the PawPal+ core classes."""

import os
import sys
from datetime import date, time

# Make the project root importable so `import pawpal_system` works when pytest
# runs this file from inside the tests/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Owner, Pet, Task, Scheduler


def _scheduler_with(tasks, available_minutes=240):
    """Build a Scheduler pre-loaded with the given tasks."""
    scheduler = Scheduler(available_minutes=available_minutes)
    for task in tasks:
        scheduler.add_task(task)
    return scheduler


def test_mark_complete_changes_status():
    """Task Completion: mark_complete() should flip the task's status to done."""
    task = Task("Morning walk", "walk", time(8, 0), priority=5, duration=30)

    assert task.completed is False  # a new task starts as not completed

    task.mark_complete()

    assert task.completed is True


def test_mark_complete_spawns_next_occurrence_for_recurring():
    """Recurrence: completing a daily/weekly task auto-creates a fresh, not-yet-
    completed instance for the next occurrence and attaches it to the same pet."""
    pet = Pet("Biscuit", "dog")
    walk = Task("Walk", "walk", time(8, 0), priority=5, duration=30,
                recurrence="daily")
    vet = Task("Vet", "medical", time(10, 0), priority=4, duration=60,
               recurrence="weekly:tuesday")
    pet.add_task(walk)
    pet.add_task(vet)

    new_walk = walk.mark_complete()
    new_vet = vet.mark_complete()

    # The originals are done; a fresh copy of each was returned.
    assert walk.completed is True and vet.completed is True
    assert new_walk is not None and new_vet is not None

    # The new instances are distinct, not completed, and carry the same schedule.
    assert new_walk is not walk
    assert new_walk.completed is False
    assert new_walk.name == "Walk" and new_walk.recurrence == "daily"
    assert new_vet.recurrence == "weekly:tuesday"

    # They were attached to the same pet, with the back-reference set.
    assert new_walk.pet is pet and new_vet.pet is pet
    assert pet.tasks == [walk, vet, new_walk, new_vet]


def test_next_occurrence_advances_due_date_with_timedelta():
    """Recurrence dates: completing a daily task sets the next due date to the
    original due date + 1 day; a weekly task advances by 7 days. Uses fixed
    dates (incl. a month boundary) so the timedelta math is checked exactly."""
    # Daily: a task due Jan 31 rolls over to Feb 1 (timedelta handles the month).
    daily = Task("Feed", "feeding", time(7, 0), priority=3, duration=10,
                 recurrence="daily", due_date=date(2026, 1, 31))
    next_daily = daily.next_occurrence()
    assert next_daily.due_date == date(2026, 2, 1)

    # Weekly: +7 days.
    weekly = Task("Vet", "medical", time(10, 0), priority=4, duration=60,
                  recurrence="weekly:tuesday", due_date=date(2026, 1, 6))
    next_weekly = weekly.next_occurrence()
    assert next_weekly.due_date == date(2026, 1, 13)

    # A brand-new task with no explicit due_date defaults to today.
    assert Task("X", "x", time(9, 0), 1, 5).due_date == date.today()


def test_check_time_conflicts_reports_same_and_different_pets():
    """Conflict detection: check_time_conflicts() returns a warning string that
    flags same-time tasks and distinguishes same-pet from different-pet clashes,
    and reports 'no conflicts' when there are none."""
    biscuit = Pet("Biscuit", "dog")
    mochi = Pet("Mochi", "cat")

    # Same pet, same start time.
    walk = Task("Walk", "walk", time(8, 0), priority=5, duration=30, pet=biscuit)
    pill = Task("Give pill", "meds", time(8, 0), priority=4, duration=5, pet=biscuit)
    # Different pets, same start time.
    groom = Task("Groom", "grooming", time(9, 0), priority=2, duration=40, pet=biscuit)
    vet = Task("Vet", "medical", time(9, 0), priority=4, duration=60, pet=mochi)

    scheduler = _scheduler_with([walk, pill, groom, vet])
    message = scheduler.check_time_conflicts()

    assert "WARNING" in message
    assert "same pet (Biscuit)" in message
    assert "different pets (Biscuit, Mochi)" in message

    # No-conflict case returns the friendly message and never raises.
    clear = _scheduler_with([Task("Feed", "feeding", time(12, 0), 3, 10)])
    assert clear.check_time_conflicts() == "No scheduling conflicts detected."


def test_check_time_conflicts_never_crashes_on_bad_input():
    """Conflict detection is lightweight/defensive: bad input yields a warning
    string, not an exception."""
    scheduler = _scheduler_with([])
    # Non-iterable argument: returns a message rather than raising.
    result = scheduler.check_time_conflicts(tasks=42)
    assert isinstance(result, str)
    assert "Could not check for conflicts" in result


def test_mark_complete_no_spawn_for_one_off_task():
    """Recurrence: a one-off (non-recurring) task does NOT spawn a next
    occurrence — mark_complete() returns None and the pet gains no new task."""
    pet = Pet("Mochi", "cat")
    groom = Task("Grooming", "grooming", time(14, 0), priority=2, duration=40)
    pet.add_task(groom)

    result = groom.mark_complete()

    assert result is None
    assert groom.completed is True
    assert pet.tasks == [groom]


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet should grow its task list by one."""
    pet = Pet("Biscuit", "dog")

    assert len(pet.tasks) == 0  # a new pet has no tasks

    task = Task("Dental work", "dental", time(9, 30), priority=4, duration=45)
    pet.add_task(task)

    assert len(pet.tasks) == 1


def test_sort_by_time_orders_chronologically():
    """Sorting: sort_by_time() returns tasks earliest-start first, timeless last."""
    late = Task("Evening walk", "walk", time(18, 0), priority=1, duration=30)
    early = Task("Morning walk", "walk", time(7, 0), priority=1, duration=30)
    timeless = Task("Refill water", "feeding", None, priority=1, duration=5)
    scheduler = _scheduler_with([late, timeless, early])

    ordered = scheduler.sort_by_time()

    assert ordered == [early, late, timeless]


def test_filter_tasks_by_pet_and_status():
    """Filtering: filter_tasks() narrows the pool by pet and completion status."""
    biscuit = Pet("Biscuit", "dog")
    mochi = Pet("Mochi", "cat")
    walk = Task("Walk", "walk", time(8, 0), priority=3, duration=30)
    litter = Task("Litter", "cleaning", time(9, 0), priority=2, duration=15)
    done_walk = Task("Old walk", "walk", time(7, 0), priority=3, duration=30, completed=True)
    biscuit.add_task(walk)
    biscuit.add_task(done_walk)
    mochi.add_task(litter)
    scheduler = _scheduler_with([walk, litter, done_walk])

    # Filter by pet (accepts a Pet object) and by not-yet-completed status.
    assert scheduler.filter_tasks(pet=biscuit) == [walk, done_walk]
    assert scheduler.filter_tasks(pet="Mochi") == [litter]
    assert scheduler.filter_tasks(completed=False) == [walk, litter]


def test_is_due_handles_recurrence_rules():
    """Recurring tasks: is_due() respects one-off, daily, and weekly rules."""
    one_off = Task("Vet visit", "medical", time(10, 0), priority=5, duration=60)
    daily = Task("Feed", "feeding", time(8, 0), priority=5, duration=10, recurrence="daily")
    weekly = Task("Bath", "grooming", time(11, 0), priority=2, duration=40, recurrence="weekly:tuesday")

    # One-off and daily tasks are due on any day.
    assert one_off.is_due("monday") is True
    assert daily.is_due("monday") is True
    # Weekly task is due only on its named day (weekday int 1 == Tuesday).
    assert weekly.is_due("tuesday") is True
    assert weekly.is_due(1) is True
    assert weekly.is_due("wednesday") is False


def test_build_plan_filters_recurring_tasks_by_weekday():
    """Recurring tasks: build_plan(weekday=...) only schedules tasks due that day."""
    daily = Task("Feed", "feeding", time(8, 0), priority=5, duration=10, recurrence="daily")
    tue = Task("Bath", "grooming", time(11, 0), priority=4, duration=40, recurrence="weekly:tuesday")
    scheduler = _scheduler_with([daily, tue])

    scheduler.build_plan(weekday="monday")

    assert daily in scheduler.scheduled_tasks
    assert tue not in scheduler.scheduled_tasks


def test_build_plan_skips_tasks_when_time_runs_out():
    """Time budget: build_plan() schedules tasks in priority order until the
    available time runs out, then skips the rest with a 'not enough time' reason
    (exercises the _schedule_or_skip_for_time helper)."""
    # 60-minute budget. Priority order: walk (5), dental (4), grooming (2).
    walk = Task("Walk", "walk", time(8, 0), priority=5, duration=30)
    dental = Task("Dental", "dental", time(9, 0), priority=4, duration=45)
    groom = Task("Groom", "grooming", time(14, 0), priority=2, duration=20)
    scheduler = _scheduler_with([walk, dental, groom], available_minutes=60)

    scheduler.build_plan()

    # walk (30) fits; dental (45) does not fit the remaining 30 and is skipped;
    # groom (20) still fits the leftover 30, so it slips in after dental.
    assert scheduler.scheduled_tasks == [walk, groom]
    assert dental in scheduler.skipped_tasks
    assert scheduler.skip_reasons[dental] == "not enough time remaining"


def test_detect_conflicts_flags_overlap():
    """Conflict detection: overlapping scheduled tasks are reported as conflicts."""
    a = Task("Walk", "walk", time(8, 0), priority=3, duration=60)   # 08:00-09:00
    b = Task("Feed", "feeding", time(8, 30), priority=3, duration=30)  # 08:30-09:00
    scheduler = _scheduler_with([a, b])

    # resolve_conflicts=False lets both stay scheduled so detect_conflicts sees them.
    scheduler.build_plan(resolve_conflicts=False)
    conflicts = scheduler.detect_conflicts()

    assert a in conflicts and b in conflicts
