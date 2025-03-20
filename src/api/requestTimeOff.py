# requestTimeOff.py
import psycopg2
from datetime import datetime

class requestTimeOff:
    def __init__(self, db_config):
        """
        Initializes the API instance with database configuration.
        :param db_config: Dictionary containing database connection parameters.
        """
        self.db_config = db_config
        self.staff_number = None
        self.start_date = None
        self.end_date = None
        self.reason = None
        self.substitute_number = None
        self.request_result = None
        self.request_id = None

    @classmethod
    def prepareStatements(cls, db_config):
        """
        Prepares server‑side prepared statements for handling time off requests.
        The following statements are prepared:
          - validate_staff_plan: Validates a staff member by their number.
          - validate_substitute_plan: Validates a substitute by their number.
          - check_substitute_availability_plan: Checks if a substitute is available for the given dates.
          - insert_time_off_request_plan: Inserts a time off request and returns the new request ID.
          - get_time_off_request_plan: Retrieves details of a time off request for confirmation.
        
        The persistent connection and prepared statement names are stored as class variables.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        try:
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            
            # Prepare statement for validating staff.
            stmt_staff = """
                PREPARE validate_staff_plan (text) AS
                SELECT ID, FirstName, LastName 
                FROM Staff 
                WHERE Number = $1;
            """
            cursor.execute(stmt_staff)
            
            # Prepare statement for validating substitute.
            stmt_substitute = """
                PREPARE validate_substitute_plan (text) AS
                SELECT ID, FirstName, LastName
                FROM Substitute
                WHERE Number = $1;
            """
            cursor.execute(stmt_substitute)
            
            # Prepare statement for checking substitute availability.
            stmt_availability = """
                PREPARE check_substitute_availability_plan (integer, date, date) AS
                SELECT COUNT(*)
                FROM Availability
                WHERE SubstituteID = $1
                AND StartDate <= $2
                AND EndDate >= $3;
            """
            cursor.execute(stmt_availability)
            
            # Prepare statement for inserting a time off request.
            stmt_insert = """
                PREPARE insert_time_off_request_plan (date, date, text, integer, integer) AS
                INSERT INTO TimeOffRequest (StartDate, EndDate, Reason, StaffID, SubstituteID)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING ID;
            """
            cursor.execute(stmt_insert)
            
            # Prepare statement for retrieving time off request details.
            stmt_request_details = """
                PREPARE get_time_off_request_plan (integer) AS
                SELECT t.ID, t.StartDate, t.EndDate, t.Reason, 
                       s.Number as StaffNumber, s.FirstName as StaffFirstName, s.LastName as StaffLastName,
                       sub.Number as SubNumber, sub.FirstName as SubFirstName, sub.LastName as SubLastName
                FROM TimeOffRequest t
                JOIN Staff s ON t.StaffID = s.ID
                LEFT JOIN Substitute sub ON t.SubstituteID = sub.ID
                WHERE t.ID = $1;
            """
            cursor.execute(stmt_request_details)
            
            connection.commit()
            cursor.close()
            
            # Store the persistent connection and prepared statement names as class variables.
            cls.prepared_conn = connection
            cls.prepared_statement_staff = "validate_staff_plan"
            cls.prepared_statement_substitute = "validate_substitute_plan"
            cls.prepared_statement_availability = "check_substitute_availability_plan"
            cls.prepared_statement_insert = "insert_time_off_request_plan"
            cls.prepared_statement_request_details = "get_time_off_request_plan"
            
            print("Prepared statements for requestTimeOff.")
        except Exception as e:
            print("Error preparing statements for requestTimeOff:", e)

    def getDescription(self):
        """
        Returns a description of what this API does.
        """
        return """Allows staff to request time off and have their classes assigned a substitute.

                Input:
                - Staff Number
                - Start and end date
                - Reason
                - Substitute number (optional)

                Output:
                - Confirmation of new request
                - Details of the time off request"""

    def getInput(self, staff_number=None, start_date=None, end_date=None, reason=None, substitute_number=None):
        """
        Takes the inputs for requesting time off.
        If called without parameters, prompts the user for input interactively.
        
        :param staff_number: The unique staff number.
        :param start_date: The start date of time off (format: YYYY-MM-DD).
        :param end_date: The end date of time off (format: YYYY-MM-DD).
        :param reason: The reason for time off.
        :param substitute_number: Optional substitute number if already arranged.
        """
        if staff_number and start_date and end_date and reason:
            self.staff_number = staff_number
            self.start_date = start_date
            self.end_date = end_date
            self.reason = reason
            self.substitute_number = substitute_number
            return
            
        print("Please enter the following information for the time off request:")
        self.staff_number = input("Staff Number: ").strip()
        
        while True:
            try:
                start_date_input = input("Start Date (YYYY-MM-DD): ").strip()
                if len(start_date_input.split('-')) != 3:
                    print("Invalid date format. Please use YYYY-MM-DD format.")
                    continue
                self.start_date = start_date_input
                break
            except Exception:
                print("Invalid date format. Please use YYYY-MM-DD format.")
        
        while True:
            try:
                end_date_input = input("End Date (YYYY-MM-DD): ").strip()
                if len(end_date_input.split('-')) != 3:
                    print("Invalid date format. Please use YYYY-MM-DD format.")
                    continue
                self.end_date = end_date_input
                break
            except Exception:
                print("Invalid date format. Please use YYYY-MM-DD format.")
        
        self.reason = input("Reason for time off: ").strip()
        
        has_substitute = input("Do you already have a substitute? (y/n): ").lower().strip()
        if has_substitute == 'y':
            self.substitute_number = input("Substitute Number: ").strip()
        else:
            self.substitute_number = None

    def retrieveOutput(self):
        """
        Connects to the database using the persistent connection with prepared statements,
        validates inputs, and creates a time off request.
        """
        try:
            connection = self.__class__.prepared_conn
            cursor = connection.cursor()
            connection.autocommit = False
            
            # Validate staff number using the prepared statement.
            exec_staff = f"EXECUTE {self.__class__.prepared_statement_staff} (%s);"
            cursor.execute(exec_staff, (self.staff_number,))
            staff_data = cursor.fetchone()
            if not staff_data:
                self.request_result = {"success": False, "message": f"Staff with number {self.staff_number} not found."}
                cursor.close()
                return
            
            staff_id, staff_first_name, staff_last_name = staff_data
            
            # Validate substitute number if provided.
            substitute_id = None
            if self.substitute_number:
                exec_substitute = f"EXECUTE {self.__class__.prepared_statement_substitute} (%s);"
                cursor.execute(exec_substitute, (self.substitute_number,))
                substitute_data = cursor.fetchone()
                if not substitute_data:
                    self.request_result = {"success": False, "message": f"Substitute with number {self.substitute_number} not found."}
                    cursor.close()
                    return
                substitute_id = substitute_data[0]
                
                # Check if substitute is available using the prepared statement.
                exec_availability = f"EXECUTE {self.__class__.prepared_statement_availability} (%s, %s, %s);"
                cursor.execute(exec_availability, (substitute_id, self.start_date, self.end_date))
                available_count = cursor.fetchone()[0]
                if available_count == 0:
                    self.request_result = {"success": False, "message": f"Substitute is not available for the requested dates."}
                    cursor.close()
                    return
            
            # Create time off request using the prepared statement.
            exec_insert = f"EXECUTE {self.__class__.prepared_statement_insert} (%s, %s, %s, %s, %s);"
            cursor.execute(exec_insert, (self.start_date, self.end_date, self.reason, staff_id, substitute_id))
            self.request_id = cursor.fetchone()[0]
            
            connection.commit()
            
            # Retrieve the created request details for confirmation using the prepared statement.
            exec_request_details = f"EXECUTE {self.__class__.prepared_statement_request_details} (%s);"
            cursor.execute(exec_request_details, (self.request_id,))
            request_details = cursor.fetchone()
            
            if request_details:
                self.request_result = {
                    "success": True,
                    "request_id": request_details[0],
                    "start_date": request_details[1],
                    "end_date": request_details[2],
                    "reason": request_details[3],
                    "staff": {
                        "number": request_details[4],
                        "name": f"{request_details[5]} {request_details[6]}"
                    },
                    "substitute": None
                }
                if request_details[7]:  # If a substitute exists
                    self.request_result["substitute"] = {
                        "number": request_details[7],
                        "name": f"{request_details[8]} {request_details[9]}"
                    }
            else:
                self.request_result = {"success": False, "message": "Failed to retrieve request details."}
            
            cursor.close()
        except Exception as e:
            if connection:
                connection.rollback()
            self.request_result = {"success": False, "message": f"Error creating time off request: {e}"}
            if cursor:
                cursor.close()

    def displayOutput(self):
        """Displays the result of the time off request operation."""
        if not self.request_result:
            print("No request was processed.")
            return
            
        if not self.request_result["success"]:
            print(f"Error: {self.request_result['message']}")
            return
            
        print("\n=== Time Off Request Created Successfully ===")
        print(f"Request ID: {self.request_result['request_id']}")
        print(f"Staff: {self.request_result['staff']['name']} (Number: {self.request_result['staff']['number']})")
        print(f"Dates: {self.request_result['start_date']} to {self.request_result['end_date']}")
        print(f"Reason: {self.request_result['reason']}")
        
        if self.request_result["substitute"]:
            print(f"Substitute: {self.request_result['substitute']['name']} (Number: {self.request_result['substitute']['number']})")
        else:
            print("Substitute: None assigned")
        
        print("===================================================")
