"""PawPal+ — a pet-care task scheduling system.

This module models the core domain of PawPal+, an application that helps pet
owners organize and schedule care tasks (walks, feedings, vet appointments,
grooming, etc.) for their pets.

The design follows the UML class diagram in ``diagrams/uml.mmd`` and is built
around four classes:

- ``Owner``: a pet owner, holding their contact info, the pets they own, and
  their scheduling preferences.
- ``Pet``: a single pet, holding its details, medical history, and the care
  tasks associated with it.
- ``Task``: a single unit of pet care, with a time, priority, duration, and
  optional recurrence. Each task knows which ``Pet`` it belongs to.
- ``Scheduler``: the engine that takes a collection of tasks along with owner
  and pet information, applies constraints (available time, priority,
  preferences), builds a plan, detects conflicts, and explains its decisions.

Relationships:
    Owner "1" --> "*" Pet     (an owner owns many pets)
    Pet   "1" --> "*" Task     (a pet has many tasks)
    Task  "*" --> "1" Pet      (each task is assigned to one pet)
    Scheduler ..> Task/Owner/Pet (the scheduler reads these to build a plan)
"""

from datetime import time
from typing import Dict, List


def _minutes_since_midnight(t: "time") -> int:
    """Convert a datetime.time to minutes since midnight; a missing time returns
    a sentinel (end of day) so timeless tasks sort last."""
    if t is None:
        return 24 * 60
    return t.hour * 60 + t.minute


def _tasks_overlap(a: "Task", b: "Task") -> bool:
    """Return True if two tasks' [start, start + duration) slots overlap; tasks
    without a start ``time`` never overlap."""
    if a.time is None or b.time is None:
        return False
    a_start = _minutes_since_midnight(a.time)
    b_start = _minutes_since_midnight(b.time)
    return a_start < b_start + b.duration and b_start < a_start + a.duration


class Owner:
    """A pet owner and the pets and preferences associated with them."""

    def __init__(
        self,
        first_name: str,
        last_name: str,
        address: str,
        preferences: Dict = None,
    ) -> None:
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.address: str = address
        self.pets: List["Pet"] = []
        # Owner.preferences: the owner's PERSISTENT, personal scheduling wishes
        # (e.g. {"no_tasks_before": "07:00", "preferred_walk_time": "morning"}).
        # This is part of the owner's saved profile and outlives any single plan.
        # The Scheduler reads a copy of these when it builds a plan.
        self.preferences: Dict = preferences if preferences is not None else {}

    def add_pet(self, pet: "Pet") -> None:
        """Add a pet (skipping duplicates) and set its ``owner`` back-reference
        so the Owner <-> Pet link stays consistent both ways."""
        if pet not in self.pets:
            self.pets.append(pet)
            pet.owner = self

    def remove_pet(self, pet: "Pet") -> None:
        """Remove a pet and clear its ``owner`` back-reference; a no-op if the
        pet isn't owned by this owner."""
        if pet in self.pets:
            self.pets.remove(pet)
            pet.owner = None

    def list_pets(self) -> List["Pet"]:
        """Return the list of pets belonging to this owner."""
        return self.pets

    def list_all_tasks(self) -> List["Task"]:
        """Return every task across all the owner's pets, flattening each pet's
        ``tasks`` into one combined list (handy for feeding the Scheduler)."""
        all_tasks: List["Task"] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


class Pet:
    """A pet, including its details, medical history, and care tasks."""

    def __init__(
        self,
        name: str,
        species: str,
        owner: "Owner" = None,
    ) -> None:
        self.name: str = name
        self.species: str = species
        self.owner: "Owner" = owner
        self.medical_history: List[str] = []
        self.tasks: List["Task"] = []

    def add_task(self, task: "Task") -> None:
        """Attach a task (skipping duplicates) and set its ``pet`` back-reference
        so the Pet <-> Task link stays consistent both ways."""
        if task not in self.tasks:
            self.tasks.append(task)
            task.pet = self

    def add_medical_record(self, record: str) -> None:
        """Add a record to this pet's medical history."""
        self.medical_history.append(record)

    def list_tasks(self) -> List["Task"]:
        """Return the list of tasks associated with this pet."""
        return self.tasks


class Task:
    """A single pet-care task with timing, priority, and recurrence info."""

    def __init__(
        self,
        name: str,
        task_type: str,
        time: time,
        priority: int,
        duration: int,
        recurrence: str = None,
        pet: "Pet" = None,
        end_time: time = None,
        completed: bool = False,
    ) -> None:
        self.name: str = name
        self.task_type: str = task_type
        self.time: time = time  # start time of the task (datetime.time)
        self.priority: int = priority
        self.duration: int = duration  # length of the task in minutes
        self.recurrence: str = recurrence
        # Back-reference to the Pet this task is assigned to, so a task always
        # knows which pet it belongs to (mirrors Pet.tasks in the other direction).
        self.pet: "Pet" = pet
        # End time of the task (datetime.time). May be provided directly or
        # computed from `time` + `duration` when the logic is implemented.
        self.end_time: time = end_time
        # Completion status: marks whether this task has been done (True) or not
        # (False). This matters for the scheduler too — a daily plan usually
        # shouldn't re-schedule tasks that are already completed.
        self.completed: bool = completed

    def edit(self, updates: Dict) -> None:
        """Update task attributes from an ``{attr: value}`` dict; unknown keys are
        ignored so a bad key can't create a stray attribute."""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def is_recurring(self) -> bool:
        """Return True if this task repeats (has a recurrence rule)."""
        return bool(self.recurrence)

    def mark_complete(self) -> None:
        """Mark this task as done by setting its completion status to True."""
        self.completed = True


class Scheduler:
    """Builds a care plan from tasks, subject to time and preference constraints."""

    def __init__(
        self,
        available_minutes: int,
        preferences: Dict = None,
    ) -> None:
        self.tasks: List["Task"] = []
        self.available_minutes: int = available_minutes
        # Scheduler.preferences: the ACTIVE preferences applied to THIS planning
        # run. Usually loaded/copied from an Owner (see load_tasks_from_owner),
        # but kept separately so a single planning session can be tweaked or
        # overridden without mutating the owner's saved profile.
        self.preferences: Dict = preferences if preferences is not None else {}
        self.scheduled_tasks: List["Task"] = []
        self.skipped_tasks: List["Task"] = []
        # Maps a skipped task -> the reason it was skipped (budget vs. conflict),
        # so explain_plan() can tell the user why each task didn't make the plan.
        self.skip_reasons: Dict["Task", str] = {}

    def add_task(self, task: "Task") -> None:
        """Add a task to the pool of tasks to be scheduled."""
        self.tasks.append(task)

    def load_tasks_from_pet(self, pet: "Pet") -> None:
        """Load all of a single pet's tasks into the scheduler's task pool."""
        for task in pet.tasks:
            self.add_task(task)

    def load_tasks_from_owner(self, owner: "Owner") -> None:
        """Load every pet's tasks (via ``owner.list_all_tasks``) and adopt a COPY
        of the owner's preferences so this run can't mutate the saved profile."""
        # Ask the owner for its tasks rather than reaching into its pets directly,
        # so the pet-traversal logic lives in one place (Owner.list_all_tasks).
        for task in owner.list_all_tasks():
            self.add_task(task)
        # Adopt a COPY of the owner's preferences so tweaking this planning run
        # never mutates the owner's saved profile.
        self.preferences = dict(owner.preferences)

    def apply_constraints(self, highest_priority_first: bool = True) -> List["Task"]:
        """Return a new list of non-completed tasks ordered by priority (higher
        int = more important; pass ``highest_priority_first=False`` to reverse),
        ties broken by earlier start time. Does not mutate ``self.tasks``."""
        candidates = [task for task in self.tasks if not task.completed]
        candidates.sort(
            key=lambda task: (
                -task.priority if highest_priority_first else task.priority,
                _minutes_since_midnight(task.time),
            )
        )
        return candidates

    def build_plan(
        self,
        highest_priority_first: bool = True,
        resolve_conflicts: bool = True,
    ) -> List["Task"]:
        """Greedily fill the plan in priority order against the ``available_minutes``
        budget (hard cutoff): fitting tasks go to ``scheduled_tasks``, the rest to
        ``skipped_tasks`` with a reason in ``skip_reasons``. When
        ``resolve_conflicts`` is True (default), a task overlapping one already
        scheduled is skipped (the earlier, higher-priority task wins); when False,
        overlaps stay in the plan for detect_conflicts() to flag."""
        # Reset so the method can be re-run safely (e.g. after editing tasks).
        self.scheduled_tasks = []
        self.skipped_tasks = []
        self.skip_reasons = {}
        remaining = self.available_minutes
        for task in self.apply_constraints(highest_priority_first):
            # Find the first already-scheduled task this one overlaps (if any).
            clash = None
            if resolve_conflicts:
                clash = next(
                    (s for s in self.scheduled_tasks if _tasks_overlap(task, s)),
                    None,
                )

            if clash is not None:
                self.skipped_tasks.append(task)
                self.skip_reasons[task] = (
                    f"overlaps '{clash.name}' (kept the higher-priority task)"
                )
            elif task.duration <= remaining:
                self.scheduled_tasks.append(task)
                remaining -= task.duration
            else:
                self.skipped_tasks.append(task)
                self.skip_reasons[task] = "not enough time remaining"
        return self.scheduled_tasks

    def detect_conflicts(self) -> List["Task"]:
        """Return scheduled tasks whose ``[start, start + duration)`` slots overlap
        (timeless tasks ignored). Run build_plan() first."""
        timed = [task for task in self.scheduled_tasks if task.time is not None]
        conflicting: List["Task"] = []
        for i, a in enumerate(timed):
            for b in timed[i + 1:]:
                if _tasks_overlap(a, b):
                    if a not in conflicting:
                        conflicting.append(a)
                    if b not in conflicting:
                        conflicting.append(b)
        return conflicting

    def explain_plan(self) -> str:
        """Return a human-readable summary of the current plan: time budget,
        scheduled tasks, skipped tasks (with reasons), and conflicts. Run
        build_plan() first."""
        def describe(task: "Task") -> str:
            start = task.time.strftime("%H:%M") if task.time else "--:--"
            pet_name = task.pet.name if task.pet else "unassigned"
            return (
                f"{start}  {task.name} ({pet_name}) "
                f"[priority {task.priority}, {task.duration} min]"
            )

        used = sum(task.duration for task in self.scheduled_tasks)
        free = self.available_minutes - used
        lines = [
            "Daily Care Plan",
            "===============",
            (
                f"Time budget: {self.available_minutes} min available, "
                f"{used} min scheduled, {free} min free."
            ),
            "",
            f"Scheduled ({len(self.scheduled_tasks)}):",
        ]
        lines += (
            [f"  - {describe(task)}" for task in self.scheduled_tasks]
            or ["  (none)"]
        )

        lines += ["", f"Skipped ({len(self.skipped_tasks)}):"]
        lines += (
            [
                f"  - {describe(task)} — "
                f"{self.skip_reasons.get(task, 'not scheduled')}"
                for task in self.skipped_tasks
            ]
            or ["  (none)"]
        )

        conflicts = self.detect_conflicts()
        if conflicts:
            lines += ["", f"Conflicts ({len(conflicts)}):"]
            lines += [
                f"  - {describe(task)} overlaps another scheduled task"
                for task in conflicts
            ]
        return "\n".join(lines)
