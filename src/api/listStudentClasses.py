# listStudentClasses.py
import psycopg2

class listStudentClasses:
    def __init__(self, db_config):
        """
        Initializes the API instance with database configuration.
        :param db_config: Dictionary containing database connection parameters.
        """
        self.db_config = db_config
        self.student_number = None
        self.student_first_name = None
        self.student_last_name = None
        self.classes = []
        
    @classmethod
    def prepareStatements(cls, db_config):
        """
        Prepares server‑side prepared statements for listing a student's classes.
        Two statements are created:
          - get_student_details_plan: Retrieves student details by student number.
          - get_student_classes_plan: Retrieves classes attended by the student (by student ID).
        The persistent connection and statement names are stored as class variables.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        try:
            # Establish a persistent connection.
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            
            # Prepare statement for retrieving student details.
            stmt_details = """
                PREPARE get_student_details_plan (text) AS
                SELECT ID, FirstName, LastName 
                FROM Student 
                WHERE Number = $1;
            """
            cursor.execute(stmt_details)
            
            # Prepare statement for retrieving student classes.
            stmt_classes = """
                PREPARE get_student_classes_plan (integer) AS
                SELECT C.Number, CT.Name, C.RoomNumber, C.startTime, C.duration
                FROM Class C
                    JOIN ClassType CT ON CT.ID = C.classTypeID
                    JOIN StudentToClass SC ON SC.classID = C.ID
                WHERE SC.studentID = $1;
            """
            cursor.execute(stmt_classes)
            
            connection.commit()
            cursor.close()
            
            # Store the persistent connection and prepared statement names as class variables.
            cls.prepared_conn = connection
            cls.prepared_statement_details = "get_student_details_plan"
            cls.prepared_statement_classes = "get_student_classes_plan"
            print("Prepared statements for listStudentClasses.")
        except Exception as e:
            print("Error preparing statements for listStudentClasses:", e)
    
    def getDescription(self):
        """
        Returns a description of what this API does.
        """
        return """Lists each class an individual student attends.

Input:
- Student number

Output:
- List of all classes and their details:
  - Class number
  - Class Type
  - Room Number
  - Start Time
  - Duration

Business purpose:
Allows anyone to track where a student is at any given time throughout the school day."""
    
    def getInput(self, student_number=None, student_first_name=None, student_last_name=None):
        """
        Takes the input for the student's number.
        If parameters are provided directly, they are used; otherwise, prompts the user.
        
        :param student_number: The unique student number.
        """
        if student_number:
            self.student_number = student_number
            self.student_first_name = student_first_name
            self.student_last_name = student_last_name
            return
            
        print("Please enter the following information to find student classes:")
        self.student_number = input("Student Number: ").strip()
    
    def retrieveOutput(self):
        """
        Retrieves the student's classes using the prepared statements.
        Uses the persistent connection created in prepareStatements().
        """
        try:
            # Use the persistent connection.
            connection = self.__class__.prepared_conn
            cursor = connection.cursor()
            
            # Retrieve student details using the prepared statement.
            exec_query_details = f"EXECUTE {self.__class__.prepared_statement_details} (%s);"
            cursor.execute(exec_query_details, (self.student_number,))
            student_data = cursor.fetchone()
            
            if not student_data:
                print(f"Error: Student with number {self.student_number} not found.")
                cursor.close()
                return
            
            student_id = student_data[0]
            self.student_first_name = student_data[1]
            self.student_last_name = student_data[2]
            
            # Retrieve all classes the student attends using the prepared statement.
            exec_query_classes = f"EXECUTE {self.__class__.prepared_statement_classes} (%s);"
            cursor.execute(exec_query_classes, (student_id,))
            all_classes = cursor.fetchall()
            
            # Format the result.
            self.classes = []
            for each_class in all_classes:
                self.classes.append({
                    "number": each_class[0],
                    "type": each_class[1],
                    "room_number": each_class[2],
                    "start_time": each_class[3],
                    "duration": each_class[4]
                })
            
            cursor.close()
        except Exception as e:
            print(f"Error finding student classes: {e}")
    
    def displayOutput(self):
        """
        Displays a list of the classes this student attends.
        """
        if not self.classes:
            print(f"No classes were found for student {self.student_number}.")
            return
        
        print(f"\n=== Classes for student {self.student_number}: {self.student_first_name} {self.student_last_name} ===")
        for i, each_class in enumerate(self.classes, 1):
            print(f"\n[{i}] Number: {each_class['number']}")
            print(f"    Class Type: {each_class['type']}")
            print(f"    Room Number: {each_class['room_number']}")
            print(f"    Start Time: {each_class['start_time']}")
            print(f"    Duration: {each_class['duration']}")
        print("\n========================================================")
