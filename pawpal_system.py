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

from datetime import date, time, timedelta
from typing import Dict, List


def _minutes_since_midnight(t: "time") -> int:
    """Convert a datetime.time to minutes since midnight; a missing time returns
    a sentinel (end of day) so timeless tasks sort last."""
    if t is None:
        return 24 * 60
    return t.hour * 60 + t.minute


# Weekday names in datetime.weekday() order (Monday == 0), used to interpret
# weekly recurrence rules like "weekly:tuesday".
_WEEKDAY_NAMES = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
]


def _weekday_name(weekday) -> str:
    """Normalize a weekday given as an int (0=Monday..6=Sunday) or a name/string
    into a lowercase weekday name; None passes through as None."""
    if weekday is None:
        return None
    if isinstance(weekday, int):
        return _WEEKDAY_NAMES[weekday % 7]
    return str(weekday).strip().lower()


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

    def edit(self, updates: Dict) -> None:
        """Update owner attributes from an ``{attr: value}`` dict; unknown keys are
        ignored so a bad key can't create a stray attribute."""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)

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

    def remove_task(self, task: "Task") -> None:
        """Remove a task and clear its ``pet`` back-reference; a no-op if the task
        isn't attached to this pet."""
        if task in self.tasks:
            self.tasks.remove(task)
            task.pet = None

    def edit(self, updates: Dict) -> None:
        """Update pet attributes from an ``{attr: value}`` dict; unknown keys are
        ignored so a bad key can't create a stray attribute."""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)

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
        include_in_plan: bool = True,
        due_date: date = None,
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
        # Whether the user wants this task considered for today's plan. Lets them
        # toggle a task out of scheduling without deleting it; the Scheduler skips
        # tasks where this is False (see Scheduler.apply_constraints).
        self.include_in_plan: bool = include_in_plan
        # Calendar date this task is due (datetime.date). Defaults to today.
        # `time` is the time-of-day; `due_date` is the day. When a recurring task
        # is completed, next_occurrence() advances this date with timedelta
        # (+1 day for "daily", +7 days for "weekly").
        self.due_date: date = due_date if due_date is not None else date.today()

    def edit(self, updates: Dict) -> None:
        """Update task attributes from an ``{attr: value}`` dict; unknown keys are
        ignored so a bad key can't create a stray attribute."""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def is_recurring(self) -> bool:
        """Return True if this task repeats (has a recurrence rule)."""
        return bool(self.recurrence)

    def is_due(self, weekday=None) -> bool:
        """Return True if this task should appear in a plan for ``weekday``
        (an int 0=Monday..6=Sunday, or a weekday name, or None).

        Recurrence rules understood:
        - no recurrence (one-off): always due (assumed to be for today).
        - ``"daily"``: due every day.
        - ``"weekly:<day>"`` (e.g. ``"weekly:tuesday"``): due only on that day;
          if ``weekday`` is None the day can't be checked, so it's treated as due.
        - ``"weekly"`` with no day, or any unrecognized rule: treated as due so a
          task is never silently dropped from the plan."""
        if not self.is_recurring():
            return True
        rule = self.recurrence.strip().lower()
        if rule == "daily":
            return True
        if rule.startswith("weekly"):
            parts = rule.split(":", 1)
            target = parts[1].strip() if len(parts) == 2 else ""
            if not target or weekday is None:
                return True
            return _weekday_name(weekday) == target
        # Unknown rule: default to due rather than hiding the task.
        return True

    def _recurs_daily_or_weekly(self) -> bool:
        """Return True if this task repeats on a ``"daily"`` or ``"weekly"``
        schedule (the recurrences that auto-spawn a next occurrence)."""
        if not self.is_recurring():
            return False
        rule = self.recurrence.strip().lower()
        return rule == "daily" or rule.startswith("weekly")

    def _recurrence_interval(self) -> "timedelta":
        """Return how far ahead the next occurrence falls, as a timedelta:
        one day for ``"daily"`` and one week for ``"weekly"`` (including
        ``"weekly:<day>"``). Returns ``None`` for non-recurring tasks."""
        if not self._recurs_daily_or_weekly():
            return None
        rule = self.recurrence.strip().lower()
        return timedelta(days=1) if rule == "daily" else timedelta(weeks=1)

    def next_occurrence(self) -> "Task":
        """Return a fresh, NOT-completed copy of this task for its next
        occurrence, or ``None`` if this task doesn't recur daily/weekly.

        The copy keeps the same name, type, time, priority, duration,
        recurrence, and include_in_plan flag, but its ``due_date`` is advanced
        with ``timedelta`` from this task's due date — +1 day for ``"daily"``,
        +7 days for ``"weekly"`` (so a daily task due today becomes due
        tomorrow). It has no ``pet`` set yet — the caller (see ``mark_complete``)
        attaches it via ``Pet.add_task`` so the Pet <-> Task back-reference stays
        consistent."""
        interval = self._recurrence_interval()
        if interval is None:
            return None
        return Task(
            name=self.name,
            task_type=self.task_type,
            time=self.time,
            priority=self.priority,
            duration=self.duration,
            recurrence=self.recurrence,
            pet=None,
            end_time=self.end_time,
            completed=False,
            include_in_plan=self.include_in_plan,
            due_date=self.due_date + interval,
        )

    def mark_complete(self) -> "Task":
        """Mark this task as done. If it's a daily/weekly recurring task, also
        create a fresh instance for the next occurrence, attach it to the same
        pet, and return it — so a recurring chore never vanishes from the pet's
        task list once it's done. Returns the new task, or ``None`` for one-off
        (non-recurring) tasks."""
        self.completed = True
        upcoming = self.next_occurrence()
        if upcoming is not None and self.pet is not None:
            self.pet.add_task(upcoming)
        return upcoming


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

    def filter_tasks(
        self,
        pet=None,
        completed: bool = None,
        include_in_plan: bool = None,
        weekday=None,
        match: str = "all",
    ) -> List["Task"]:
        """Return tasks from the pool matching the given filters; a filter left
        as ``None`` is not applied. ``pet`` matches by ``Pet`` object or by pet
        name (string). ``completed`` / ``include_in_plan`` match those booleans.
        ``weekday`` keeps only tasks due that day (see ``Task.is_due``).

        ``match`` controls how multiple filters combine:
        - ``"all"`` (default): a task must satisfy EVERY given filter (AND).
        - ``"any"``: a task need satisfy only ONE given filter (OR), e.g.
          ``filter_tasks(pet="Mochi", completed=True, match="any")`` returns
          every Mochi task plus every completed task.
        With ``match="any"`` and no filters given, returns an empty list (no
        filter can match). Does not mutate ``self.tasks``."""
        if match not in ("all", "any"):
            raise ValueError("match must be 'all' or 'any'")

        wanted_pet = pet.name if isinstance(pet, Pet) else pet

        # Build one predicate per filter that was actually supplied, so "all"/
        # "any" only ever combine the filters the caller opted into.
        predicates = []
        if completed is not None:
            predicates.append(lambda task: task.completed == completed)
        if include_in_plan is not None:
            predicates.append(lambda task: task.include_in_plan == include_in_plan)
        if wanted_pet is not None:
            predicates.append(
                lambda task: (task.pet.name if task.pet else None) == wanted_pet
            )
        if weekday is not None:
            predicates.append(lambda task: task.is_due(weekday))

        # No filters supplied: "all" keeps everything, "any" matches nothing.
        if not predicates:
            return list(self.tasks) if match == "all" else []

        combine = all if match == "all" else any
        return [
            task for task in self.tasks
            if combine(predicate(task) for predicate in predicates)
        ]

    def sort_by_time(self, descending: bool = False) -> List["Task"]:
        """Return schedulable tasks ordered purely by start time (earliest first;
        pass ``descending=True`` for latest first). Timeless tasks sort last.
        Drops completed and toggled-out tasks. Does not mutate ``self.tasks``."""
        candidates = self.filter_tasks(completed=False, include_in_plan=True)
        candidates.sort(
            key=lambda task: _minutes_since_midnight(task.time),
            reverse=descending,
        )
        return candidates

    def apply_constraints(
        self,
        highest_priority_first: bool = True,
        weekday=None,
        pet=None,
    ) -> List["Task"]:
        """Return a new list of schedulable tasks ordered by priority (higher
        int = more important; pass ``highest_priority_first=False`` to reverse),
        ties broken by earlier start time. Drops completed tasks and tasks the
        user toggled out (include_in_plan=False). Optionally restrict to a single
        ``pet`` and to tasks due on ``weekday`` (recurrence-aware). Does not
        mutate ``self.tasks``."""
        candidates = self.filter_tasks(
            pet=pet, completed=False, include_in_plan=True, weekday=weekday,
        )
        candidates.sort(
            key=lambda task: (
                -task.priority if highest_priority_first else task.priority,
                _minutes_since_midnight(task.time),
            )
        )
        return candidates

    def _schedule_or_skip_for_time(self, task: "Task", remaining: int) -> int:
        """Time-budget helper: schedule ``task`` if it fits within ``remaining``
        minutes, otherwise skip it (recording "not enough time remaining").
        Returns the updated remaining minutes — unchanged when the task is
        skipped, reduced by ``task.duration`` when it's scheduled."""
        if task.duration <= remaining:
            self.scheduled_tasks.append(task)
            return remaining - task.duration
        self.skipped_tasks.append(task)
        self.skip_reasons[task] = "not enough time remaining"
        return remaining

    def build_plan(
        self,
        highest_priority_first: bool = True,
        resolve_conflicts: bool = True,
        weekday=None,
        pet=None,
    ) -> List["Task"]:
        """Greedily fill the plan in priority order against the ``available_minutes``
        budget (hard cutoff): fitting tasks go to ``scheduled_tasks``, the rest to
        ``skipped_tasks`` with a reason in ``skip_reasons``. When
        ``resolve_conflicts`` is True (default), a task overlapping one already
        scheduled is skipped (the earlier, higher-priority task wins); when False,
        overlaps stay in the plan for detect_conflicts() to flag. Pass ``weekday``
        to plan only recurring tasks due that day, and ``pet`` to plan for a single
        pet."""
        # Reset so the method can be re-run safely (e.g. after editing tasks).
        self.scheduled_tasks = []
        self.skipped_tasks = []
        self.skip_reasons = {}
        remaining = self.available_minutes
        for task in self.apply_constraints(highest_priority_first, weekday=weekday, pet=pet):
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
            else:
                # Schedule the task if it fits the remaining budget, else skip it
                # for lack of time (see _schedule_or_skip_for_time).
                remaining = self._schedule_or_skip_for_time(task, remaining)
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

    def check_time_conflicts(self, tasks: List["Task"] = None) -> str:
        """Lightweight conflict check: return a human-readable WARNING message
        for any tasks scheduled at the exact same start time — noting whether
        each clash is for the SAME pet or for DIFFERENT pets.

        This is deliberately defensive: it never raises. Bad or missing data
        (no ``time``, no ``pet``, a non-list argument) is skipped or handled
        gracefully so a caller can surface the warning instead of crashing.

        ``tasks`` defaults to the current plan (``scheduled_tasks``) if one has
        been built, otherwise the schedulable pool. Returns a friendly
        "no conflicts" message when nothing clashes."""
        try:
            if tasks is None:
                tasks = self.scheduled_tasks or self.filter_tasks(
                    completed=False, include_in_plan=True,
                )

            # Group tasks by their exact start time; skip timeless tasks since
            # "no time" can't collide with anything.
            by_start: Dict["time", List["Task"]] = {}
            for task in tasks:
                start = getattr(task, "time", None)
                if start is None:
                    continue
                by_start.setdefault(start, []).append(task)

            # Keep only the time slots that hold more than one task, earliest
            # first, so the warning reads top-to-bottom through the day.
            clashes = sorted(
                (slot for slot in by_start.items() if len(slot[1]) > 1),
                key=lambda slot: _minutes_since_midnight(slot[0]),
            )
            if not clashes:
                return "No scheduling conflicts detected."

            def pet_name(task: "Task") -> str:
                pet = getattr(task, "pet", None)
                return pet.name if pet is not None else "unassigned"

            lines = [f"WARNING: found {len(clashes)} time conflict(s):"]
            for start, slot_tasks in clashes:
                stamp = start.strftime("%H:%M")
                names = ", ".join(f"'{t.name}'" for t in slot_tasks)
                # Same pet vs. different pets: the count of distinct pet names in
                # the slot tells us which case we're in. (Two unassigned tasks
                # share the name "unassigned", so they read as "same pet
                # (unassigned)" — a reasonable, non-crashing default.)
                pets = {pet_name(t) for t in slot_tasks}
                if len(pets) == 1:
                    scope = f"same pet ({next(iter(pets))})"
                else:
                    scope = f"different pets ({', '.join(sorted(pets))})"
                lines.append(f"  - {stamp}: {names} overlap — {scope}.")
            return "\n".join(lines)
        except Exception as exc:  # never let conflict-checking crash the caller
            return f"Could not check for conflicts ({exc})."

    def conflict_details(self, tasks: List["Task"] = None) -> List[Dict]:
        """Return a structured list of timing conflicts among ``tasks`` (defaults
        to the current plan, ``scheduled_tasks``), so a UI can present each clash
        in its own way instead of parsing the ``check_time_conflicts`` string.

        Each entry describes one overlapping PAIR of tasks, earliest first::

            {
                "earlier": Task,   # the task that starts first (or higher priority
                                   #   on a tie) — the one worth keeping put
                "later": Task,     # the task that starts later — the natural one
                                   #   to nudge to resolve the clash
                "same_pet": bool,  # True if both tasks belong to the same pet
                "pets": [str],     # distinct pet name(s) involved, sorted
            }

        A same-pet clash is physically impossible (one animal, two places at
        once); a different-pet clash is only a heads-up. Timeless tasks never
        conflict. Run ``build_plan()`` first, or pass ``tasks`` explicitly."""
        if tasks is None:
            tasks = self.scheduled_tasks
        timed = [t for t in tasks if t.time is not None]
        # Sort so the earlier-starting task is 'a'; ties go to higher priority.
        timed.sort(key=lambda t: (_minutes_since_midnight(t.time), -t.priority))

        details: List[Dict] = []
        for i, a in enumerate(timed):
            for b in timed[i + 1:]:
                if not _tasks_overlap(a, b):
                    continue
                pet_a = a.pet.name if a.pet else "unassigned"
                pet_b = b.pet.name if b.pet else "unassigned"
                details.append(
                    {
                        "earlier": a,
                        "later": b,
                        "same_pet": pet_a == pet_b,
                        "pets": sorted({pet_a, pet_b}),
                    }
                )
        return details

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

        # Lightweight same-start-time warning (same/different pet). Only shown
        # when something actually clashes, so a clean plan stays uncluttered.
        warning = self.check_time_conflicts()
        if warning != "No scheduling conflicts detected.":
            lines += ["", warning]
        return "\n".join(lines)
