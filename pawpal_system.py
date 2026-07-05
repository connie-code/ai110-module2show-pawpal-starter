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
  optional recurrence.
- ``Scheduler``: the engine that takes a collection of tasks along with owner
  and pet information, applies constraints (available time, priority,
  preferences), builds a plan, detects conflicts, and explains its decisions.

Relationships:
    Owner "1" --> "*" Pet    (an owner owns many pets)
    Pet   "1" --> "*" Task   (a pet has many tasks)
    Scheduler ..> Task/Owner/Pet (the scheduler reads these to build a plan)
"""

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
        time: str,
        priority: int,
        duration: int,
        recurrence: str = None,
    ) -> None:
        self.name: str = name
        self.task_type: str = task_type
        self.time: str = time
        self.priority: int = priority
        self.duration: int = duration
        self.recurrence: str = recurrence

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
        self.preferences: Dict = preferences if preferences is not None else {}
        self.scheduled_tasks: List["Task"] = []
        self.skipped_tasks: List["Task"] = []

    def add_task(self, task: "Task") -> None:
        """Add a task to the pool of tasks to be scheduled."""
        pass

    def apply_constraints(self) -> List["Task"]:
        """Filter/order tasks according to constraints and return the candidates."""
        pass

    def build_plan(self) -> List["Task"]:
        """Build and return the scheduled plan of tasks."""
        pass

    def detect_conflicts(self) -> List["Task"]:
        """Return tasks that conflict (e.g. overlapping times) within the plan."""
        pass

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the scheduling decisions."""
        pass
