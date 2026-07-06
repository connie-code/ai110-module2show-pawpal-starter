from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# Map the friendly priority labels to the integer priorities the scheduler uses
# (higher integer = more important), and back again for pre-filling edit forms.
PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}
PRIORITY_LABELS = ["low", "medium", "high"]
PRIORITY_TO_LABEL = {1: "low", 2: "medium", 3: "high"}
SPECIES = ["dog", "cat", "other"]
TASK_TYPES = ["walk", "feeding", "medical", "grooming", "cleaning", "enrichment", "other"]
# Recurrence options offered in the UI, mapped to the rule strings the scheduler
# understands (see Task.is_due). "one-off" means no recurrence at all.
RECURRENCE_LABELS = [
    "one-off", "daily",
    "weekly:monday", "weekly:tuesday", "weekly:wednesday", "weekly:thursday",
    "weekly:friday", "weekly:saturday", "weekly:sunday",
]
WEEKDAYS = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
]


def _recurrence_from_label(label):
    """Turn a UI recurrence label into the Task.recurrence value (None for one-off)."""
    return None if label == "one-off" else label


def _label_from_recurrence(recurrence):
    """Turn a Task.recurrence value back into its UI label (for edit forms)."""
    return recurrence if recurrence else "one-off"


def _index_of(options, value, default=0):
    """Return the position of value in options, or a default if it's not present.

    Keeps selectboxes from crashing when an object's current value isn't one of
    the listed options (e.g. a custom species).
    """
    return options.index(value) if value in options else default

# ---------------------------------------------------------------------------
# Owner: create the Owner once and keep it in the session "vault" so the pets
# and tasks we attach to it survive across Streamlit reruns.
# ---------------------------------------------------------------------------
st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(first_name=owner_name, last_name="", address="")

owner = st.session_state.owner
# Keep the stored owner's name in sync with the input box on every rerun.
owner.edit({"first_name": owner_name})

# ---------------------------------------------------------------------------
# Pets: add pets to the persistent owner.
# ---------------------------------------------------------------------------
st.subheader("Pets")
col_p1, col_p2 = st.columns(2)
with col_p1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with col_p2:
    new_species = st.selectbox("Species", SPECIES)

if st.button("Add pet"):
    if new_pet_name.strip():
        owner.add_pet(Pet(name=new_pet_name.strip(), species=new_species))
        st.success(f"Added {new_pet_name} to {owner.first_name}'s pets.")
    else:
        st.warning("Please enter a pet name.")

pets = owner.list_pets()
if pets:
    st.caption("Manage pets (deleting a pet also removes its tasks):")
    for i, pet in enumerate(pets):
        with st.expander(f"{pet.name} ({pet.species})"):
            edit_name = st.text_input("Name", value=pet.name, key=f"pet_name_{i}")
            edit_species = st.selectbox(
                "Species", SPECIES, index=_index_of(SPECIES, pet.species, 2),
                key=f"pet_species_{i}",
            )
            save_col, del_col = st.columns(2)
            with save_col:
                if st.button("Save changes", key=f"pet_save_{i}"):
                    pet.edit(
                        {
                            "name": edit_name.strip() or pet.name,
                            "species": edit_species,
                        }
                    )
                    st.rerun()
            with del_col:
                if st.button("Delete pet", key=f"pet_delete_{i}"):
                    owner.remove_pet(pet)
                    st.rerun()
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Tasks: add care tasks to a chosen pet.
# ---------------------------------------------------------------------------
st.subheader("Tasks")

if pets:
    selected_pet_name = st.selectbox("Assign task to pet", [p.name for p in pets])
    selected_pet = next(p for p in pets if p.name == selected_pet_name)

    col1, col2 = st.columns(2)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
        task_type = st.selectbox("Task type", TASK_TYPES)
    with col2:
        start_time = st.time_input("Start time", value=time(8, 0))
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    priority_label = st.selectbox("Priority", PRIORITY_LABELS, index=2)
    recurrence_label = st.selectbox("Repeats", RECURRENCE_LABELS, index=0)

    if st.button("Add task"):
        selected_pet.add_task(
            Task(
                name=task_title,
                task_type=task_type,
                time=start_time,
                priority=PRIORITY_MAP[priority_label],
                duration=int(duration),
                recurrence=_recurrence_from_label(recurrence_label),
            )
        )
        st.success(f"Added '{task_title}' to {selected_pet.name}.")

    all_tasks = owner.list_all_tasks()
    if all_tasks:
        st.caption("Manage tasks (edit any field, mark done, or delete):")
        for i, t in enumerate(all_tasks):
            label_time = t.time.strftime("%H:%M") if t.time else "--:--"
            done_mark = "✅ " if t.completed else ""
            excluded_mark = "" if t.include_in_plan else "🚫 "
            pet_label = t.pet.name if t.pet else "-"
            with st.expander(f"{excluded_mark}{done_mark}{label_time}  {t.name} ({pet_label})"):
                e1, e2 = st.columns(2)
                with e1:
                    edit_title = st.text_input("Title", value=t.name, key=f"task_title_{i}")
                    edit_type = st.selectbox(
                        "Type", TASK_TYPES, index=_index_of(TASK_TYPES, t.task_type, len(TASK_TYPES) - 1),
                        key=f"task_type_{i}",
                    )
                with e2:
                    edit_time = st.time_input(
                        "Start time", value=t.time or time(8, 0), key=f"task_time_{i}"
                    )
                    edit_duration = st.number_input(
                        "Duration (minutes)", min_value=1, max_value=240,
                        value=t.duration, key=f"task_dur_{i}",
                    )
                edit_priority = st.selectbox(
                    "Priority", PRIORITY_LABELS,
                    index=_index_of(PRIORITY_LABELS, PRIORITY_TO_LABEL.get(t.priority, "high"), 2),
                    key=f"task_prio_{i}",
                )
                edit_recurrence = st.selectbox(
                    "Repeats", RECURRENCE_LABELS,
                    index=_index_of(RECURRENCE_LABELS, _label_from_recurrence(t.recurrence), 0),
                    key=f"task_recur_{i}",
                )
                edit_done = st.checkbox("Completed", value=t.completed, key=f"task_done_{i}")

                # Instant toggle: applies immediately (no Save needed) so the user
                # can flip a task in/out of today's plan quickly.
                include = st.toggle(
                    "Include in today's plan", value=t.include_in_plan,
                    key=f"task_include_{i}",
                )
                if include != t.include_in_plan:
                    t.edit({"include_in_plan": include})
                    st.rerun()

                save_col, del_col = st.columns(2)
                with save_col:
                    if st.button("Save changes", key=f"task_save_{i}"):
                        t.edit(
                            {
                                "name": edit_title.strip() or t.name,
                                "task_type": edit_type,
                                "time": edit_time,
                                "duration": int(edit_duration),
                                "priority": PRIORITY_MAP[edit_priority],
                                "recurrence": _recurrence_from_label(edit_recurrence),
                                "completed": edit_done,
                            }
                        )
                        st.rerun()
                with del_col:
                    if st.button("Delete task", key=f"task_delete_{i}"):
                        if t.pet:
                            t.pet.remove_task(t)
                        st.rerun()
    else:
        st.info("No tasks yet. Add one above.")
else:
    st.info("Add a pet first, then you can add tasks for it.")

st.divider()

# ---------------------------------------------------------------------------
# Build Schedule: run the Scheduler over the owner's tasks and show the plan.
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

col_s1, col_s2 = st.columns(2)
with col_s1:
    available_minutes = st.number_input(
        "Available minutes for the day", min_value=1, max_value=1440, value=180
    )
with col_s2:
    highest_first = st.checkbox("Highest priority first", value=True)
resolve_conflicts = st.checkbox(
    "Resolve time conflicts (skip overlapping lower-priority tasks)", value=True
)

col_f1, col_f2 = st.columns(2)
with col_f1:
    day_label = st.selectbox("Plan for day", ["any day"] + WEEKDAYS)
with col_f2:
    pet_filter_label = st.selectbox(
        "Only for pet", ["all pets"] + [p.name for p in pets]
    ) if pets else "all pets"

# Translate the UI filter choices into scheduler arguments (None = no filter).
weekday_arg = None if day_label == "any day" else day_label
pet_arg = None if pet_filter_label == "all pets" else pet_filter_label

# Count tasks currently toggled into today's plan (and not already done),
# honoring the same weekday/pet filters the scheduler will apply.
_preview = Scheduler(available_minutes=int(available_minutes))
_preview.load_tasks_from_owner(owner)
planned = _preview.apply_constraints(weekday=weekday_arg, pet=pet_arg)
st.caption(f"{len(planned)} task(s) match today's plan filters.")

if st.button("Generate schedule"):
    if not planned:
        st.warning(
            "No tasks match the current plan filters. Add tasks, toggle "
            "'Include in today's plan' on, and check the day/pet filters."
        )
    else:
        scheduler = Scheduler(available_minutes=int(available_minutes))
        scheduler.load_tasks_from_owner(owner)
        scheduler.build_plan(
            highest_priority_first=highest_first,
            resolve_conflicts=resolve_conflicts,
            weekday=weekday_arg,
            pet=pet_arg,
        )
        st.text(scheduler.explain_plan())
