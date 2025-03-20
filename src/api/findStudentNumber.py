# findStudentNumber.py
# Ella Williams
import psycopg2

class findStudentNumber:
    def __init__(self, db_config):
        """
        Initializes the API instance with database configuration.
        :param db_config: Dictionary containing database connection parameters.
        """
        self.db_config = db_config
        self.first_name = None
        self.last_name = None
        self.students = []
        
    @classmethod
    def prepareStatements(cls, db_config):
        """
        Prepares a server‑side prepared statement for finding student numbers.
        This statement retrieves the student's number, first name, last name, and grade,
        given a first name and last name.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        try:
            # Establish a persistent connection for the prepared statement.
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            
            # Create a prepared statement named "find_student_number_plan"
            stmt = """
                PREPARE find_student_number_plan (text, text) AS
                SELECT S.Number, S.FirstName, S.LastName, S.Grade
                FROM Student S
                WHERE S.FirstName = $1 AND S.LastName = $2;
            """
            cursor.execute(stmt)
            connection.commit()
            cursor.close()
            
            # Store the persistent connection and prepared statement name as class variables.
            cls.prepared_conn = connection
            cls.prepared_statement_name = "find_student_number_plan"
            print("Prepared statement for findStudentNumber.")
        except Exception as e:
            print("Error preparing statement for findStudentNumber:", e)

    def getDescription(self):
        """
        Returns a description of what this API does.
        """
        return """Lists the number for each student with the given name

Input:
- First name
- Last name

Output:
- Student number
- First name
- Last name
- Grade 

Business purpose:
Allows the user to find a student's number."""
    
    def getInput(self, first_name=None, last_name=None):
        """
        Takes the input for the student's number.
        If called without parameters, prompts the user for input interactively.
        
        :param first_name: Student's first name.
        :param last_name: Student's last name.
        """
        if first_name and last_name:
            self.first_name = first_name
            self.last_name = last_name
            return
            
        print("Please enter the following information to find student number:")
        self.first_name = input("Student First Name: ").strip()
        self.last_name = input("Student Last Name: ").strip()
    
    def retrieveOutput(self):
        """
        Retrieves the student numbers using the prepared statement.
        It reuses the persistent connection created in prepareStatements().
        """
        try:
            # Use the persistent connection created in prepareStatements.
            connection = self.__class__.prepared_conn
            cursor = connection.cursor()
            
            # Execute the prepared statement with the provided first and last name.
            exec_query = f"EXECUTE {self.__class__.prepared_statement_name} (%s, %s);"
            cursor.execute(exec_query, (self.first_name, self.last_name))
            students = cursor.fetchall()
            
            # Format the result into a list of dictionaries.
            self.students = []
            for each_student in students:
                self.students.append({
                    "number": each_student[0],
                    "firstname": each_student[1],
                    "lastname": each_student[2],
                    "grade": each_student[3]
                })
            
            cursor.close()
        except Exception as e:
            print(f"Error finding students: {e}")
    
    def displayOutput(self):
        """
        Displays a list of all students with the provided name.
        """
        if not self.students:
            print(f"No students were found with the name {self.first_name} {self.last_name}.")
            return
        
        print(f"\n=== Students with the name: {self.first_name} {self.last_name} ===")
        
        for i, each_student in enumerate(self.students, 1):
            print(f"\n[{i}] Number: {each_student['number']}")
            print(f"    First Name: {each_student['firstname']}")
            print(f"    Last Name: {each_student['lastname']}")
            print(f"    Grade: {each_student['grade']}")
        
        print("\n========================================================")