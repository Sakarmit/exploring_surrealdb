import csv

def parse_students(file_path):
    students = []
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            students.append({"id":row['StudentID'], 
                             "name": row['Student'], 
                             "sis_id": row['SIS Login ID']})
    return students

def parse_submissions(file_path, only_section_ids=None):
    main_table = []
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            class_id = row['CourseSectionID']
            if only_section_ids and class_id not in only_section_ids:
                continue        
            float_score = None
            try:
                float_score = float(row['Score'])
            except ValueError:
                pass 
            submission = {"student_id": row['SubjectID'], 
                           "class_id": class_id, 
                           "problem_id": row['ProblemID'], 
                           "code_state_id": row['CodeStateID'], 
                           "event_type": row['EventType'], 
                           "result": row['Compile.Result'], 
                            "order": row['Order']}
            if float_score is not None:
                submission["score"] = float_score
            main_table.append(submission)
    return main_table

def parse_problem_concepts(file_path):
    problems = []
    checked_problem_ids = set()
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Avoid duplicates in case the same problem appears multiple times in the dataset
            if row['ProblemID'] in checked_problem_ids:
                continue
            checked_problem_ids.add(row['ProblemID'])

            data = {
                'id': row['ProblemID']
            }
            # Extract concepts based on columns that have a value of 1.0, excluding other data columns
            concepts = []
            for key, value in row.items():
                if key not in ['SubjectID', 'ProblemID', 'Attempt', 'Score','CodeStateID']:
                    try:
                        float_value = float(value)
                        if float_value == 1.0:
                            concepts.append(key)
                    except ValueError:
                        pass
            data['concepts'] = concepts

            problems.append(data)
    return problems
