import random

names = ["Thomas", "Joeseph", "Charlie", "Madison", "Mariana", "Leo", "Ayush", "Edward", "Melissa", "Giovanni", "Melvin", "Bond", "Morgan", "Jonah", "Festo", "John", "Schmidt", "Ian"]
buildings = ["Watson", "Taylor", "Franklin", "Millard", "Bowman"]
departments = ["Computer Science", "History", "Music", "Biology", "Physics", "Finance", "Electrical Engineering", "Mathematics", "English", "Philosophy"]
course_id_prefix = ["CS-", "HIS-", "MU-", "BIO-", "PHY-", "FIN-", "EE-", "MATH-", "ENG-", "PHIL-"]
semester = ['Fall', 'Spring', 'Summer']
days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
course_titles = ['Intro. to Biology', 'Genetics', 'Computational Biology', 'Intro. to Computer Science', 'Game Design', 'Robotics', 'Image Processing', 'Database System Concepts', 'Intro. to Digital Systems', 'Investment Banking', 'World History', 'Music Video Production', 'Physical Principles', "Intro. to Philosophy"]

# Should be initialized to empty
classrooms = []
advisors = []
instructors = []
students = []
courses = []
sections = []
time_slots = []

if (__name__ == "__main__"):
   # Starting amounts to generte
   classroom_amount = 20
   instructor_amount = 10
   student_amount = 40
   time_slot_amount = 15

   # Create the file
   with open("Group 17 - Project Phase 1 - Random Data.sql", "w") as sql_file:
      sql_file.write("USE univ_db;\n")

      # Empty Query
      insertion_query = ""

      # Classrooms
      for i in range(classroom_amount):
         # Generates random data
         class_building = random.choice(buildings)
         classroom_num = str(random.randint(100, 300))
         capacity = str(random.randint(10, 500))
         
         if (classroom_num, class_building) not in classrooms:
            classrooms.append((classroom_num, class_building))

            # Generates the query
            insertion_query = (
               "INSERT into classroom values (\'" +
               class_building + "\', \'" +
               classroom_num + "\', " +
               capacity + ");"
            )

            # Write the query to the file
            sql_file.write(insertion_query + '\n')

      # Departments
      for name in departments:
         # Generates random data
         budget = str(random.randint(1, 99) * 1000)
         depart_building = random.choice(buildings)

         # Generate the query
         insertion_query = (
            "INSERT into department values (\'" +
            name + "\', \'" + depart_building + "\', " +
            budget + ");"
         )
         
         # Write the query to the file
         sql_file.write(insertion_query + '\n')

      # Courses
      for name in course_titles:
         # Generates Random Data
         num = random.randint(0,9)
         random_id = course_id_prefix[num] + str(random.randint(100, 999))
         random_dept = departments[num]
         random_credits = str(random.randint(3,5))
         
         if (random_id not in courses):
            courses.append(random_id)
         
            # Generate the query
            insertion_query = (
               "INSERT into course values (\'" +
               random_id + "\', \'" +
               name + "\', \'" +
               random_dept + "\', " +
               random_credits + ");"
            )

            # Write the query to the file
            sql_file.write(insertion_query + '\n')

      # Instructors
      for i in range(instructor_amount):
         # Generates Random Data
         random_id = str(random.randint(100000000, 999999999))
         random_first = random.choice(names)
         random_middle = random.choice(names)
         random_last = random.choice(names)
         random_dept = random.choice(departments)
         instructors.append(random_id)
         advisors.append(random_id) # List of Advisors
         random_salary = str(random.randint(1000,99999))

         # Generate the query
         insertion_query = (
            "INSERT into instructor values (\'" +
            random_id + "\', \'" +
            random_first + "\', \'" +
            random_middle + "\', \'" +
            random_last + "\', \'" +
            random_dept + "\', " +
            random_salary + ");"
         )

         # Write the query to the file
         sql_file.write(insertion_query + '\n')
      
      # Students
      for i in range(student_amount):
         # Generates Random Data
         random_id = str(random.randint(100000000, 999999999))
         random_first = random.choice(names)
         random_middle = random.choice(names)
         random_last = random.choice(names)
         random_dept = random.choice(departments)
         random_credits = str(random.randint(0, 34))

         if (random.randint(1, 100) <= 40):
            random_advisor = "\'" + random.choice(advisors) + "\'"
         else:
            random_advisor = "NULL"

         students.append(random_id)

         # Generate the query
         insertion_query = (
            "INSERT into student values (\'" +
            random_id + "\', \'" +
            random_first + "\', \'" +
            random_middle + "\', \'" +
            random_last + "\', \'" +
            random_dept + "\', " +
            random_credits + ", " +
            random_advisor + ");"
         )

         # Write the query to the file
         sql_file.write(insertion_query + '\n')

      # Time Slot
      for i in range(time_slot_amount): #change for loop
         # Generates Random Data
         random_id = str(random.randint(1000, 9999))
         random_day = random.choice(days)
         random_hr = random.randint(5, 20) # Start
         random_min = random.randint(0, 59) # Start

         time_slots.append(random_id)

         # Generate the query
         insertion_query = (
            "INSERT into time_slot values (\'" +
            random_id + "\', \'" +
            random_day + "\', " +
            str(random_hr) + ", " +
            str(random_min) + ", " +
            str(random_hr + random.randint(1, 2)) + ", " +
            str(random_min) + ");"
         )

         # Write the query to the file
         sql_file.write(insertion_query + '\n')

      #
      # Highly Dependent on Relations
      #

      # Section
      for i in range(len(courses)):
         # Generates Random Data
         random_course = random.choice(courses)
         random_id = str(random.randint(10000, 99999)) # sec_id
         random_semester = random.choice(semester)
         random_year = str(random.randint(2019, 2022))
         random_room = random.choice(classrooms)
         random_time = random.choice(time_slots)

         sections.append((random_id, random_semester, random_year, random_course))

         # Generate the query
         insertion_query = (
            "INSERT into section values (\'" +
            random_course + "\', \'" +
            random_id + "\', \'" +
            random_semester + "\', " +
            random_year + ", \'" +
            random_room[1] + "\', \'" + # room's building
            random_room[0] + "\', \'" + # room number
            random_time + "\');"
         )

         # Write the query to the file
         sql_file.write(insertion_query + '\n')

      # Prereq
      for course_id in courses:
         # Generates Random Data
         if (random.randint(1, 100) <= 50):
            random_prereq = random.choice(courses)
            
            # Prevents a course being its own prereq
            while (random_prereq == course_id):
               random_prereq = random.choice(courses)

            # Generate the query
            insertion_query = (
               "INSERT into prereq values (\'" +
               course_id + "\', \'" +
               random_prereq + "\');"
            )

            # Write the query to the file
            sql_file.write(insertion_query + '\n')
         else: # If there is no prereq don't enter the course ID into prereqs
            pass

      # Teaches
      for sec in sections:
         # Generates Random Data
         random_instructor = random.choice(instructors)

         # Generate the query
         insertion_query = (
            "INSERT into teaches values (\'" +
            random_instructor + "\', \'" +
            sec[3] + "\', \'" + # course id
            sec[0] + "\', \'" + # section id
            sec[1] + "\', " +   # semester
            sec[2] + ");"       # year
         )

         # Write the query to the file
         sql_file.write(insertion_query + '\n')

      # Takes
      for person in students:
         # Generates Random Data
         random_sec = random.choice(sections)

         # Generate the query
         insertion_query = (
            "INSERT into takes values (\'" +
            person + "\', \'" +
            random_sec[3] + "\', \'" + # course id
            random_sec[0] + "\', \'" + # sec id
            random_sec[1] + "\', " + # semester
            random_sec[2] + ");"     # sec year
         )

         # Write the query to the file
         sql_file.write(insertion_query + '\n')
