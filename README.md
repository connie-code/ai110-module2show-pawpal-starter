# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
Today's Schedule for Jane Smith
========================================
Daily Care Plan
===============
Time budget: 180 min available, 130 min scheduled, 50 min free.

Scheduled (4):
  - 08:00  Morning walk (Biscuit) [priority 5, 30 min]
  - 09:30  Dental work (Biscuit) [priority 4, 45 min]
  - 11:00  Litter cleaning (Mochi) [priority 3, 15 min]
  - 14:00  Grooming (Mochi) [priority 2, 40 min]
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Run with coverage:
pytest --cov
```
Description of Tests: The tests covered the Owner, Pet, Task, and Scheduler classes. It checks that tasks can be created, added to pets, and marked complete; that recurring tasks spawn a correct next occurrence (daily +1 day, weekly +7 days) while one-off tasks don't; that tasks sort chronologically and filter by pet and status; and that the scheduler respects its time budget, handles boundary cases (exact fit, one minute over, zero minutes), and detects time conflicts—keeping the higher-priority task when two overlap.

Sample test output:

```
collected 20 items                                                                                                                                              

tests/test_pawpal.py ....................                                                                                                                 [100%]

====================================================================== 20 passed in 0.07s =======================================================================
```

Confidence Level: 5

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting by time | sort_by_time() | sort by time |
| Task sort by constraints | apply_constraints() | sort by priority, duration |
| Filtering | _schedule_or_skip_for_time() | skip tasks if time runs out |
| Conflict handling | tasks_overlap(), detect_conflicts(), check_time_conflicts() | overlapping time slots |
| Recurring tasks | is_due() | daily vs. weekly |

## 📸 Demo Walkthrough

1. Run `streamlit run app.py` to launch the app in the browser.
2. In the Owner section, type a name in the "Owner name" box (saves automatically).
3. In the Pets section, type a "Pet name", pick a "Species", and click "Add pet". Repeat to add more pets.
4. In the Tasks section, choose a pet from "Assign task to pet", fill in the title, type, start time, duration, priority, and repeat rule, then click "Add task".
5. Expand any task row to edit its fields and click "Save changes", click "Delete task", or flip the "Include in today's plan" toggle.
6. In the Build Schedule section, set "Available minutes for the day" and, if you like, adjust the "Highest priority first" and "Resolve time conflicts" checkboxes.
7. Use the "Plan for day" and "Only for pet" dropdowns to filter which tasks get scheduled.
8. Click "Generate schedule" to build the plan.
9. In the Daily Care Plan section, review the time-budget metrics, the conflict warnings (green if clear, red/amber if tasks overlap), the chronologically sorted Scheduled table, and the Skipped table with reasons.
10. Expand "Plan explanation (text)" to read the full written summary of the plan.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
