# listStudentsInClass.py
import psycopg2

class listStudentsInClass:
    def __init__(self, db_config):
        """
        Initializes the API instance with database configuration.
        :param db_config: Dictionary containing database connection parameters.
        """
        self.db_config = db_config
        self.class_number = None
        self.students = []

    @classmethod
    def prepareStatements(cls, db_config):
        """
        Prepares the SQL statement for listing students in a class using a server-side
        prepared statement. This method establishes a persistent connection and prepares
        the statement once.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        try:
            # Establish a persistent connection for prepared statements.
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            
            # Prepare the statement using PostgreSQL's PREPARE command.
            stmt = """
                PREPARE list_students_plan (text) AS
                SELECT s.Number, s.FirstName, s.LastName 
                FROM Student s
                JOIN StudentToClass sc ON s.ID = sc.StudentID
                JOIN Class c ON sc.ClassID = c.ID
                WHERE c.Number = $1;
            """
            cursor.execute(stmt)
            connection.commit()
            cursor.close()
            
            # Store the connection and statement name as class variables.
            cls.prepared_conn = connection
            cls.prepared_statement_name = "list_students_plan"
            print("Prepared statement for listStudentsInClass.")
        except Exception as e:
            print("Error preparing statement for listStudentsInClass:", e)

    def getDescription(self):
        """
        Returns a description of what this API does.
        """
        return "Retrieves a list of students enrolled in a given class."  

    def getInput(self, class_number=None):
        """
        Takes the class number as input. If no class number is provided, it prompts the user.
        :param class_number: The unique class number.
        """
        if class_number is None:
            class_number = input("\nEnter Class Number: ").strip()

        self.class_number = class_number

    def retrieveOutput(self):
        """
        Retrieves students for the given class number using the previously prepared statement.
        It uses the persistent connection from prepareStatements().
        """
        try:
            # Use the persistent connection created in prepareStatements.
            connection = self.__class__.prepared_conn
            cursor = connection.cursor()
            
            # Execute the prepared statement using PostgreSQL's EXECUTE command.
            exec_query = f"EXECUTE {self.__class__.prepared_statement_name} (%s);"
            cursor.execute(exec_query, (self.class_number,))
            self.students = cursor.fetchall()
            
            cursor.close()
            # Note: Do not close the connection here because it is reused for prepared statements.
        except Exception as e:
            print(f"Error retrieving students: {e}")
    
    def displayOutput(self):
        """
        Displays the retrieved student information.
        """
        if not self.students:
            print(f"No students found for class {self.class_number}.")
        else:
            print(f"Students in class {self.class_number}:")
            for student in self.students:
                print(f"Student Number: {student[0]}, Name: {student[1]} {student[2]}")
