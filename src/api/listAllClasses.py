# listAllClasses.py
# Ella Williams
import psycopg2

class listAllClasses:
    def __init__(self, db_config):
        """
        Initializes the API instance with database configuration.
        :param db_config: Dictionary containing database connection parameters.
        """
        self.db_config = db_config
        self.grade = None
        self.classes = []
        
    @classmethod
    def prepareStatements(cls, db_config):
        """
        Prepares server‑side prepared statements for listing classes.
        Two statements are prepared:
          - list_classes_by_grade_plan: For listing classes matching a specific grade level.
          - list_all_classes_plan: For listing all classes when no grade is specified.
        The persistent connection and the statement names are stored as class variables.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        try:
            # Establish a persistent connection for prepared statements.
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            
            # Prepare statement for listing classes by a specific grade level.
            stmt_grade = """
                PREPARE list_classes_by_grade_plan (text) AS
                SELECT C.Number, CT.Name, C.RoomNumber, C.startTime, C.duration, S.number
                FROM Class C
                    JOIN ClassType CT ON CT.ID = C.classTypeID
                    JOIN StaffToClass SC ON (SC.classID = C.ID)
                    JOIN Staff S ON (S.ID = SC.staffID)
                WHERE CT.ID ILIKE $1
                ORDER BY CT.ID;
            """
            cursor.execute(stmt_grade)
            
            # Prepare statement for listing all classes (no parameter needed).
            stmt_all = """
                PREPARE list_all_classes_plan AS
                SELECT C.Number, CT.Name, C.RoomNumber, C.startTime, C.duration, S.number
                FROM Class C
                    JOIN ClassType CT ON CT.ID = C.classTypeID
                    JOIN StaffToClass SC ON (SC.classID = C.ID)
                    JOIN Staff S ON (S.ID = SC.staffID)
                ORDER BY CT.ID;
            """
            cursor.execute(stmt_all)
            
            connection.commit()
            cursor.close()
            
            # Store the persistent connection and prepared statement names as class variables.
            cls.prepared_conn = connection
            cls.prepared_statement_grade = "list_classes_by_grade_plan"
            cls.prepared_statement_all = "list_all_classes_plan"
            print("Prepared statements for listAllClasses.")
        except Exception as e:
            print("Error preparing statements for listAllClasses:", e)
    
    def getDescription(self):
        """
        Returns a description of what this API does.
        """
        return """Lists all classes available in our elementary school.

Input:
- grade level (optional)

Output:
- List of all classes and their details:
  - Class number
  - Class Type
  - Room Number
  - Start Time
  - Duration
  - Staff Number

Business purpose:
Allows anyone to track which classes are offered at our school."""
    
    def getInput(self):
        """
        Asks if using a specific grade for the query.
        """
        specific_grade = input("Do you want classes for a specific grade level? (y/n): ").lower()
        if specific_grade == "y":
            self.grade = input("Enter the grade level (K, 1, 2, 3, 4, 5): ").strip().upper()
            while(self.grade != "K" and self.grade != "1" and self.grade != "2" and self.grade != "3" and self.grade != "4" and self.grade != "5"):
                self.grade = input("Enter an acceptable grade level (K, 1, 2, 3, 4, 5): ").strip().upper()

    def retrieveOutput(self):
        """
        Retrieves classes using the prepared statements.
        Uses the persistent connection created in prepareStatements().
        """
        try:
            # Use the persistent connection from the class variable.
            connection = self.__class__.prepared_conn
            cursor = connection.cursor()
            
            if self.grade is not None:
                # Execute the prepared statement for a specific grade.
                exec_query = f"EXECUTE {self.__class__.prepared_statement_grade} (%s);"
                cursor.execute(exec_query, (f"%{self.grade}%",))
            else:
                # Execute the prepared statement for listing all classes.
                exec_query = f"EXECUTE {self.__class__.prepared_statement_all};"
                cursor.execute(exec_query)
            
            all_classes = cursor.fetchall()
            
            # Format the result into a list of dictionaries.
            self.classes = []
            for each_class in all_classes:
                self.classes.append({
                    "number": each_class[0],
                    "type": each_class[1],
                    "room_number": each_class[2],
                    "start_time": each_class[3],
                    "duration": each_class[4],
                    "staff": each_class[5]
                })
            
            cursor.close()
            # Note: The persistent connection is not closed here.
        except Exception as e:
            print(f"Error finding classes: {e}")
    
    def displayOutput(self):
        """
        Displays a list of the classes.
        """
        if not self.classes:
            print("No classes were found.")
            return
        
        print("\n=== All available classes ===")
        for i, each_class in enumerate(self.classes, 1):
            print(f"\n[{i}] Number: {each_class['number']}")
            print(f"    Class Type: {each_class['type']}")
            print(f"    Room Number: {each_class['room_number']}")
            print(f"    Start Time: {each_class['start_time']}")
            print(f"    Duration: {each_class['duration']}")
            print(f"    Assigned Staff: {each_class['staff']}")
        print("\n========================================================")
