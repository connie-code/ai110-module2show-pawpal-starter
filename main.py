"""PawPal+ demo script.

Builds a small sample world (one owner, two pets, several care tasks), runs the
Scheduler, and prints "Today's Schedule" to the terminal so you can see the
system working end-to-end without the Streamlit UI.

Run with:
    python3 main.py
"""

from datetime import time

from pawpal_system import Owner, Pet, Task, Scheduler


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

    # 3. Add tasks with different times to the pets.
    #    (priority: higher integer = more important)
    biscuit.add_task(
        Task("Morning walk", "walk", time(8, 0), priority=5, duration=30)
    )
    biscuit.add_task(
        Task("Dental work", "dental", time(9, 30), priority=4, duration=45)
    )
    mochi.add_task(
        Task("Litter cleaning", "cleaning", time(11, 0), priority=3, duration=15)
    )
    mochi.add_task(
        Task("Grooming", "grooming", time(14, 0), priority=2, duration=40)
    )

    # 4. Run the scheduler for the day and print the plan.
    scheduler = Scheduler(available_minutes=180, preferences=owner.preferences)
    scheduler.load_tasks_from_owner(owner)
    scheduler.build_plan()

    print(f"Today's Schedule for {owner.first_name} {owner.last_name}")
    print("=" * 40)
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


if __name__ == "__main__":
    main()
    print()
    tight_budget_demo()
    print()
    conflict_demo()
