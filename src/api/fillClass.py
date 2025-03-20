# fillClass.py
# Clayton McArthur
# Maxx McArthur
import psycopg2

class fillClass:
    def __init__(self, db_config):
        """
        Initializes the API instance with database configuration.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        self.db_config = db_config
        self.class_number = None
        self.staff_number = None
        self.assignments = []  # List of dictionaries with keys: number and type
        self.error_message = None

    @classmethod
    def prepareStatements(cls, db_config):
        """
        Prepares server‑side prepared statements for the fillClass API.
        
        Prepared statements:
          1. get_class_id_plan: Given a class number, returns the class ID.
          2. get_staff_id_plan: Given a staff number, returns the staff ID.
          3. insert_staff_plan: Inserts a record into StaffToClass (assigns a staff member to a class)
             using ON CONFLICT DO NOTHING.
          4. get_class_assignments_plan: Returns all assigned student and staff numbers (with a type tag)
             for a given class number.
          5. get_class_details_plan: Given a class number, returns the class’s StartTime, Duration,
             and derived Grade (the first character of ClassType.ID) by joining with classtype.
          6. get_eligible_students_plan: Returns student numbers from the student table for students
             whose Grade equals a given grade and who do not already have a homeroom assignment
             (as determined by having a class with a ClassTypeID like '%HR%' other than the target class).
             (Parameters: target grade, target class number)
          7. get_student_id_plan: Given a student number, returns the student's internal ID.
          8. insert_student_plan: Inserts a record into StudentToClass (assigns a student to a class)
             using ON CONFLICT DO NOTHING.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        try:
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            
            # 1. Prepare statement to get the class ID from class number.
            stmt_class_id = """
                PREPARE get_class_id_plan (varchar) AS
                SELECT ID FROM class WHERE Number = $1;
            """
            cursor.execute(stmt_class_id)
            
            # 2. Prepare statement to get the staff ID from staff number.
            stmt_staff_id = """
                PREPARE get_staff_id_plan (varchar) AS
                SELECT ID FROM staff WHERE Number = $1;
            """
            cursor.execute(stmt_staff_id)
            
            # 3. Prepare statement to insert into StaffToClass.
            stmt_insert_staff = """
                PREPARE insert_staff_plan (integer, integer) AS
                INSERT INTO StaffToClass (StaffID, ClassID)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING;
            """
            cursor.execute(stmt_insert_staff)
            
            # 4. Prepare statement to get class assignments (both students and staff).
            stmt_assignments = """
                PREPARE get_class_assignments_plan (varchar) AS
                SELECT s.Number, 'student' AS type
                FROM student s
                JOIN StudentToClass stc ON s.ID = stc.StudentID
                JOIN class c ON stc.ClassID = c.ID
                WHERE c.Number = $1
                UNION ALL
                SELECT st.Number, 'staff' AS type
                FROM staff st
                JOIN StaffToClass stf ON st.ID = stf.StaffID
                JOIN class c ON stf.ClassID = c.ID
                WHERE c.Number = $1;
            """
            cursor.execute(stmt_assignments)
            
            # 5. Prepare statement to get class details (start time, duration, derived grade).
            stmt_class_details = """
                PREPARE get_class_details_plan (varchar) AS
                SELECT c.StartTime, c.Duration, LEFT(ct.ID, 1) AS grade
                FROM class c
                JOIN classtype ct ON c.ClassTypeID = ct.ID
                WHERE c.Number = $1;
            """
            cursor.execute(stmt_class_details)
            
            # 6. Prepare statement to get eligible students based on homeroom check.
            stmt_eligible_students = """
                PREPARE get_eligible_students_plan (varchar, varchar) AS
                SELECT s.Number
                FROM student s
                WHERE s.Grade = $1
                  AND NOT EXISTS (
                      SELECT 1
                      FROM StudentToClass stc
                      JOIN class c ON stc.ClassID = c.ID
                      WHERE s.ID = stc.StudentID
                        AND c.ClassTypeID LIKE '%HR%'
                        AND c.Number <> $2
                  );
            """
            cursor.execute(stmt_eligible_students)
            
            # 7. Prepare statement to get student ID from student number.
            stmt_student_id = """
                PREPARE get_student_id_plan (varchar) AS
                SELECT ID FROM student WHERE Number = $1;
            """
            cursor.execute(stmt_student_id)
            
            # 8. Prepare statement to insert into StudentToClass.
            stmt_insert_student = """
                PREPARE insert_student_plan (integer, integer) AS
                INSERT INTO StudentToClass (StudentID, ClassID)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING;
            """
            cursor.execute(stmt_insert_student)
            
            connection.commit()
            cursor.close()
            
            cls.prepared_conn = connection
            cls.prepared_statement_get_class_id = "get_class_id_plan"
            cls.prepared_statement_get_staff_id = "get_staff_id_plan"
            cls.prepared_statement_insert_staff = "insert_staff_plan"
            cls.prepared_statement_assignments = "get_class_assignments_plan"
            cls.prepared_statement_class_details = "get_class_details_plan"
            cls.prepared_statement_eligible_students = "get_eligible_students_plan"
            cls.prepared_statement_get_student_id = "get_student_id_plan"
            cls.prepared_statement_insert_student = "insert_student_plan"
            print("Prepared statements for fillClass.")
        except Exception as e:
            print("Error preparing statements for fillClass:", e)

    def getDescription(self):
        """
        Returns a description of what this API does.
        """
        return (
            "Assigns a staff member to manage a class while filling it with students attending it.\n\n"
            "Input:\n"
            "- Class Number\n"
            "- Staff Number\n\n"
            "Output:\n"
            "- List of all student and staff numbers assigned to the class.\n"
            "  (Only students in the same grade as the class and not already assigned to a homeroom are added.)"
        )

    def getInput(self, class_number=None, staff_number=None):
        """
        Takes input for the class number and staff number.
        
        :param class_number: The unique class number.
        :param staff_number: The unique staff number.
        """
        if class_number and staff_number:
            self.class_number = class_number
            self.staff_number = staff_number
        else:
            self.class_number = input("Enter Class Number: ").strip()
            self.staff_number = input("Enter Staff Number: ").strip()

    def retrieveOutput(self):
        """
        Assigns the staff to the class (if not already assigned), fills the class with eligible students,
        and retrieves the final list of all student and staff numbers assigned to that class.
        Only students who are in the same grade as the class and who are not already assigned to a homeroom
        (other than the target class) are added.
        """
        try:
            # Ensure prepared statements are ready.
            if not hasattr(self.__class__, 'prepared_conn'):
                self.__class__.prepareStatements(self.db_config)
            
            connection = self.__class__.prepared_conn
            cursor = connection.cursor()
            
            # 1. Get the class ID.
            exec_class_id = f"EXECUTE {self.__class__.prepared_statement_get_class_id} (%s);"
            cursor.execute(exec_class_id, (self.class_number,))
            class_id_result = cursor.fetchone()
            if not class_id_result:
                self.error_message = f"Class with number {self.class_number} not found."
                cursor.close()
                return
            class_id = class_id_result[0]
            
            # 2. Get the staff ID.
            exec_staff_id = f"EXECUTE {self.__class__.prepared_statement_get_staff_id} (%s);"
            cursor.execute(exec_staff_id, (self.staff_number,))
            staff_id_result = cursor.fetchone()
            if not staff_id_result:
                self.error_message = f"Staff with number {self.staff_number} not found."
                cursor.close()
                return
            staff_id = staff_id_result[0]
            
            # 3. Insert the staff assignment.
            exec_insert_staff = f"EXECUTE {self.__class__.prepared_statement_insert_staff} (%s, %s);"
            cursor.execute(exec_insert_staff, (staff_id, class_id))
            connection.commit()
            
            # 4. Get class details: start time, duration, and derived grade.
            exec_class_details = f"EXECUTE {self.__class__.prepared_statement_class_details} (%s);"
            cursor.execute(exec_class_details, (self.class_number,))
            details = cursor.fetchone()
            if not details:
                self.error_message = f"Could not retrieve details for class {self.class_number}."
                cursor.close()
                return
            class_start_time, class_duration, class_grade = details
            
            # 5. Retrieve eligible students based on homeroom assignment.
            exec_eligible_students = f"EXECUTE {self.__class__.prepared_statement_eligible_students} (%s, %s);"
            cursor.execute(exec_eligible_students, (class_grade, self.class_number))
            eligible_students = cursor.fetchall()
            
            # 6. For each eligible student, get their internal ID and insert into StudentToClass.
            for (student_number,) in eligible_students:
                exec_student_id = f"EXECUTE {self.__class__.prepared_statement_get_student_id} (%s);"
                cursor.execute(exec_student_id, (student_number,))
                student_id_result = cursor.fetchone()
                if student_id_result:
                    student_id = student_id_result[0]
                    exec_insert_student = f"EXECUTE {self.__class__.prepared_statement_insert_student} (%s, %s);"
                    cursor.execute(exec_insert_student, (student_id, class_id))
            connection.commit()
            
            # 7. Retrieve all assignments for the class (students and staff).
            exec_assignments = f"EXECUTE {self.__class__.prepared_statement_assignments} (%s);"
            cursor.execute(exec_assignments, (self.class_number,))
            results = cursor.fetchall()
            self.assignments = []
            for row in results:
                self.assignments.append({"number": row[0], "type": row[1]})
            cursor.close()
        except Exception as e:
            if connection:
                connection.rollback()
            self.error_message = f"Error retrieving class assignments: {e}"

    def displayOutput(self):
        """
        Displays the final list of student and staff assignments for the class.
        """
        if self.error_message:
            print(self.error_message)
            return
        if not self.assignments:
            print(f"No assignments found for class {self.class_number}.")
            return
        
        print(f"\n=== Assignments for Class {self.class_number} ===")
        for assign in self.assignments:
            print(f"{assign['type'].capitalize()}: {assign['number']}")
        print("========================================")