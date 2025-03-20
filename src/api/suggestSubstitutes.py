# suggestSubstitutes.py
import psycopg2
from datetime import datetime

class suggestSubstitutes:
    def __init__(self, db_config):
        """
        Initializes the API instance with database configuration.
        :param db_config: Dictionary containing database connection parameters.
        """
        self.db_config = db_config
        self.staff_number = None
        self.start_date = None
        self.end_date = None
        self.substitutes = []
        
    @classmethod
    def prepareStatements(cls, db_config):
        """
        Prepares server‑side prepared statements for suggesting substitutes.
        The following statements are prepared:
          1. suggest_subs_validate_staff_plan:
             Retrieves staff details based on staff number.
          2. suggest_subs_timeoff_request_plan:
             Checks for an existing time off request for the staff within a given date range.
          3. suggest_subs_assigned_plan:
             Retrieves details for an assigned substitute (if any) for the request.
          4. suggest_subs_available_plan:
             Retrieves available substitutes whose availability covers the entire requested range
             and who are not already assigned to a conflicting time off request.
        
        The persistent connection and prepared statement names are stored as class variables.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        try:
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            
            # Validate staff details.
            stmt_staff = """
                PREPARE suggest_subs_validate_staff_plan (text) AS
                SELECT ID, FirstName, LastName 
                FROM Staff 
                WHERE Number = $1;
            """
            cursor.execute(stmt_staff)
            
            # Check for an existing time off request.
            stmt_request = """
                PREPARE suggest_subs_timeoff_request_plan (integer, date, date, date, date, date, date) AS
                SELECT ID, StartDate, EndDate, SubstituteID
                FROM TimeOffRequest
                WHERE StaffID = $1
                AND (
                    (StartDate <= $2 AND EndDate >= $3) OR
                    (StartDate >= $4 AND StartDate <= $5) OR
                    (EndDate >= $6 AND EndDate <= $7)
                );
            """
            cursor.execute(stmt_request)
            
            # Get details for an assigned substitute.
            stmt_assigned = """
                PREPARE suggest_subs_assigned_plan (integer, date, date) AS
                SELECT s.Number, s.FirstName, s.LastName, s.WorkEmail,
                       a.StartDate, a.EndDate
                FROM Substitute s
                JOIN Availability a ON s.ID = a.SubstituteID
                WHERE s.ID = $1
                AND (a.StartDate <= $2 AND a.EndDate >= $3);
            """
            cursor.execute(stmt_assigned)
            
            # Retrieve available substitutes.
            stmt_available = """
                PREPARE suggest_subs_available_plan (date, date, date, date, date, date, date, date) AS
                SELECT s.Number, s.FirstName, s.LastName, s.WorkEmail,
                       a.StartDate, a.EndDate
                FROM Substitute s
                JOIN Availability a ON s.ID = a.SubstituteID
                WHERE (a.StartDate <= $1 AND a.EndDate >= $2)
                AND s.ID NOT IN (
                    SELECT SubstituteID 
                    FROM TimeOffRequest 
                    WHERE SubstituteID IS NOT NULL
                    AND (
                        (StartDate <= $3 AND EndDate >= $4) OR
                        (StartDate >= $5 AND StartDate <= $6) OR
                        (EndDate >= $7 AND EndDate <= $8)
                    )
                )
                ORDER BY s.LastName, s.FirstName;
            """
            cursor.execute(stmt_available)
            
            connection.commit()
            cursor.close()
            
            # Store connection and prepared statement names as class variables.
            cls.prepared_conn = connection
            cls.prepared_statement_staff = "suggest_subs_validate_staff_plan"
            cls.prepared_statement_request = "suggest_subs_timeoff_request_plan"
            cls.prepared_statement_assigned = "suggest_subs_assigned_plan"
            cls.prepared_statement_available = "suggest_subs_available_plan"
            
            print("Prepared statements for suggestSubstitutes.")
        except Exception as e:
            print("Error preparing statements for suggestSubstitutes:", e)
    
    def getDescription(self):
        """
        Returns a description of what this API does.
        """
        return """Suggests available substitutes for a staff member for a specific date range.

        Input:
        - Staff number
        - Start date
        - End date

        Output:
        - List of available substitutes with their details:
        - Substitute number
        - First name
        - Last name
        - Work email
        - Availability dates

        Business purpose:
        Checks if a time off request has been filled, and if not, it suggests which substitutes
        would best cover that time off period."""
    
    def getInput(self, staff_number=None, start_date=None, end_date=None):
        """
        Takes the inputs required to suggest substitutes.
        If called without parameters, prompts the user for input interactively.
        
        :param staff_number: The unique staff number.
        :param start_date: The start date to find substitutes for (format: YYYY-MM-DD).
        :param end_date: The end date to find substitutes for (format: YYYY-MM-DD).
        """
        if staff_number and start_date and end_date:
            self.staff_number = staff_number
            self.start_date = start_date
            self.end_date = end_date
            return
            
        print("Please enter the following information to find available substitutes:")
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
                if datetime.strptime(end_date_input, "%Y-%m-%d") < datetime.strptime(self.start_date, "%Y-%m-%d"):
                    print("End date must be after or equal to start date.")
                    continue
                self.end_date = end_date_input
                break
            except Exception:
                print("Invalid date format. Please use YYYY-MM-DD format.")
    
    def retrieveOutput(self):
        """
        Uses the persistent connection and prepared statements to retrieve available substitutes.
        First, it validates the staff number. Then it checks if there's an existing time off request.
        If a substitute is already assigned, it retrieves that substitute's details. Otherwise,
        it retrieves a list of available substitutes for the given date range.
        """
        try:
            connection = self.__class__.prepared_conn
            cursor = connection.cursor()
            
            # Validate staff using the prepared statement.
            exec_staff = f"EXECUTE {self.__class__.prepared_statement_staff} (%s);"
            cursor.execute(exec_staff, (self.staff_number,))
            staff_data = cursor.fetchone()
            if not staff_data:
                print(f"Error: Staff with number {self.staff_number} not found.")
                cursor.close()
                return
            staff_id = staff_data[0]
            
            # Check for an existing time off request for this staff.
            exec_request = f"EXECUTE {self.__class__.prepared_statement_request} (%s, %s, %s, %s, %s, %s, %s);"
            cursor.execute(exec_request, (staff_id, self.start_date, self.end_date,
                                            self.start_date, self.end_date,
                                            self.start_date, self.end_date))
            request = cursor.fetchone()
            
            # If a request exists and a substitute is already assigned, retrieve assigned substitute details.
            if request and request[3] is not None:
                exec_assigned = f"EXECUTE {self.__class__.prepared_statement_assigned} (%s, %s, %s);"
                cursor.execute(exec_assigned, (request[3], self.start_date, self.end_date))
                assigned_sub = cursor.fetchone()
                if assigned_sub:
                    self.substitutes = [{
                        "number": assigned_sub[0],
                        "first_name": assigned_sub[1],
                        "last_name": assigned_sub[2],
                        "work_email": assigned_sub[3],
                        "availability_start": assigned_sub[4],
                        "availability_end": assigned_sub[5],
                        "already_assigned": True
                    }]
                    cursor.close()
                    return
            
            # Retrieve available substitutes using the prepared statement.
            exec_available = f"EXECUTE {self.__class__.prepared_statement_available} (%s, %s, %s, %s, %s, %s, %s, %s);"
            cursor.execute(exec_available, (self.start_date, self.end_date,
                                            self.start_date, self.end_date,
                                            self.start_date, self.end_date,
                                            self.start_date, self.end_date))
            available_subs = cursor.fetchall()
            
            self.substitutes = []
            for sub in available_subs:
                self.substitutes.append({
                    "number": sub[0],
                    "first_name": sub[1],
                    "last_name": sub[2],
                    "work_email": sub[3],
                    "availability_start": sub[4],
                    "availability_end": sub[5],
                    "already_assigned": False
                })
            
            cursor.close()
        except Exception as e:
            print(f"Error finding available substitutes: {e}")
            if 'cursor' in locals() and cursor:
                cursor.close()
    
    def displayOutput(self):
        """Displays the list of suggested substitutes."""
        if not self.substitutes:
            print(f"No available substitutes found for staff {self.staff_number} from {self.start_date} to {self.end_date}.")
            return
        
        print(f"\n=== Available Substitutes for Staff {self.staff_number} from {self.start_date} to {self.end_date} ===")
        for i, sub in enumerate(self.substitutes, 1):
            print(f"\n[{i}] {sub['first_name']} {sub['last_name']}")
            print(f"    Number: {sub['number']}")
            print(f"    Email: {sub['work_email']}")
            print(f"    Available from {sub['availability_start']} to {sub['availability_end']}")
            if sub.get("already_assigned", False):
                print("    (Already assigned to this time off request)")
                
        print("\n========================================================")
