"""PawPal+ demo script.

Builds a small sample world (one owner, two pets, several care tasks), runs the
Scheduler, and prints "Today's Schedule" to the terminal so you can see the
system working end-to-end without the Streamlit UI.

Run with:
    python3 main.py
"""

from datetime import time

from pawpal_system import Owner, Pet, Task, Scheduler


def _print_task(task: "Task") -> None:
    """Print a one-line summary of a task for the demo output."""
    start = task.time.strftime("%H:%M") if task.time else "--:--"
    pet_name = task.pet.name if task.pet else "unassigned"
    status = "done" if task.completed else "todo"
    print(
        f"  {start}  {task.name} ({pet_name}) "
        f"[priority {task.priority}, {task.duration} min, {status}]"
    )


def main() -> None:
    # 1. Create an owner.
    owner = Owner(
        first_name="Jane",
        last_name="Smith",
        address="123 Puppy Lane",
        preferences={"preferred_walk_time": "morning"},
    )

    # 2. Create at least two pets and attach them to the owner.
    biscuit = Pet(name="Biscuit", species="dog")
    mochi = Pet(name="Mochi", species="cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # 3. Add tasks to the pets, deliberately OUT OF TIME ORDER, so the sorting
    #    method below has real work to do. (priority: higher integer = more
    #    important.) One task is pre-marked complete to show off filtering.
    biscuit.add_task(
        Task("Grooming", "grooming", time(14, 0), priority=2, duration=40)
    )
    biscuit.add_task(
        Task("Morning walk", "walk", time(8, 0), priority=5, duration=30)
    )
    mochi.add_task(
        Task("Litter cleaning", "cleaning", time(11, 0), priority=3, duration=15)
    )
    biscuit.add_task(
        Task("Dental work", "dental", time(9, 30), priority=4, duration=45,
             completed=True)
    )
    mochi.add_task(
        Task("Evening feeding", "feeding", time(18, 0), priority=4, duration=10)
    )
    # Deliberate CONFLICT: another task for Mochi at 11:00, the same start time
    # as "Litter cleaning" above, so the scheduler's conflict check has a
    # same-time clash to warn about.
    mochi.add_task(
        Task("Medication", "meds", time(11, 0), priority=4, duration=5)
    )

    # 4. Load the tasks into the scheduler.
    scheduler = Scheduler(available_minutes=180, preferences=owner.preferences)
    scheduler.load_tasks_from_owner(owner)

    # 5. Show the tasks in the ORDER THEY WERE ADDED (unsorted) so the effect of
    #    sort_by_time() is visible.
    print(f"Today's Schedule for {owner.first_name} {owner.last_name}")
    print("=" * 40)
    print("\nTasks as added (unsorted):")
    for task in scheduler.tasks:
        _print_task(task)

    # 6. Sorting: sort_by_time() returns schedulable tasks earliest-first
    #    (completed tasks are dropped automatically).
    print("\nSorted by time (earliest first):")
    for task in scheduler.sort_by_time():
        _print_task(task)

    print("\nSorted by time (latest first):")
    for task in scheduler.sort_by_time(descending=True):
        _print_task(task)

    # 7. Filtering: by pet name, by completion status, and the OR ("any") mode.
    print("\nFilter by pet name 'Mochi':")
    for task in scheduler.filter_tasks(pet="Mochi"):
        _print_task(task)

    print("\nFilter by completion status (completed only):")
    for task in scheduler.filter_tasks(completed=True):
        _print_task(task)

    print("\nFilter (OR): Mochi's tasks OR any completed task:")
    for task in scheduler.filter_tasks(pet="Mochi", completed=True, match="any"):
        _print_task(task)

    # 8. Conflict detection: "Litter cleaning" and "Medication" are both at
    #    11:00, so the lightweight check should print a same-time warning. We run
    #    it on the task pool BEFORE build_plan() resolves the clash by skipping
    #    the lower-priority task.
    print("\nConflict check (before planning):")
    print(scheduler.check_time_conflicts())

    # 9. Finally, build and print the full plan. build_plan() resolves the 11:00
    #    clash by keeping the higher-priority task and skipping the other.
    scheduler.build_plan()
    print()
    print(scheduler.explain_plan())


def tight_budget_demo() -> None:
    """Show tasks being skipped when the time budget is too small to fit them all.

    Same tasks as the main demo, but the scheduler only has 60 available minutes,
    so the lower-priority tasks get pushed into "Skipped".
    """
    owner = Owner("Jane", "Smith", "123 Puppy Lane")
    biscuit = Pet(name="Biscuit", species="dog")
    mochi = Pet(name="Mochi", species="cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    biscuit.add_task(Task("Morning walk", "walk", time(8, 0), priority=5, duration=30))
    biscuit.add_task(Task("Dental work", "dental", time(9, 30), priority=4, duration=45))
    mochi.add_task(Task("Litter cleaning", "cleaning", time(11, 0), priority=3, duration=15))
    mochi.add_task(Task("Grooming", "grooming", time(14, 0), priority=2, duration=40))

    # Only 60 minutes available -> not everything fits.
    scheduler = Scheduler(available_minutes=60)
    scheduler.load_tasks_from_owner(owner)
    scheduler.build_plan()

    print(f"Today's Schedule for {owner.first_name} {owner.last_name} (tight budget)")
    print("=" * 40)
    print(scheduler.explain_plan())


def conflict_demo() -> None:
    """Show a time-slot conflict when two scheduled tasks overlap.

    The walk (8:00-8:30) and the vet visit (8:15-9:00) overlap, so both appear
    under "Conflicts" in the printed schedule.
    """
    owner = Owner("Jane", "Smith", "123 Puppy Lane")
    biscuit = Pet(name="Biscuit", species="dog")
    mochi = Pet(name="Mochi", species="cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # These two start times overlap on purpose.
    biscuit.add_task(Task("Morning walk", "walk", time(8, 0), priority=5, duration=30))
    mochi.add_task(Task("Vet visit", "medical", time(8, 15), priority=5, duration=45))

    # Plenty of time so nothing is skipped -- the point here is the overlap.
    # resolve_conflicts=False keeps both tasks in the plan and flags the overlap
    # under "Conflicts" instead of skipping the lower-priority one.
    scheduler = Scheduler(available_minutes=180)
    scheduler.load_tasks_from_owner(owner)
    scheduler.build_plan(resolve_conflicts=False)

    print(f"Today's Schedule for {owner.first_name} {owner.last_name} (overlapping tasks)")
    print("=" * 40)
    print(scheduler.explain_plan())


def recurring_demo() -> None:
    """Show recurring tasks re-spawning when marked complete.

    A daily walk and a weekly vet visit are completed; each automatically
    creates a fresh, not-yet-done instance for its next occurrence, while a
    one-off grooming task simply stays done and does not repeat.
    """
    biscuit = Pet(name="Biscuit", species="dog")

    walk = Task("Morning walk", "walk", time(8, 0), priority=5, duration=30,
                recurrence="daily")
    vet = Task("Vet checkup", "medical", time(10, 0), priority=4, duration=60,
               recurrence="weekly:tuesday")
    groom = Task("Grooming", "grooming", time(14, 0), priority=2, duration=40)
    for task in (walk, vet, groom):
        biscuit.add_task(task)

    print(f"Recurring-task demo for {biscuit.name}")
    print("=" * 40)
    print("\nBefore completing anything:")
    for task in biscuit.tasks:
        _print_task(task)

    # Complete each task; recurring ones spawn their next occurrence.
    for task in (walk, vet, groom):
        spawned = task.mark_complete()
        if spawned is not None:
            print(f"\n'{task.name}' completed -> spawned next occurrence "
                  f"({spawned.recurrence}).")
        else:
            print(f"\n'{task.name}' completed -> one-off, no repeat.")

    print("\nAfter completing all three:")
    for task in biscuit.tasks:
        _print_task(task)


def time_conflict_demo() -> None:
    """Show the lightweight same-start-time conflict warning.

    Two tasks for the SAME pet and two tasks for DIFFERENT pets are scheduled
    at identical start times, so check_time_conflicts() flags both cases without
    crashing.
    """
    owner = Owner("Jane", "Smith", "123 Puppy Lane")
    biscuit = Pet(name="Biscuit", species="dog")
    mochi = Pet(name="Mochi", species="cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # Same pet, same 08:00 start.
    biscuit.add_task(Task("Morning walk", "walk", time(8, 0), priority=5, duration=30))
    biscuit.add_task(Task("Give pill", "meds", time(8, 0), priority=4, duration=5))
    # Different pets, same 09:00 start.
    biscuit.add_task(Task("Grooming", "grooming", time(9, 0), priority=2, duration=40))
    mochi.add_task(Task("Vet checkup", "medical", time(9, 0), priority=4, duration=60))

    scheduler = Scheduler(available_minutes=180)
    scheduler.load_tasks_from_owner(owner)

    print(f"Time-conflict demo for {owner.first_name} {owner.last_name}")
    print("=" * 40)
    # Lightweight check on the task pool (no plan needed) -- returns a warning
    # string rather than raising.
    print(scheduler.check_time_conflicts())


if __name__ == "__main__":
    main()
    print()
    tight_budget_demo()
    print()
    conflict_demo()
    print()
    recurring_demo()
    print()
    time_conflict_demo()
