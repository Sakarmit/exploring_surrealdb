1) CodeStates.csv and MainTable.csv included in this folder have the full dump of exercise attempts the semester of Fall 2024.

1.a) CodeStates.csv table. That table has just 2 columns, the CodeStateID and the Code itself. 

1.b) MainTable.csv table. That table includes information per submission. Specifically speaking, each row records who did what, when, on which problem, and what happened It has the following columns:

•  SubjectID → student 
•  ProblemID → problem 
•  session_id → session 
•  CodeStateID → code snapshot 
•  Other columns → features (score, attempt, etc.)

SubjectID: Unique student identifier
ToolInstances: Tools used in the environment
CourseID: Course name/code
CourseSectionID: Section of the course
TermID: Semester
AssignmentID
• Assignment identifier 
• Groups multiple problems 
ProblemID
• Specific problem within assignment
X-WorkoutOfferingID
• Internal ID for the assignment offering
X-ExerciseID
• Internal ID for the specific exercise/problem
Attempt
• Attempt number on the problem 
• Increases when student submits or retries
CodeStateID
• Unique ID for a version of the student’s code. Changes when code is modified
ServerTimestamp
• Exact time of event 
• Format: YYYY-MM-DDTHH:MM:SS
ServerTimezone
• Timezone of the server 
• Example: +0000 (UTC)
EventType
Describes what the student/system did:
Common values:
• Compile → code compiled 
• Run.Program → student ran the program 
• (others may exist: edit, submit, etc.) 
Score
• Result of execution
• Example:
• 1.0 → correct 
• 0.0 → incorrect
Compile.Result
• Result of compilation 
• Example: 
o Success 
o Error
CompileMessageType
• Type of compile error (if any)
CompileMessageData
• Details of compile error message. Useful for debugging behavior analysis
EventID
• Unique ID for this event 
ParentEventID
• Links events together
Example: 
Run event may depend on compile event
Order
• Order of events within the log. Used when timestamps are identical
IsEventOrderingConsistent
• Boolean indicating if event ordering is reliable. Helps detect logging issues

These columns allow you to reconstruct:
Student problem-solving workflows over time
Example:
Compile → Run → Error → Edit → Run → Success

Besides, the CourseSectionID which identifies each of our sections, and information for each submission (each time the student clicks "Check my answer!" on CodeWorkout) with the results.

CourseSectionID
1265 - Manuel
1266 - Qiong
1267 - Enas
1268 - Matt
1269 - Lulu
1270 - Dhruv
1271 - Dale-Marie
1276 - Testing
1279 - Ghost
1284 - who knows

For this study, please just focus on CourseSectionID=1266.


2) studentIDMapping_canvas_codeworkout.csv includes the mappings between student CodeWorkd IDs and Canvas IDs.

3) CodeWorkout_Questions.csv includes CodeWorkout question descriptions.

4) context_of_Codeworkout_Questions.scv includes the relationship between modules and CodeWorkout practices as well as the weeks that we assigned these practices.

5) Learning_Concepts_and_Objectives.csv is essential a subject-specific hierarchical curriculum map (or knowledge graph) that links:
- Learning Concepts (left column)
- Learning Objectives (right column) 

The Left Column represents the Learning Concept taxonomy, where the arrows (->) represent a hierarchy / dependency chain.
Example:
OOP -> Abstraction -> Object -> Reference Variables

This means:
Start with the learning concept OOP (Object-Oriented Programming)
, which includes the subconcept Abstraction
, which includes the subconcept Objects
, which includes the subconcept Reference Variables

So each deeper level = more specific skill

Please represent this learning concept taxonomy term as concept-concept relationships.

6) matrix_interation_concepts_outcomes_w_ori_order.csv includes the mapping between each student submission or interaction and the underlying learning concepts (as well as learning outcomes) that have been assessed.
