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
        """Add a pet to this owner's list of pets."""
        pass

    def remove_pet(self, pet: "Pet") -> None:
        """Remove a pet from this owner's list of pets."""
        pass

    def list_pets(self) -> List["Pet"]:
        """Return the list of pets belonging to this owner."""
        pass


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
        """Attach a care task to this pet."""
        pass

    def add_medical_record(self, record: str) -> None:
        """Add a record to this pet's medical history."""
        pass

    def list_tasks(self) -> List["Task"]:
        """Return the list of tasks associated with this pet."""
        pass


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

    def edit(self, updates: Dict) -> None:
        """Update one or more attributes of this task from a dict of changes."""
        pass

    def is_recurring(self) -> bool:
        """Return True if this task repeats (has a recurrence rule)."""
        pass


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

    def add_task(self, task: "Task") -> None:
        """Add a task to the pool of tasks to be scheduled."""
        pass

    def load_tasks_from_pet(self, pet: "Pet") -> None:
        """Load all of a single pet's tasks into the scheduler's task pool."""
        pass

    def load_tasks_from_owner(self, owner: "Owner") -> None:
        """Load tasks from every pet the owner has, and adopt the owner's preferences.

        Walks owner -> pets -> tasks so a page can populate the scheduler from a
        single owner. This realizes the ``Scheduler ..> Owner/Pet`` relationship.
        """
        pass

    def apply_constraints(self) -> List["Task"]:
        """Filter/order tasks according to constraints and return the candidates."""
        pass

    def build_plan(self) -> List["Task"]:
        """Build and return the scheduled plan of tasks."""
        pass

    def detect_conflicts(self) -> List["Task"]:
        """Return tasks that conflict (e.g. overlapping time slots) within the plan."""
        pass

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the scheduling decisions."""
        pass
