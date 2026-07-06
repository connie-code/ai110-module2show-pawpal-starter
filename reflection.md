# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
  1. Users can add pet and owner information
  2. Users can add and edit tasks with time and the priority of the task
  3. Users can schedule appointments for doctors, walk, cleaning, etc.
- What classes did you include, and what responsibilities did you assign to each?
  * Owner - holds the first and last name of the owner, address, pet(s) they have, their preferences for pet care
  * Pet - holds the pet's name, medical history, owner name, species, tasks
  * Task - the task name, type, time, priority, recurrence (f any), duration
  * Schedular - applies contraints to the tasks with the owner and pet information and creates a plan 

**b. Design changes**

- Did your design change during implementation?
  * Yes
  
- If yes, describe at least one change and why you made it.
  * In the Task object, a relationship with Pet was added so that each tasks knows which Pet it is assigned to. Without this a task does not know which pet it belongs to, while Pet knows its tasks
  * Changed the time attribute in Time class to have type datetime.time. This is to prevent different time format of time to cause bugs and problems.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
  * The schedular considers time, priority and preferences
- How did you decide which constraints mattered most?
  * I thought of the human aspect and how a typical user would like to engage with the application.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
  * A tradeoff the scheduler makes is when there's a conflicting task and it's of similiar priority and time. Decided to schedule it in and have a warning message letting the user decides. 
- Why is that tradeoff reasonable for this scenario?
  * There's times where the user would like to add everything that is going on into the schedule and multiple people are executing the tasks so it technically does not overlap in real life.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
