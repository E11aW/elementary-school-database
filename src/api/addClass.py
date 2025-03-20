# addClass.py
# NOT GRADED
import psycopg2

class addClass:
    def __init__(self, db_config):
        """
        Initializes the API instance with database configuration.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        self.db_config = db_config
        self.room_number = None
        self.class_type = None
        self.start_time = None
        self.duration = None
        self.error_message = None
        self.new_class_details = None

    @classmethod
    def prepareStatements(cls, db_config):
        """
        Prepares server‑side prepared statements for checking room availability
        and for inserting a new class.
        
        Two statements are prepared:
          1. check_room_availability_plan:
             Checks if a room has an existing class that overlaps with a given start time and duration.
          2. insert_class_plan_v5:
             Uses a CTE to generate a new ID from the class sequence, then inserts a new class row
             using that ID, and sets Number to 'C' concatenated with that ID.
             Returns the new class details: Number, RoomNumber, StartTime, Duration.
        
        The persistent connection and prepared statement names are stored as class variables.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        try:
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            
            # Prepare statement to check room availability.
            stmt_availability = """
                PREPARE check_room_availability_plan (varchar, time, interval) AS
                SELECT 1 FROM class
                WHERE RoomNumber = $1
                  AND ($2 < (StartTime + Duration) AND StartTime < ($2 + $3));
            """
            cursor.execute(stmt_availability)
            
            # Prepare statement to insert a new class.
            stmt_insert = """
                PREPARE insert_class_plan_v5 (varchar, varchar, time, interval) AS
                WITH new_id AS (
                    SELECT nextval(pg_get_serial_sequence('class','id')) as id
                )
                INSERT INTO class (ID, Number, ClassTypeID, RoomNumber, StartTime, Duration)
                SELECT new_id.id, 'C' || new_id.id, $1, $2, $3, $4
                FROM new_id
                RETURNING Number, RoomNumber, StartTime, Duration;
            """
            cursor.execute(stmt_insert)
            
            connection.commit()
            cursor.close()
            
            cls.prepared_conn = connection
            cls.prepared_statement_availability = "check_room_availability_plan"
            cls.prepared_statement_insert = "insert_class_plan_v5"
            print("Prepared statements for addClass.")
        except Exception as e:
            print("Error preparing statements for addClass:", e)

    def getDescription(self):
        """
        Returns a description of what this API does.
        """
        return (
            "Creates a new class if the room is available.\n\n"
            "Input:\n"
            "- Room Number\n"
            "- Class Type (ID)\n"
            "- Start Time (HH:MM:SS)\n"
            "- Duration (HH:MM:SS, e.g., '01:00:00' for one hour)\n\n"
            "Output:\n"
            "- Confirmation of new class creation with details:\n"
            "  - Class Number\n"
            "  - Room Number\n"
            "  - Start Time\n"
            "  - Duration\n\n"
            "If the room is not available, an error message is returned and the class is not created."
        )

    def getInput(self, room_number=None, class_type=None, start_time=None, duration=None):
        """
        Takes input for the new class.
        
        :param room_number: The room number where the class will be held.
        :param class_type: The class type (ID) for the new class.
        :param start_time: The start time of the class (HH:MM:SS).
        :param duration: The duration of the class (HH:MM:SS).
        """
        if room_number and class_type and start_time and duration:
            self.room_number = room_number
            self.class_type = class_type
            self.start_time = start_time
            self.duration = duration
        else:
            self.room_number = input("Enter Room Number: ").strip()
            self.class_type = input("Enter Class Type (ID): ").strip()
            self.start_time = input("Enter Start Time (HH:MM:SS): ").strip()
            self.duration = input("Enter Duration (HH:MM:SS): ").strip()

    def retrieveOutput(self):
        """
        Checks room availability and, if available, creates a new class.
        If the room is not available, sets an error message.
        """
        try:
            # Fallback: if prepared_conn is not set, prepare the statements.
            if not hasattr(self.__class__, 'prepared_conn'):
                self.__class__.prepareStatements(self.db_config)
            
            connection = self.__class__.prepared_conn
            cursor = connection.cursor()
            
            # Synchronize the sequence for class.id (if needed)
            cursor.execute("""
                SELECT setval(pg_get_serial_sequence('class','id'),
                COALESCE((SELECT max(id) FROM class), 0) + 1, false);
            """)
            connection.commit()
            
            # 1. Check if the room is available.
            exec_check = f"EXECUTE {self.__class__.prepared_statement_availability} (%s, %s, %s);"
            cursor.execute(exec_check, (self.room_number, self.start_time, self.duration))
            availability_result = cursor.fetchone()
            if availability_result:
                self.error_message = f"Room {self.room_number} is not available at the given time."
                cursor.close()
                return
            
            # 2. Room is available. Insert the new class.
            exec_insert = f"EXECUTE {self.__class__.prepared_statement_insert} (%s, %s, %s, %s);"
            cursor.execute(exec_insert, (self.class_type, self.room_number, self.start_time, self.duration))
            result = cursor.fetchone()
            connection.commit()
            cursor.close()
            
            if result:
                self.new_class_details = {
                    "number": result[0],
                    "room_number": result[1],
                    "start_time": result[2],
                    "duration": result[3]
                }
            else:
                self.error_message = "Failed to create new class."
        except Exception as e:
            if connection:
                connection.rollback()
            self.error_message = f"Error creating new class: {e}"

    def displayOutput(self):
        """
        Displays either an error message or the details of the newly created class.
        """
        if self.error_message:
            print(self.error_message)
        elif self.new_class_details:
            print("New class created successfully!")
            print(f"Class Number: {self.new_class_details['number']}")
            print(f"Room Number: {self.new_class_details['room_number']}")
            print(f"Start Time: {self.new_class_details['start_time']}")
            print(f"Duration: {self.new_class_details['duration']}")
        else:
            print("No output to display.")